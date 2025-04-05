from pathlib import Path
from loguru import logger
import pandas as pd
import typer

app = typer.Typer()
root_directory = Path(__file__).parent


def load_snomed_ct(data_path: Path):
    """
    Create a SNOMED CT concept DataFrame.

    Derived from: https://github.com/CogStack/MedCAT/blob/master/medcat/utils/preprocess_snomed.py

    Returns:
        pandas.DataFrame: SNOMED CT concept DataFrame.
    """

    def _read_file_and_subset_to_active(filename):
        with open(filename, encoding="utf-8") as f:
            entities = [[n.strip() for n in line.split("\t")] for line in f]
            df = pd.DataFrame(entities[1:], columns=entities[0])
        return df[df.active == "1"]

    active_terms = _read_file_and_subset_to_active(
        data_path / "sct2_Concept_Snapshot_INT_20250401.txt"
    )
    active_descs = _read_file_and_subset_to_active(
        data_path / "sct2_Description_Snapshot-en_INT_20250401.txt"
    )

    df = pd.merge(active_terms, active_descs, left_on=["id"], right_on=["conceptId"], how="inner")[
        ["id_x", "term", "typeId"]
    ].rename(columns={"id_x": "concept_id", "term": "concept_name", "typeId": "name_type"})

    # active description or active synonym
    df["name_type"] = df["name_type"].replace(
        ["900000000000003001", "900000000000013009"], ["P", "A"]
    )
    active_snomed_df = df[df.name_type.isin(["P", "A"])]

    active_snomed_df["hierarchy"] = active_snomed_df["concept_name"].str.extract(
        r"\((\w+\s?.?\s?\w+.?\w+.?\w+.?)\)$"
    )
    active_snomed_df = active_snomed_df[active_snomed_df.hierarchy.notnull()].reset_index(drop=True)
    return active_snomed_df


@app.command()
def make_flattened_terminology(
    snomed_ct_directory: Path = (
        root_directory
        / "data"
        / "SnomedCT_InternationalRF2_PRODUCTION_20250401T120000Z"
    ),
    output_path: Path = root_directory / "assets" / "dataflattened_terminology.csv",
):
    # unzip the terminology provided on the data download page and specify the path to the folder here
    snomed_rf2_path = Path(snomed_ct_directory)
    # load the SNOMED release
    df = load_snomed_ct(snomed_rf2_path / "Snapshot" / "Terminology")
    logger.debug(f"Loaded SNOMED CT release containing {len(df):,} rows (expected 364,323).")

    concept_type_subset = [
        "procedure",  # top level category
        "body structure",  # top level category
        "finding",  # top level category
        "disorder",  # child of finding
        "morphologic abnormality",  # child of body structure
        "regime/therapy",  # child of procedure
        "cell structure",  # child of body structure
    ]

    filtered_df = df[
        (
            df.hierarchy.isin(concept_type_subset)
        )  # Filter the SNOMED data to the selected Concept Types
        & (df.name_type == "P")  # Preferred Terms only (i.e. one row per concept, drop synonyms)
    ].copy()
    logger.debug(f"Filtered to {len(filtered_df):,} relevant rows (expected 218,467).")

    logger.debug(f"Value counts:\n{filtered_df.hierarchy.value_counts()}")

    logger.debug(f"Saving flattened terminology with {len(filtered_df):,} rows to {output_path}")
    filtered_df.drop("name_type", axis="columns", inplace=True)
    filtered_df.to_csv(output_path)
    return filtered_df


@app.command()
def generate_sct_dictionary(
    snapshot_path: Path = root_directory
    / "data"
    / "SnomedCT_InternationalRF2_PRODUCTION_20250401T120000Z"
    / "Snapshot"
    / "Terminology"
    / "sct2_Description_Snapshot-en_INT_20250401.txt",
    flattened_terminology_path: Path = root_directory / "assets" / "dataflattened_terminology.csv",
    output_path: Path = root_directory / "assets" / "newdict_snomed.txt",
):
    logger.info(
        f"Generating SNOMED-CT dictionary from {snapshot_path} and {flattened_terminology_path} and writing result to {output_path}"
    )
    snomed = pd.read_csv(snapshot_path, sep="\t")

    logger.debug(snomed.shape)
    flat = pd.read_csv(flattened_terminology_path, sep=",")
    print(flat.shape)

    out = []
    for row in snomed.itertuples():
        selected = flat["concept_id"].eq(row.conceptId).any()
        if (
            selected
            and "(" not in str(row.term)
            and not str(row.conceptId).startswith("900000000000")
            and not str(row.term).startswith("[")
        ):
            out.append([str(row.term), row.conceptId])

    out_df = pd.DataFrame(columns=["term", "code"], data=out)
    logger.debug(out_df.shape)
    out_df.to_csv(output_path, sep="\t", index=False)


if __name__ == "__main__":
    app()
