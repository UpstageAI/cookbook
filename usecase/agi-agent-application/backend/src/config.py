"""
Configuration settings for the application
"""

import os
import yaml

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "conf.d", "config.yaml")
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
UPLOADS_DIR = os.path.join(BASE_DIR, "src", "uploads")

# Load configuration from YAML
with open(CONFIG_PATH, 'r') as file:
    config = yaml.safe_load(file)

# API settings
OPENAI_API_KEY = config['openai']['key']
UPSTAGE_API_KEY = config['upstage']['key']
TAVILY_API_KEY = config['tavily']['key']  # Added from config.yaml

# Dataset paths
CASE_DB_PATH = os.path.join(DATASETS_DIR, "case_db.json")
EMBEDDING_PATH = os.path.join(DATASETS_DIR, "precomputed_embeddings.npz")

# Prompt paths
SIMULATION_PROMPT_PATH = os.path.join(PROMPTS_DIR, "simulate_dispute.txt")
FORMAT_PROMPT_PATH = os.path.join(PROMPTS_DIR, "format_output.txt")
HIGHLIGHT_PROMPT_PATH = os.path.join(PROMPTS_DIR, "find_toxic_clause.txt")

# Ensure directories exist
for directory in [DATASETS_DIR, PROMPTS_DIR, UPLOADS_DIR]:
    os.makedirs(directory, exist_ok=True)
