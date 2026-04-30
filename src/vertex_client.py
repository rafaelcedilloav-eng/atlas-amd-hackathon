"""
ATLAS Vertex AI Client
Wrapper for Gemini models on Vertex AI.
Supports multimodal PDF input and Google Search grounding.
"""
import os
import logging
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

_PROJECT  = os.getenv("GOOGLE_CLOUD_PROJECT", "")
_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Cloud deployment: service account JSON as env var → temp file
_sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if _sa_json and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    try:
        _tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        _tmp.write(_sa_json)
        _tmp.close()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _tmp.name
        logger.info("Service account loaded from GOOGLE_SERVICE_ACCOUNT_JSON")
    except Exception as _e:
        logger.warning(f"Could not write service account JSON to temp file: {_e}")

_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(
            vertexai=True,
            project=_PROJECT,
            location=_LOCATION,
        )
    return _client


def call_gemini(
    prompt: str,
    model: str = "gemini-2.5-flash",
    pdf_path: Optional[str] = None,
    system: Optional[str] = None,
    with_search: bool = False,
    temperature: float = 0.1,
) -> str:
    """
    Call a Gemini model on Vertex AI.
    pdf_path  → attach PDF as multimodal Part
    with_search → enable Google Search grounding
    """
    from google.genai import types

    client = _get_client()
    contents = []

    if pdf_path:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        contents.append(
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
        )

    contents.append(prompt)

    config_kwargs: dict = {"temperature": temperature}

    if system:
        config_kwargs["system_instruction"] = system

    if with_search:
        config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(**config_kwargs),
    )

    return response.text
