"""State management for Streamlit session state."""

from typing import List, Optional
import streamlit as st
from pathlib import Path
from ..models import FreshnessMetadata, DescriptionTemplate
from .path_utils import resolve_path


class StateManager:
    """Manager for Streamlit session state for note freshness."""

    # State keys
    KEY_RAW_NOTE_PATH = "freshness_raw_note_path"
    KEY_SAVE_FOLDER_PATH = "freshness_save_folder_path"
    KEY_RAW_NOTE_CONTENT = "freshness_raw_note_content"
    KEY_METADATA = "freshness_metadata"
    KEY_INFO_KEYWORD = "freshness_info_keyword"
    KEY_INFO_QUERY = "freshness_info_query"
    KEY_DESCRIPTION_TEMPLATE = "freshness_desc_template"
    KEY_WIKI_RESULTS = "freshness_wiki_results"
    KEY_TAVILY_RESULTS = "freshness_tavily_results"
    KEY_STEP = "freshness_current_step"

    # Step identifiers
    STEP_INIT = "init"
    STEP_NOTE_VALIDATED = "note_validated"
    STEP_TEMPLATE_SELECT = "template_select"
    STEP_EXTRACTION_DONE = "extraction_done"
    STEP_METADATA_CONFIRMED = "metadata_confirmed"
    STEP_SEARCH_DONE = "search_done"
    STEP_GUIDE_GENERATED = "guide_generated"

    @staticmethod
    def initialize():
        """Initialize session state with default values."""
        if StateManager.KEY_STEP not in st.session_state:
            st.session_state[StateManager.KEY_STEP] = StateManager.STEP_INIT

        if StateManager.KEY_RAW_NOTE_PATH not in st.session_state:
            st.session_state[StateManager.KEY_RAW_NOTE_PATH] = None

        if StateManager.KEY_SAVE_FOLDER_PATH not in st.session_state:
            st.session_state[StateManager.KEY_SAVE_FOLDER_PATH] = None

        if StateManager.KEY_RAW_NOTE_CONTENT not in st.session_state:
            st.session_state[StateManager.KEY_RAW_NOTE_CONTENT] = None

        if StateManager.KEY_METADATA not in st.session_state:
            st.session_state[StateManager.KEY_METADATA] = None

        if StateManager.KEY_INFO_KEYWORD not in st.session_state:
            st.session_state[StateManager.KEY_INFO_KEYWORD] = []

        if StateManager.KEY_INFO_QUERY not in st.session_state:
            st.session_state[StateManager.KEY_INFO_QUERY] = []

        if StateManager.KEY_DESCRIPTION_TEMPLATE not in st.session_state:
            st.session_state[StateManager.KEY_DESCRIPTION_TEMPLATE] = None

        if StateManager.KEY_WIKI_RESULTS not in st.session_state:
            st.session_state[StateManager.KEY_WIKI_RESULTS] = []

        if StateManager.KEY_TAVILY_RESULTS not in st.session_state:
            st.session_state[StateManager.KEY_TAVILY_RESULTS] = []

    @staticmethod
    def get_current_step() -> str:
        return st.session_state.get(StateManager.KEY_STEP, StateManager.STEP_INIT)

    @staticmethod
    def set_step(step: str):
        st.session_state[StateManager.KEY_STEP] = step

    @staticmethod
    def get_raw_note_path() -> Optional[Path]:
        path = st.session_state.get(StateManager.KEY_RAW_NOTE_PATH)
        if path:
            return resolve_path(path)
        return None

    @staticmethod
    def set_raw_note_path(path: Path):
        st.session_state[StateManager.KEY_RAW_NOTE_PATH] = str(path)

    @staticmethod
    def get_save_folder_path() -> Optional[Path]:
        path = st.session_state.get(StateManager.KEY_SAVE_FOLDER_PATH)
        if path:
            return resolve_path(path)
        return None

    @staticmethod
    def set_save_folder_path(path: Path):
        st.session_state[StateManager.KEY_SAVE_FOLDER_PATH] = str(path)

    @staticmethod
    def get_raw_note_content() -> Optional[str]:
        return st.session_state.get(StateManager.KEY_RAW_NOTE_CONTENT)

    @staticmethod
    def set_raw_note_content(content: str):
        st.session_state[StateManager.KEY_RAW_NOTE_CONTENT] = content

    @staticmethod
    def get_metadata() -> Optional[FreshnessMetadata]:
        data = st.session_state.get(StateManager.KEY_METADATA)
        if data:
            return FreshnessMetadata(
                info_keyword=data.get("info_keyword", []),
                info_query=data.get("info_query", []),
                wiki_searched_at=data.get("wiki_searched_at"),
                tavily_searched_at=data.get("tavily_searched_at"),
            )
        return None

    @staticmethod
    def set_metadata(metadata: FreshnessMetadata):
        st.session_state[StateManager.KEY_METADATA] = metadata.to_yaml_dict()

    @staticmethod
    def get_info_keyword() -> List[str]:
        return st.session_state.get(StateManager.KEY_INFO_KEYWORD, [])

    @staticmethod
    def set_info_keyword(keywords: List[str]):
        st.session_state[StateManager.KEY_INFO_KEYWORD] = keywords

    @staticmethod
    def get_info_query() -> List[str]:
        return st.session_state.get(StateManager.KEY_INFO_QUERY, [])

    @staticmethod
    def set_info_query(queries: List[str]):
        st.session_state[StateManager.KEY_INFO_QUERY] = queries

    @staticmethod
    def get_description_template() -> Optional[DescriptionTemplate]:
        data = st.session_state.get(StateManager.KEY_DESCRIPTION_TEMPLATE)
        if data:
            return DescriptionTemplate.from_dict(data)
        return None

    @staticmethod
    def set_description_template(template: DescriptionTemplate):
        st.session_state[StateManager.KEY_DESCRIPTION_TEMPLATE] = template.to_dict()

    @staticmethod
    def get_wiki_results() -> List[dict]:
        return st.session_state.get(StateManager.KEY_WIKI_RESULTS, [])

    @staticmethod
    def set_wiki_results(results: List[dict]):
        st.session_state[StateManager.KEY_WIKI_RESULTS] = results

    @staticmethod
    def get_tavily_results() -> List[dict]:
        return st.session_state.get(StateManager.KEY_TAVILY_RESULTS, [])

    @staticmethod
    def set_tavily_results(results: List[dict]):
        st.session_state[StateManager.KEY_TAVILY_RESULTS] = results

    @staticmethod
    def reset():
        """Reset all state to initial values."""
        keys_to_reset = [
            StateManager.KEY_STEP,
            StateManager.KEY_RAW_NOTE_PATH,
            StateManager.KEY_SAVE_FOLDER_PATH,
            StateManager.KEY_RAW_NOTE_CONTENT,
            StateManager.KEY_METADATA,
            StateManager.KEY_INFO_KEYWORD,
            StateManager.KEY_INFO_QUERY,
            StateManager.KEY_DESCRIPTION_TEMPLATE,
            StateManager.KEY_WIKI_RESULTS,
            StateManager.KEY_TAVILY_RESULTS,
        ]
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        StateManager.initialize()
