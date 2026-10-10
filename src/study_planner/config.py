"""No model is created until an AI feature is used."""
import os

_model = None


def get_model():
    global _model
    if _model is None:
        from dotenv import load_dotenv
        from langchain_openrouter import ChatOpenRouter
        load_dotenv()
        key = os.getenv('OPENROUTER_API_KEY') or os.getenv('ai_api_key')
        if not key:
            raise ValueError('Add OPENROUTER_API_KEY to your .env file')
        name = os.getenv('OPENROUTER_MODEL') or os.getenv('ai_model', 'nvidia/nemotron-3.5-lightning:free')
        _model = ChatOpenRouter(model=name, temperature=0, api_key=key)
    return _model
