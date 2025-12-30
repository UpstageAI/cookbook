"""Main Streamlit application for Atomic Note Weaver."""
import streamlit as st
import asyncio
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Define prompts directory
PROMPTS_DIR = project_root / 'prompts'

from backend.note_split.config import Config
from backend.note_split.models import Topic
from backend.note_split.core.state_manager import StateManager
from backend.note_split.core.file_handler import FileHandler
from backend.note_split.core.path_utils import resolve_path, format_path_for_display
from backend.note_split.llm.client import UpstageClient
from backend.note_split.llm.parsers import ResponseParser
from backend.note_split.llm.prompt_loader import PromptLoader
from backend.note_split.ui.components import (
    render_file_input_section,
    render_template_selection_section,
    render_topics_list,
    render_batch_actions,
    render_add_topics_form,
    render_error,
    render_success,
    render_info
)


def initialize_app():
    """Initialize the application."""
    Config.ensure_directories()
    StateManager.initialize()


def validate_api_key() -> bool:
    """Validate that API key is configured."""
    if not Config.validate():
        st.error(
            "⚠️ Upstage API key not found. Please set UPSTAGE_API_KEY in your .env file."
        )
        st.code("UPSTAGE_API_KEY=your_api_key_here")
        return False
    return True


def handle_note_analysis(note_path: str, save_folder: str, instructions: str):
    """Handle the note analysis step."""
    # Normalize path for WSL if needed
    path = resolve_path(note_path)

    if not path.exists():
        render_error(f"File not found: {note_path}")
        return

    if not path.suffix == '.md':
        render_error("Please provide a markdown (.md) file.")
        return

    # Read the note
    content, lines = FileHandler.read_note(path)
    if content is None:
        render_error("Failed to read the note file.")
        return

    # Set paths in state
    StateManager.set_raw_note_path(path)
    StateManager.set_raw_note_content(content, lines)
    StateManager.set_analysis_instructions(instructions)

    # Set save folder
    if save_folder:
        resolved_save_folder = resolve_path(save_folder)
        StateManager.set_save_folder_path(resolved_save_folder)
    else:
        default_folder = Config.get_atomic_notes_folder(path)
        StateManager.set_save_folder_path(default_folder)

    # Move to next step
    StateManager.set_step(StateManager.STEP_TEMPLATE_SELECT)
    render_success(f"Note loaded successfully: {path.name}")
    st.rerun()


def handle_template_selection(template_name: str):
    """Handle template selection."""
    StateManager.set_selected_template(template_name)
    render_success(f"Template selected: {template_name}")


def handle_topic_extraction():
    """Handle topic extraction from the note."""
    template_name = StateManager.get_selected_template()
    if not template_name:
        render_error("Please select a template first.")
        return

    # Load template
    loader = PromptLoader(prompts_dir=PROMPTS_DIR)
    template = loader.load_template(template_name)
    if not template:
        # 파일이 존재하는지 확인하여 더 구체적인 메시지 제공
        template_path = loader.prompts_dir / f"{template_name}.yml"
        if template_path.exists():
            render_error(f"Failed to load template '{template_name}': The YAML file is empty or invalid. Please check the file format.")
        else:
            render_error(f"Template '{template_name}' not found. Please check the template name.")
        return

    # Get note content
    content = StateManager.get_raw_note_content()
    instructions = StateManager.get_analysis_instructions()

    # Prepare variables for prompt
    user_vars = {
        'note_content': content,
        'additional_instructions': instructions if instructions else 'None'
    }

    # Call LLM
    with st.spinner("Extracting topics from your note..."):
        try:
            client = UpstageClient()
            response = client.generate_with_template_sync(template, user_vars)

            if not response:
                render_error("Failed to get response from LLM.")
                return

            # Parse topics
            topics = ResponseParser.parse_topics_from_json(response)

            if not topics:
                render_error("No topics were extracted. Please try again with different instructions.")
                return

            # Save topics to state
            StateManager.set_topics(topics)
            StateManager.set_step(StateManager.STEP_TOPICS_EXTRACTED)
            render_success(f"Successfully extracted {len(topics)} topic(s)!")
            st.rerun()

        except Exception as e:
            render_error(f"Error during topic extraction: {str(e)}")


def handle_topic_update(index: int, updated_topic: Topic):
    """Handle topic update."""
    # Check if we need to update line numbers
    original_topic = StateManager.get_topics()[index]

    needs_line_update = (
        updated_topic.topic != original_topic.topic or
        updated_topic.coverage != original_topic.coverage
    )

    # If only use_llm changed, skip line number update and success message
    only_llm_changed = (
        updated_topic.topic == original_topic.topic and
        updated_topic.coverage == original_topic.coverage and
        updated_topic.use_llm != original_topic.use_llm
    )

    if needs_line_update:
        # Load line number update template
        loader = PromptLoader(prompts_dir=PROMPTS_DIR)
        template = loader.load_template('line_number_update')

        if template:
            content = StateManager.get_raw_note_content()
            user_vars = {
                'note_content': content,
                'topic': updated_topic.topic,
                'coverage': updated_topic.coverage
            }

            with st.spinner("Updating line numbers..."):
                try:
                    client = UpstageClient()
                    response = client.generate_with_template_sync(template, user_vars)

                    if response:
                        new_line_numbers = ResponseParser.parse_line_numbers_from_json(response)
                        updated_topic.line_numbers = new_line_numbers

                except Exception as e:
                    st.warning(f"Could not update line numbers automatically: {str(e)}")

    # Update the topic
    StateManager.update_topic(index, updated_topic)
    
    if not only_llm_changed:
        render_success("Topic updated successfully!")
    else:
        st.rerun()


def handle_topic_delete(index: int):
    """Handle topic deletion."""
    StateManager.delete_topic(index)
    render_success("Topic deleted successfully!")
    st.rerun()


def handle_topic_selection(index: int, selected: bool):
    """Handle topic selection toggle."""
    topics = StateManager.get_topics()
    topics[index].selected = selected
    StateManager.set_topics(topics)


def handle_add_topics(guidance: str, num_topics: int, template_name: str):
    """Handle adding new topics."""
    loader = PromptLoader(prompts_dir=PROMPTS_DIR)
    template = loader.load_template(template_name)

    if not template:
        # 파일이 존재하는지 확인하여 더 구체적인 메시지 제공
        template_path = loader.prompts_dir / f"{template_name}.yml"
        if template_path.exists():
            render_error(f"Failed to load template '{template_name}': The YAML file is empty or invalid. Please check the file format.")
        else:
            render_error(f"Template '{template_name}' not found. Please check the template name.")
        return

    content = StateManager.get_raw_note_content()
    existing_topics = StateManager.get_topics()
    existing_topics_str = '\n'.join([f"- {t.topic}: {t.coverage}" for t in existing_topics])

    user_vars = {
        'note_content': content,
        'existing_topics': existing_topics_str,
        'guidance': guidance if guidance else 'Extract additional relevant topics',
        'num_topics': num_topics
    }

    with st.spinner(f"Generating {num_topics} new topic(s)..."):
        try:
            client = UpstageClient()
            response = client.generate_with_template_sync(template, user_vars)

            if not response:
                render_error("Failed to get response from LLM.")
                return

            new_topics = ResponseParser.parse_topics_from_json(response)

            if not new_topics:
                render_error("No new topics were generated.")
                return

            # Add new topics to state
            for topic in new_topics:
                StateManager.add_topic(topic)

            render_success(f"Added {len(new_topics)} new topic(s)!")
            st.rerun()

        except Exception as e:
            render_error(f"Error generating new topics: {str(e)}")


async def generate_atomic_note(
    topic: Topic,
    lines: List[str],
    save_folder: Path
) -> bool:
    """Generate and save a single atomic note.

    Args:
        topic: Topic object
        lines: Lines from the raw note
        save_folder: Folder to save the atomic note

    Returns:
        True if successful, False otherwise
    """
    # Get related content
    related_content = FileHandler.get_lines_content(lines, topic.line_numbers)

    # Generate content with LLM if use_llm is enabled
    generated_content = None
    if topic.use_llm:
        try:
            loader = PromptLoader(prompts_dir=PROMPTS_DIR)
            template = loader.load_template('atomic_note_generate')

            if template:
                # Use user_direction if provided, otherwise use DEFAULT_ATOM_DIRECTION
                direction = topic.user_direction or Config.DEFAULT_ATOM_DIRECTION
                
                # If no direction is provided at all, skip LLM generation
                if not direction:
                    print(f"Warning: No direction provided for {topic.topic}. Skipping LLM generation.")
                else:
                    user_vars = {
                        'topic': topic.topic,
                        'coverage': topic.coverage,
                        'related_content': related_content,
                        'keywords': ', '.join(topic.keywords),
                        'user_direction': direction
                    }

                    client = UpstageClient()
                    response = await client.generate_with_template(template, user_vars)

                    if response:
                        generated_content = ResponseParser.parse_atomic_note_content(response)

        except Exception as e:
            print(f"Warning: Could not generate content for {topic.topic}: {e}")

    # Create atomic note content
    note_content = FileHandler.create_atomic_note(
        topic,
        related_content,
        generated_content
    )

    # Save the note
    return FileHandler.save_atomic_note(save_folder, topic, note_content)


async def handle_generate_atomic_notes_async(topics: List[Topic]):
    """Handle atomic note generation (async)."""
    lines = StateManager.get_raw_note_lines()
    save_folder = StateManager.get_save_folder_path()
    raw_note_path = StateManager.get_raw_note_path()

    if not lines or not save_folder or not raw_note_path:
        render_error("Missing required data. Please start over.")
        return

    # Generate all atomic notes in parallel
    progress_bar = st.progress(0, text="Generating atomic notes...")

    tasks = [generate_atomic_note(topic, lines, save_folder) for topic in topics]
    results = []

    for i, task in enumerate(asyncio.as_completed(tasks)):
        result = await task
        results.append(result)
        progress = (i + 1) / len(tasks)
        progress_bar.progress(progress, text=f"Generated {i + 1}/{len(tasks)} atomic notes...")

    success_count = sum(results)

    if success_count == 0:
        render_error("Failed to generate any atomic notes.")
        return

    # Insert backlinks in raw note
    modified_lines = FileHandler.insert_backlinks(lines, topics)

    # Append topic list to raw note
    modified_lines = FileHandler.append_topic_list(modified_lines, topics)

    # Save modified raw note
    if FileHandler.save_raw_note(raw_note_path, modified_lines):
        render_success(
            f"Successfully generated {success_count}/{len(topics)} atomic note(s)!\n\n"
            f"Saved to: {save_folder}"
        )
        StateManager.set_step(StateManager.STEP_NOTES_GENERATED)
    else:
        render_error("Failed to update the raw note with backlinks.")


def handle_generate_atomic_notes():
    """Handle atomic note generation (sync wrapper)."""
    selected_topics = StateManager.get_selected_topics()

    if not selected_topics:
        render_error("Please select at least one topic to generate atomic notes.")
        return

    # Run async function
    asyncio.run(handle_generate_atomic_notes_async(selected_topics))


def main():
    """Main application entry point."""
    initialize_app()

    # Title
    st.title("📝 노트 분할")
    st.caption("원시 노트를 원자적이고 상호 연결된 지식으로 변환합니다.")

    # Check API key
    if not validate_api_key():
        return

    # Sidebar
    with st.sidebar:
        st.markdown("## Navigation")
        current_step = StateManager.get_current_step()

        st.markdown(f"**Current Step:** {current_step}")

        if st.button("🔄 Reset Application"):
            StateManager.reset()
            st.rerun()

        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            "이 애플리케이션은 AI 기반 토픽 추출을 사용하여 "
            "큰 노트를 원자 노트로 분해하는 데 도움을 줍니다."
        )

    # Main content
    current_step = StateManager.get_current_step()

    # Step 1: Initial Setup
    if current_step == StateManager.STEP_INIT:
        note_path, save_folder, instructions = render_file_input_section()

        if st.button("Start Analysis", type="primary"):
            if note_path:
                handle_note_analysis(note_path, save_folder, instructions)
            else:
                render_error("Please provide a note path.")

    # Step 2: Template Selection
    elif current_step == StateManager.STEP_TEMPLATE_SELECT:
        st.markdown("---")
        loader = PromptLoader(prompts_dir=PROMPTS_DIR)
        templates = loader.get_templates_info()

        selected_template = render_template_selection_section(templates)

        if selected_template:
            handle_template_selection(selected_template)

            if st.button("Extract Topics", type="primary"):
                handle_topic_extraction()

    # Step 3: Topic Management
    elif current_step in [StateManager.STEP_TOPICS_EXTRACTED, StateManager.STEP_NOTES_GENERATED]:
        st.markdown("---")
        st.markdown("## 3. Review and Manage Topics")

        # Batch actions
        render_batch_actions()

        st.markdown("---")

        # Topics list
        topics = StateManager.get_topics()
        render_topics_list(
            topics,
            on_update=handle_topic_update,
            on_delete=handle_topic_delete,
            on_select=handle_topic_selection
        )

        st.markdown("---")

        # Add topics form
        render_add_topics_form(on_add=handle_add_topics)

        st.markdown("---")

        # Generate atomic notes button
        st.markdown("## 4. Generate Atomic Notes")

        selected_topics = StateManager.get_selected_topics()

        if selected_topics:
            st.info(f"Ready to generate {len(selected_topics)} atomic note(s).")

            if st.button("Generate Atomic Notes", type="primary", use_container_width=True):
                handle_generate_atomic_notes()
        else:
            st.warning("Please select at least one topic to generate atomic notes.")

        # Show results if notes were generated
        if current_step == StateManager.STEP_NOTES_GENERATED:
            st.markdown("---")
            st.success("✅ Atomic notes have been generated!")

            save_folder = StateManager.get_save_folder_path()
            raw_note_path = StateManager.get_raw_note_path()

            # Format paths for display (Windows format if in WSL)
            save_folder_display = format_path_for_display(save_folder, prefer_windows_format=True) if save_folder else None
            raw_note_display = format_path_for_display(raw_note_path, prefer_windows_format=True) if raw_note_path else None

            st.markdown(f"**Atomic notes saved to:** `{save_folder_display}`")
            st.markdown(f"**Raw note updated:** `{raw_note_display}`")


if __name__ == "__main__":
    main()
