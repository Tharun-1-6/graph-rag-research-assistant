'''
Central configuration for the LLM layer:

-> loads API keys from the .env file and stores
-> this file is so that if you want to edit your llm, this is the only file i need to edit
-> for eg, if i want to switch from gemini to openai , i can just change the 
'''


import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# =====================================================
# Provider Configuration
# =====================================================

# Current provider
LLM_PROVIDER = "gemini"

# Default model
LLM_MODEL = "gemini-2.5-flash"

# API Key
LLM_API_KEY = os.getenv("GEMINI_API_KEY")

# =====================================================
# Generation Parameters
# =====================================================

DEFAULT_TEMPERATURE = 0.2

DEFAULT_MAX_OUTPUT_TOKENS = 8192

DEFAULT_TOP_P = 0.95

# =====================================================
# Validation
# =====================================================

if LLM_API_KEY is None:
    raise ValueError(
        "GEMINI_API_KEY not found. "
        "Please add it to your .env file."
    )