# UpThink

**[Upstage AI Ambassador]** Personal Knowledge Management with Upstage Solar Pro 2 ✨

## Overview

UpThink is a service designed to minimize the repetitive manual effort in Personal Knowledge Management environments (specifically Obsidian).
It addresses the following bottlenecks that inevitably arise during the knowledge organization process.

| Problem | Description |
|------|------|
| **Image Data Processing** | Manual conversion of visual information into text |
| **Tag Management** | Maintaining tag conventions and styling concerns |
| **Lack of Knowledge Connectivity** | Search costs for finding relevant past notes |
| **Unstructured Documents** | Need for splitting massive notes |

UpThink automates these processes based on the powerful language understanding capabilities of **Upstage Solar Pro 2**.
Users can break free from simple repetitive tasks and focus on what matters most—thinking.

### Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
  - [Flow Chart](#flow-chart)
- [Installation](#installation)
- [Usage](#usage)
  - [Watch Demo Video](#-watch-demo-video-youtube-)
- [Project Structure](#project-structure)
- [Members & Roles](#members--roles)
- [Acknowledgements](#acknowledgements)

## Key Features

### 1️⃣ Image Alt Text Generation

Extracts text from images within notes and automatically generates alt text describing the image content.

- Perform OCR and extract document structure from images using **Upstage Document Parse**
- Generate alt text of around 50 words based on extracted text using **Solar Pro 2**
- Batch process all images within markdown files
- Automatically insert alt text below image links in `![[image.png]]` format

### 2️⃣ Tag Recommendation

Analyzes note content to recommend appropriate tags and maintains consistency with existing Vault tag conventions.

- Automatically collect existing tags in Vault (supports hashtags `#tag` and YAML frontmatter)
- Set user-defined tag guidelines (language, case, separators, number of tags)
- Generate tags based on note content using **Solar Pro 2**
- Compare and match similarity with existing tags using **Qwen Embedding** model
- Automatically insert tags in YAML frontmatter format

### 3️⃣ Related Note Recommendation

Finds notes semantically similar to the current note and automatically connects them.

- Vectorize notes in Vault using **Upstage Embedding Model** and **Chroma DB**
- Automatically identify and batch process unembedded notes
- Process long notes through chunking
- Recommend Top 3 related notes via similarity search
- Automatically append backlinks to the `## Related Notes` section using the `[[note]]` format

### 4️⃣ Note Splitting

Splits massive notes by topic to atomize them and build an interconnected knowledge system.

- Automatically extract topics within notes using **Solar Pro 2**
- Support flexible splitting strategies based on templates
- Edit, delete, or add extracted topics
- Automatically generate and save split atomic notes
- Automatically insert backlinks and `## Generated Atomic Notes` section in original note

## Tech Stack

| Category | Technology |
|------|------|
| **Language** | Python 3.13 |
| **Frontend** | Streamlit |
| **LLM** | Upstage Solar Pro 2 |
| **Document AI** | Upstage Document Parse |
| **Embedding** | Upstage Embedding, Qwen3-Embedding-0.6B |
| **Vector DB** | Chroma DB |
| **Framework** | LangChain |
| **Package Manager** | uv |

## Architecture

<img width="500" alt="Image" src="https://github.com/user-attachments/assets/ada44519-ae1c-4490-a4ae-22c2520b237b" />
<br>
<br>

| Layer | Component | Description |
|--------|-----------|------|
| **Frontend** | Streamlit | Web-based User Interface |
| **Backend** | Python Modules | Implementation of 4 core features |
| **Upstage API** | Solar Pro 2, Document Parse, Embedding Model | LLM, OCR, Vector Embedding |
| **Local** | Qwen Embedding, Chroma DB | Tag similarity comparison, Note vector storage |

### Flow Chart

#### Image Alt Text Generation

<img width="600" alt="Image" src="https://github.com/user-attachments/assets/9d7a9c48-0e53-45f3-88d9-1cb0c6ea3981" />
<br>
<br>

| Step | Flow | Key Backend Modules |
|:----:|------|-------------------|
| 1 | Extract image links and check alt text existence | `MarkdownImageProcessor._collect_images_to_process()` |
| 1 | Search image file paths in Vault | `MarkdownImageProcessor._find_image_in_vault()` |
| 2 | Extract text from image | `OCRProcessor.extract_text()` |
| 2 | Generate alt text | `AltTextGenerator.generate_alt_text()` |
| 3 | Insert alt text below image link | `MarkdownImageProcessor.process_images()` |

#### Tag Recommendation

<img width="600" alt="Image" src="https://github.com/user-attachments/assets/4b950ff7-6a1b-4df9-ac76-afc5f1defac9" />
<br>
<br>

| Step | Flow | Key Backend Modules |
|:----:|------|-------------------|
| 1 | Collect and check existing tags | `TagExtractor.get_unique_tags()`, `TagExtractor.count_tags()` |
| 2 | Set tag guidelines and generate new tags | `GuidelineGenerator()`, `TagGenerator.generate_tags()` |
| 3 | Compare existing and new tags | `TagComparator.compare_tags()` |
| 3 | Suggest final tags | `TagComparator.get_final_tags()` |
| 4 | Insert YAML Frontmatter | `add_yaml_frontmatter()` |

#### Related Note Recommendation

<img width="600" alt="Image" src="https://github.com/user-attachments/assets/1ee795f1-9bcc-4916-9bbc-190dff0ee82e" />
<br>
<br>

| Step | Flow | Key Backend Modules |
|:----:|------|-------------------|
| 1 | Identify unembedded notes | `Related_Note.get_unembedded_notes()` |
| 2 | Preprocessing and chunking | `Related_Note.clean_text()`, `Related_Note.chunk_text()` |
| 2 | Embed notes and save to DB | `Related_Note.index_unembedded_notes()` |
| 3 | Search related notes | `Related_Note.find_related_notes()` |
| 4 | Insert backlinks | `Related_Note.append_related_links()` |

#### Note Splitting

<img width="600" alt="Image" src="https://github.com/user-attachments/assets/f834e4a6-7227-4dcd-81e3-5087cf5f218c" />
<br>
<br>

| Step | Flow | Key Backend Modules |
|:----:|------|-------------------|
| 1 | Load prompt template | `PromptLoader.load_template()` |
| 1 | Extract Topic | `UpstageClient.generate_with_template_sync()` |
| 2 | Parse Topic list | `ResponseParser.parse_topics_from_json()` |
| 3 | Generate atomic notes | `FileHandler.create_atomic_note()` |
| 3 | Insert backlinks | `FileHandler.insert_backlinks()` |

## Installation

### Supported Environments
- macOS
- Windows (PowerShell, CMD)

### Install uv

- https://docs.astral.sh/uv/getting-started/installation/

#### Homebrew

```
brew install uv
```

#### Windows

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Project Setup

```
# git clone
git clone https://github.com/geminii01/product-usecase-knowledge-management-upthink.git
cd product-usecase-knowledge-management-upthink
```
```
# Environment Variable Setup (Required!)
cp .env.example .env

# Open .env file and enter API keys
# UPSTAGE_API_KEY=your_api_key_here
# TAVILY_API_KEY=your_api_key_here
```
```
# Install Python 3.13 and dependencies automatically
uv sync
```

### Run

```
streamlit run frontend/app.py

# Access via Local URL below!
# http://localhost:8501
```

## Usage

### 🎬 Watch Demo Video: [YouTube](https://www.youtube.com/watch?v=8bjLew7KTW4) 🎬

### Basic Usage

1. Enter **Vault Path** in the sidebar. (Absolute path to Obsidian Vault)
2. Upload **Markdown file** to process.
3. Go to the desired feature page and execute.

## Project Structure

```
upthink/
├── frontend/                     # Streamlit Frontend
│   ├── app.py                    # Main App (Routing, Common Sidebar)
│   ├── home.py                   # Home Page
│   ├── image_ocr.py              # Image Alt Text Generation UI
│   ├── tag_suggest.py            # Tag Recommendation UI
│   ├── related_note.py           # Related Note Recommendation UI
│   ├── note_split.py             # Note Splitting UI
│   └── note_freshness.py         # Freshness Check UI
│
├── backend/                      # Backend Logic
│   ├── image_ocr/                # Image OCR & Alt Text Generation
│   │   ├── ocr_processor.py      # Document Parse API Integration
│   │   ├── alt_text_generator.py # Solar Pro 2 Alt Text Generation
│   │   └── markdown_processor.py # Markdown Image Processing
│   │
│   ├── tag_suggest/              # Tag Suggestion
│   │   ├── tag_extractor.py      # Extract 2 Tag Patterns
│   │   ├── tag_guidelines.py     # Guideline Generation
│   │   ├── tag_generator.py      # Solar Pro 2 Tag Generation
│   │   ├── tag_comparator.py     # Qwen Embedding Similarity Comparison
│   │   └── markdown_processor.py # YAML frontmatter Processing
│   │
│   ├── related_note/             # Related Note Recommendation
│   │   └── related_note.py       # Chroma DB based Similarity Search
│   │
│   ├── note_split/               # Note Splitting
│   │   ├── config.py             # Config
│   │   ├── models.py             # Data Models
│   │   ├── core/                 # State Management, File Handling
│   │   ├── llm/                  # LLM Client, Prompt Loader
│   │   └── ui/                   # UI Components
│   │
│   └── note_freshness/           # Freshness Verification
│       ├── api/                  # Tavily, Wikipedia API
│       ├── core/                 # State Management
│       └── llm/                  # LLM Integration
│
├── prompts/                      # Prompt Templates (YAML)
├── pyproject.toml                # Project Configuration & Dependencies
└── .env.example                  # Environment Variable Example
```

## Members & Roles

| Kim Su-yeon | Oh Ju-yeong | Yoon I-ji | Hong Jae-min |
|:------:|:------:|:------:|:------:|
| <a href="https://github.com/rlatndusgu" target="_blank"><img src="https://avatars.githubusercontent.com/u/204878926?v=4" height=130 width=130></img></a><br><a href="https://github.com/rlatndusgu" target="_blank"><img src="https://img.shields.io/badge/GitHub-black.svg?&style=round&logo=github"/> | <a href="https://github.com/Secludor" target="_blank"><img src="https://avatars.githubusercontent.com/u/129930239?v=4" height=130 width=130></img></a><br><a href="https://github.com/Secludor" target="_blank"><img src="https://img.shields.io/badge/GitHub-black.svg?&style=round&logo=github"/> | <a href="https://github.com/Yiji-1015" target="_blank"><img src="https://avatars.githubusercontent.com/u/122429800?v=4" height=130 width=130></img></a><br><a href="https://github.com/Yiji-1015" target="_blank"><img src="https://img.shields.io/badge/GitHub-black.svg?&style=round&logo=github"/> | <a href="https://github.com/geminii01" target="_blank"><img src="https://avatars.githubusercontent.com/u/171089104?v=4" height=130 width=130></img></a><br><a href="https://github.com/geminii01" target="_blank"><img src="https://img.shields.io/badge/GitHub-black.svg?&style=round&logo=github"/> |
| ▪︎ Developed Image Alt Text Generation Feature | ▪︎ Developed Note Splitting Feature <br> ▪︎ Integrated Freshness Verification | ▪︎ PM <br> ▪︎ Developed Related Note Recommendation Feature | ▪︎ Developed Tag Recommendation Feature <br> ▪︎ GitHub Management & Team Code Integration |

## Acknowledgements

This project was conducted as part of the **Upstage AI Ambassador** program. \
We thank **[Upstage](https://www.upstage.ai/)** for providing credits to support this project.
