"""OpenRouter model setup. The model is created on first use, so the
scheduler and calendar code work even without an API key."""
import os

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("ai_model", "nvidia/nemotron-3.5-lightning:free")
_model = None


def get_model():
    global _model
    if _model is None:
        from langchain_openrouter import ChatOpenRouter
        api_key = os.getenv("ai_api_key")
        if not api_key:
            raise ValueError("ai_api_key not found in .env")
        # If ChatOpenRouter rejects api_key=, rename the .env entry to
        # OPENROUTER_API_KEY and remove the argument.
        _model = ChatOpenRouter(model=MODEL_NAME, temperature=0, api_key=api_key)
    return _model
