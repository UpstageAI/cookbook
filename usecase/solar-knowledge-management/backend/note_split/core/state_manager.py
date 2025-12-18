"""State management for Streamlit session state."""
from typing import List, Optional, Dict, Any
import streamlit as st
from pathlib import Path
from ..models import Topic
from .path_utils import resolve_path


class StateManager:
    """Manager for Streamlit session state."""

    # State keys
    KEY_RAW_NOTE_PATH = 'raw_note_path'
    KEY_SAVE_FOLDER_PATH = 'save_folder_path'
    KEY_RAW_NOTE_CONTENT = 'raw_note_content'
    KEY_RAW_NOTE_LINES = 'raw_note_lines'
    KEY_TOPICS = 'topics'
    KEY_SELECTED_TEMPLATE = 'selected_template'
    KEY_ANALYSIS_INSTRUCTIONS = 'analysis_instructions'
    KEY_STEP = 'current_step'

    # Step identifiers
    STEP_INIT = 'init'
    STEP_TEMPLATE_SELECT = 'template_select'
    STEP_TOPICS_EXTRACTED = 'topics_extracted'
    STEP_NOTES_GENERATED = 'notes_generated'

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

        if StateManager.KEY_RAW_NOTE_LINES not in st.session_state:
            st.session_state[StateManager.KEY_RAW_NOTE_LINES] = None

        if StateManager.KEY_TOPICS not in st.session_state:
            st.session_state[StateManager.KEY_TOPICS] = []

        if StateManager.KEY_SELECTED_TEMPLATE not in st.session_state:
            st.session_state[StateManager.KEY_SELECTED_TEMPLATE] = None

        if StateManager.KEY_ANALYSIS_INSTRUCTIONS not in st.session_state:
            st.session_state[StateManager.KEY_ANALYSIS_INSTRUCTIONS] = ''

    @staticmethod
    def get_current_step() -> str:
        """Get the current step in the workflow."""
        return st.session_state.get(StateManager.KEY_STEP, StateManager.STEP_INIT)

    @staticmethod
    def set_step(step: str):
        """Set the current workflow step."""
        st.session_state[StateManager.KEY_STEP] = step

    @staticmethod
    def get_raw_note_path() -> Optional[Path]:
        """Get the raw note path."""
        path = st.session_state.get(StateManager.KEY_RAW_NOTE_PATH)
        if path:
            return resolve_path(path)
        return None

    @staticmethod
    def set_raw_note_path(path: Path):
        """Set the raw note path."""
        st.session_state[StateManager.KEY_RAW_NOTE_PATH] = str(path)

    @staticmethod
    def get_save_folder_path() -> Optional[Path]:
        """Get the save folder path."""
        path = st.session_state.get(StateManager.KEY_SAVE_FOLDER_PATH)
        if path:
            return resolve_path(path)
        return None

    @staticmethod
    def set_save_folder_path(path: Path):
        """Set the save folder path."""
        st.session_state[StateManager.KEY_SAVE_FOLDER_PATH] = str(path)

    @staticmethod
    def get_raw_note_content() -> Optional[str]:
        """Get the raw note content."""
        return st.session_state.get(StateManager.KEY_RAW_NOTE_CONTENT)

    @staticmethod
    def set_raw_note_content(content: str, lines: List[str]):
        """Set the raw note content and lines."""
        st.session_state[StateManager.KEY_RAW_NOTE_CONTENT] = content
        st.session_state[StateManager.KEY_RAW_NOTE_LINES] = lines

    @staticmethod
    def get_raw_note_lines() -> Optional[List[str]]:
        """Get the raw note lines."""
        return st.session_state.get(StateManager.KEY_RAW_NOTE_LINES)

    @staticmethod
    def get_topics() -> List[Topic]:
        """Get the list of topics."""
        topics_data = st.session_state.get(StateManager.KEY_TOPICS, [])
        return [Topic.from_dict(t) if isinstance(t, dict) else t for t in topics_data]

    @staticmethod
    def set_topics(topics: List[Topic]):
        """Set the list of topics."""
        st.session_state[StateManager.KEY_TOPICS] = [
            t.to_dict() if isinstance(t, Topic) else t for t in topics
        ]

    @staticmethod
    def add_topic(topic: Topic):
        """Add a new topic to the list."""
        topics = StateManager.get_topics()
        topics.append(topic)
        StateManager.set_topics(topics)

    @staticmethod
    def update_topic(index: int, topic: Topic):
        """Update a topic at a specific index."""
        topics = StateManager.get_topics()
        if 0 <= index < len(topics):
            topics[index] = topic
            StateManager.set_topics(topics)

    @staticmethod
    def delete_topic(index: int):
        """Delete a topic at a specific index."""
        topics = StateManager.get_topics()
        if 0 <= index < len(topics):
            topics.pop(index)
            StateManager.set_topics(topics)

    @staticmethod
    def delete_topics(indices: List[int]):
        """Delete multiple topics by indices."""
        topics = StateManager.get_topics()
        # Sort indices in reverse to avoid index shifting issues
        for index in sorted(indices, reverse=True):
            if 0 <= index < len(topics):
                topics.pop(index)
        StateManager.set_topics(topics)

    @staticmethod
    def get_selected_topics() -> List[Topic]:
        """Get list of topics that are selected."""
        return [t for t in StateManager.get_topics() if t.selected]

    @staticmethod
    def get_selected_topic_indices() -> List[int]:
        """Get indices of selected topics."""
        topics = StateManager.get_topics()
        return [i for i, t in enumerate(topics) if t.selected]

    @staticmethod
    def select_all_topics():
        """Select all topics."""
        topics = StateManager.get_topics()
        for topic in topics:
            topic.selected = True
        StateManager.set_topics(topics)

    @staticmethod
    def deselect_all_topics():
        """Deselect all topics."""
        topics = StateManager.get_topics()
        for topic in topics:
            topic.selected = False
        StateManager.set_topics(topics)

    @staticmethod
    def get_selected_template() -> Optional[str]:
        """Get the selected prompt template name."""
        return st.session_state.get(StateManager.KEY_SELECTED_TEMPLATE)

    @staticmethod
    def set_selected_template(template_name: str):
        """Set the selected prompt template."""
        st.session_state[StateManager.KEY_SELECTED_TEMPLATE] = template_name

    @staticmethod
    def get_analysis_instructions() -> str:
        """Get the analysis instructions."""
        return st.session_state.get(StateManager.KEY_ANALYSIS_INSTRUCTIONS, '')

    @staticmethod
    def set_analysis_instructions(instructions: str):
        """Set the analysis instructions."""
        st.session_state[StateManager.KEY_ANALYSIS_INSTRUCTIONS] = instructions

    @staticmethod
    def reset():
        """Reset all state to initial values."""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        StateManager.initialize()

