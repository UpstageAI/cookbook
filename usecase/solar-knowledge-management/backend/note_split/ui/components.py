"""Reusable UI components for Streamlit application."""
import streamlit as st
from typing import List, Optional, Callable
from ..models import Topic
from ..core.state_manager import StateManager


def render_topic_card(
    topic: Topic,
    index: int,
    on_update: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    on_select: Optional[Callable] = None
):
    """Render a topic card with information and actions.

    Args:
        topic: Topic object to display
        index: Index of the topic in the list
        on_update: Callback for update action
        on_delete: Callback for delete action
        on_select: Callback for selection toggle
    """
    with st.container():
        # Create columns for layout
        col_check, col_llm, col_content, col_actions = st.columns([0.5, 0.5, 7.5, 1.5])

        # Checkbox for selection
        with col_check:
            if on_select:
                st.markdown(
                    '<span title="원자 노트 생성을 위해 이 토픽을 선택합니다">✓</span>',
                    unsafe_allow_html=True
                )
                selected = st.checkbox(
                    "선택",
                    value=topic.selected,
                    key=f"select_{index}",
                    label_visibility="collapsed",
                    help="원자 노트 생성을 위해 이 토픽을 선택합니다"
                )
                if selected != topic.selected:
                    on_select(index, selected)

        # Checkbox for LLM generation
        with col_llm:
            st.markdown(
                '<span title="LLM을 사용하여 원자 노트 초안과 작성 가이드라인을 생성합니다">🤖</span>',
                unsafe_allow_html=True
            )
            use_llm = st.checkbox(
                "LLM 생성",
                value=topic.use_llm,
                key=f"use_llm_{index}",
                label_visibility="collapsed",
                help="LLM을 사용하여 원자 노트 초안과 작성 가이드라인을 생성합니다"
            )
            if use_llm != topic.use_llm:
                # Update topic's use_llm field
                updated_topic = Topic(
                    topic=topic.topic,
                    coverage=topic.coverage,
                    line_numbers=topic.line_numbers,
                    keywords=topic.keywords,
                    user_direction=topic.user_direction,
                    use_llm=use_llm,
                    selected=topic.selected
                )
                if on_update:
                    on_update(index, updated_topic)

        # Main content
        with col_content:
            st.markdown(f"### {topic.topic}")
            st.markdown(f"**Overview:** {topic.coverage}")

            if topic.keywords:
                keywords_str = ', '.join(f'`{kw}`' for kw in topic.keywords)
                st.markdown(f"**Keywords:** {keywords_str}")

            if topic.line_numbers:
                lines_str = ', '.join(str(ln) for ln in sorted(topic.line_numbers))
                st.markdown(f"**Related Lines:** {lines_str}")

        # Action buttons
        with col_actions:
            col_edit, col_del = st.columns(2)

            with col_edit:
                if st.button("✏️", key=f"edit_{index}", help="Edit topic"):
                    st.session_state[f'editing_{index}'] = True

            with col_del:
                if st.button("🗑️", key=f"delete_{index}", help="Delete topic"):
                    if on_delete:
                        on_delete(index)

        # Edit modal (using expander as a simple modal)
        if st.session_state.get(f'editing_{index}', False):
            with st.expander("Edit Topic", expanded=True):
                render_topic_edit_form(topic, index, on_update)

        st.divider()


def render_topic_edit_form(
    topic: Topic,
    index: int,
    on_save: Optional[Callable] = None
):
    """Render an edit form for a topic.

    Args:
        topic: Topic object to edit
        index: Index of the topic
        on_save: Callback when save is clicked
    """
    new_topic = st.text_input(
        "Topic Name",
        value=topic.topic,
        key=f"edit_topic_{index}"
    )

    new_coverage = st.text_area(
        "Coverage",
        value=topic.coverage,
        key=f"edit_coverage_{index}",
        height=100
    )

    new_keywords = st.text_input(
        "Keywords (comma-separated)",
        value=', '.join(topic.keywords),
        key=f"edit_keywords_{index}"
    )

    new_user_direction = st.text_area(
        "User Direction (optional)",
        value=topic.user_direction or '',
        key=f"edit_direction_{index}",
        height=80,
        help="Additional instructions for generating the atomic note"
    )

    new_use_llm = st.checkbox(
        "Use LLM for content generation",
        value=topic.use_llm,
        key=f"edit_use_llm_{index}",
        help="Enable LLM to generate draft content and writing guidelines"
    )

    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button("Save", key=f"save_{index}"):
            updated_topic = Topic(
                topic=new_topic,
                coverage=new_coverage,
                line_numbers=topic.line_numbers,
                keywords=[kw.strip() for kw in new_keywords.split(',') if kw.strip()],
                user_direction=new_user_direction if new_user_direction else None,
                use_llm=new_use_llm,
                selected=topic.selected
            )

            if on_save:
                on_save(index, updated_topic)

            st.session_state[f'editing_{index}'] = False
            st.rerun()

    with col_cancel:
        if st.button("Cancel", key=f"cancel_{index}"):
            st.session_state[f'editing_{index}'] = False
            st.rerun()


def render_topics_list(
    topics: List[Topic],
    on_update: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    on_select: Optional[Callable] = None
):
    """Render a list of topic cards.

    Args:
        topics: List of Topic objects
        on_update: Callback for topic updates
        on_delete: Callback for topic deletion
        on_select: Callback for topic selection
    """
    if not topics:
        st.info("No topics extracted yet. Please run topic extraction first.")
        return

    st.markdown(f"### Extracted Topics ({len(topics)})")
    st.markdown("---")

    for i, topic in enumerate(topics):
        render_topic_card(topic, i, on_update, on_delete, on_select)


def render_batch_actions():
    """Render batch action buttons."""
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("Select All", use_container_width=True):
            StateManager.select_all_topics()
            st.rerun()

    with col2:
        if st.button("Deselect All", use_container_width=True):
            StateManager.deselect_all_topics()
            st.rerun()

    with col3:
        selected_indices = StateManager.get_selected_topic_indices()
        if selected_indices:
            if st.button(
                f"Delete Selected ({len(selected_indices)})",
                use_container_width=True,
                type="primary"
            ):
                st.session_state['confirm_batch_delete'] = True

    # Confirmation dialog
    if st.session_state.get('confirm_batch_delete', False):
        st.warning("Are you sure you want to delete the selected topics?")
        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("Yes, Delete", type="primary"):
                selected_indices = StateManager.get_selected_topic_indices()
                StateManager.delete_topics(selected_indices)
                st.session_state['confirm_batch_delete'] = False
                st.success(f"Deleted {len(selected_indices)} topic(s)")
                st.rerun()

        with col_no:
            if st.button("Cancel"):
                st.session_state['confirm_batch_delete'] = False
                st.rerun()


def render_add_topics_form(on_add: Optional[Callable] = None):
    """Render form for adding new topics.

    Args:
        on_add: Callback when new topics should be added
    """
    with st.expander("Add New Topics"):
        st.markdown("### Request Additional Topics")

        guidance = st.text_area(
            "Topic Generation Guidance",
            placeholder="E.g., 'Focus on technical implementation details' or 'Extract business logic concepts'",
            help="Provide guidance for what kind of topics to extract"
        )

        col1, col2 = st.columns(2)

        with col1:
            num_topics = st.number_input(
                "Number of Topics",
                min_value=1,
                max_value=10,
                value=3,
                help="How many additional topics to generate"
            )

        with col2:
            template = st.selectbox(
                "Prompt Template",
                options=["topic_extract_amend_default", "topic_extract_diverse"],
                help="Select the prompt template for topic extraction"
            )

        if st.button("Generate New Topics", type="primary"):
            if on_add:
                on_add(guidance, num_topics, template)


def render_progress_indicator(message: str, progress: Optional[float] = None):
    """Render a progress indicator.

    Args:
        message: Message to display
        progress: Optional progress value (0.0 to 1.0)
    """
    if progress is not None:
        st.progress(progress, text=message)
    else:
        with st.spinner(message):
            pass


def render_file_input_section():
    """Render the file input section."""
    st.markdown("## 1. Initial Setup")

    note_path = st.text_input(
        "Raw Note Path",
        placeholder="/path/to/your/note.md",
        help="Path to the markdown note file you want to analyze"
    )

    save_folder = st.text_input(
        "Save Folder Path (optional)",
        placeholder="Leave empty to use default location",
        help="Folder where atomic notes will be saved. If empty, defaults to [note-name]-atoms/"
    )

    analysis_instructions = st.text_area(
        "Analysis Instructions (optional)",
        placeholder="Additional instructions for topic extraction...",
        help="Optional guidance for the LLM when extracting topics",
        height=100
    )

    return note_path, save_folder, analysis_instructions


def render_template_selection_section(templates: dict):
    """Render the template selection section.

    Args:
        templates: Dictionary of template names to descriptions

    Returns:
        Selected template name or None
    """
    st.markdown("## 2. Select Prompt Template")

    if not templates:
        st.warning("No prompt templates found. Please add template files to the prompts/ folder.")
        return None

    # Filter templates: only include topic_extract_* templates that are NOT topic_extract_amend_*
    filtered_templates = {
        name: desc for name, desc in templates.items()
        if name.startswith('topic_extract_') and not name.startswith('topic_extract_amend_')
    }

    if not filtered_templates:
        st.warning("No valid topic extraction templates found.")
        return None

    # Create options with descriptions
    template_options = {
        name: f"{name} - {desc}" for name, desc in filtered_templates.items()
    }

    # Set default to topic_extract_default if it exists, otherwise use first template
    default_index = 0
    if 'topic_extract_default' in filtered_templates:
        default_index = list(filtered_templates.keys()).index('topic_extract_default')

    selected = st.selectbox(
        "Choose a template",
        options=list(template_options.keys()),
        index=default_index,
        format_func=lambda x: template_options[x]
    )

    return selected


def render_error(message: str):
    """Render an error message."""
    st.error(f"❌ {message}")


def render_success(message: str):
    """Render a success message."""
    st.success(f"✅ {message}")


def render_info(message: str):
    """Render an info message."""
    st.info(f"ℹ️ {message}")

