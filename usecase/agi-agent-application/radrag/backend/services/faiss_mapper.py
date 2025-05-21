import os 
import pandas as pd
import faiss 

def load_faiss_and_mapping(concept_type, base_path):
    safe_concept_type = concept_type.strip().lower().replace("/", "_").replace(" ", "_")
    index_path = os.path.join(base_path, f"faiss_index_{safe_concept_type}.index")
    mapping_path = os.path.join(base_path, f"snomed_id_mapping_{safe_concept_type}.tsv")

    index = faiss.read_index(index_path)
    mapping_df = pd.read_csv(mapping_path, sep="\t")

    return index, mapping_df

def match_text_to_snomed(input_text, index, mapping_df, model, top_k=1):
    embedding = model.encode([input_text])
    D, I = index.search(embedding, top_k)

    results = []
    for idx in I[0]:
        concept_id = mapping_df.iloc[idx]["concept_id"]
        concept_name = mapping_df.iloc[idx]["concept_name"]
        results.append((concept_id, concept_name))
    return results

def mapping(output_json, ASSETS_PATH, model):
    output_rows = []
    for hierarchy, description in output_json.items():
        if not description.strip():
            output_rows.append({
                "Hierarchy": hierarchy,
                "Input Description": "No description provided.",
                "Concept Name": "-", "Concept ID": "-"
            })
            continue

        try:
            index, mapping_df = load_faiss_and_mapping(hierarchy, ASSETS_PATH)
            matches = match_text_to_snomed(description, index, mapping_df, model, top_k=1)

            if matches:
                for i, (concept_id, concept_name) in enumerate(matches, 1):
                    output_rows.append({
                        "Hierarchy": hierarchy,
                        "Input Description": description,
                        "Concept Name": concept_name,
                        "Concept ID": concept_id,
                    })
            else:
                output_rows.append({
                    "Hierarchy": hierarchy,
                    "Input Description": description,
                    "Concept Name": "No match found", "Concept ID": "-"
                })

        except FileNotFoundError:
            output_rows.append({
                "Hierarchy": hierarchy,
                "Input Description": description,
                "Concept Name": "FAISS file not found", "Concept ID": "-"
            })
        except Exception as e:
            output_rows.append({
                "Hierarchy": hierarchy,
                "Input Description": description,
                "Concept Name": f"Error: {str(e)}", "Concept ID": "-"
            })
        
    df_output = pd.DataFrame(output_rows)
    return df_output
