"""
multimodal_gemma.py
Gemma 4 multimodal integration for Livelihood Voice Assistant.

Accepts: audio transcript (str), image file path (str), or plain text (str).
Returns: Structured JSON "Skill & Livelihood Profile".

Falls back gracefully to deterministic mock output when API key is absent.
"""

import os
import json
import re
import base64
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import the Google GenAI SDK; fall back to mock mode if unavailable
# ---------------------------------------------------------------------------
try:
    import google.generativeai as genai  # pip install google-generativeai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Running in MOCK mode.")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GEMMA_API_KEY = os.getenv("GEMINI_API_KEY", "")          # Set in .env or environment
GEMMA_MODEL   = os.getenv("GEMMA_MODEL", "gemma-3-27b-it")  # or gemma-4 when available

SYSTEM_PROMPT = """
You are the Livelihood AI, an empathetic skill-extraction engine for informal and rural workers in India who may have no formal degrees but possess deep, real-world expertise.

Your task: Given a spoken/written description of someone's work experience, OR tool descriptions from an uploaded image, extract a STRICT JSON object with exactly these keys:

{
  "name": "string or 'Worker' if unknown",
  "occupation": "inferred occupation title",
  "years_experience": integer (estimate if not stated),
  "skills": ["list", "of", "skills", "as", "short", "kebab-case", "tags"],
  "tools_detected": ["tools", "mentioned", "or", "visible", "in", "image"],
  "experience_level": "Beginner | Intermediate | Expert",
  "confidence_score": float between 0 and 1,
  "raw_summary": "1-2 sentence empathetic summary of the worker's journey",
  "language_detected": "English | Hindi | Tamil | etc.",
  "input_type": "voice | image | text"
}

Be generous and encouraging. Recognize informal knowledge. Return ONLY valid JSON, no markdown, no explanation.
""".strip()

# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def _encode_image_base64(image_path: str) -> Optional[str]:
    """Encode image to base64 string for multimodal API calls."""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"Cannot read image {image_path}: {e}")
        return None


def _infer_mime_type(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(ext, "image/jpeg")


# ---------------------------------------------------------------------------
# Core extraction – REAL Gemma 4 path
# ---------------------------------------------------------------------------

def _extract_with_gemma(
    transcript: Optional[str],
    image_path: Optional[str],
    text_input: Optional[str],
) -> dict:
    """Call Gemma 4 via Google GenAI SDK and parse the JSON response."""
    genai.configure(api_key=GEMMA_API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMMA_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )

    parts = []

    # Determine input type
    if image_path:
        encoded = _encode_image_base64(image_path)
        if encoded:
            parts.append({
                "inline_data": {
                    "mime_type": _infer_mime_type(image_path),
                    "data": encoded,
                }
            })
            parts.append({
                "text": (
                    transcript or text_input or
                    "Please analyze the tools and materials visible in this image and extract the worker's skill profile."
                )
            })
    elif transcript:
        parts.append({"text": f"Voice transcript from worker: {transcript}"})
    elif text_input:
        parts.append({"text": f"Worker description (text input): {text_input}"})
    else:
        raise ValueError("At least one of transcript, image_path, or text_input must be provided.")

    response = model.generate_content(parts)
    raw = response.text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


# ---------------------------------------------------------------------------
# Deterministic mock output (when API key is missing or in test mode)
# ---------------------------------------------------------------------------

_MOCK_PROFILES = {
    "carpenter": {
        "name": "Rajesh Kumar",
        "occupation": "Master Carpenter",
        "years_experience": 15,
        "skills": [
            "woodworking", "furniture-joinery", "hand-tools",
            "wood-finishing", "custom-design", "measurement",
            "wood-identification"
        ],
        "tools_detected": [
            "hand saw", "chisel", "mallet", "wood lathe",
            "measuring tape", "sandpaper block"
        ],
        "experience_level": "Expert",
        "confidence_score": 0.91,
        "raw_summary": (
            "Rajesh has 15 years of deep, hands-on carpentry experience "
            "crafting custom furniture — skill that rivals any formally trained craftsman."
        ),
        "language_detected": "Hindi",
        "input_type": "voice",
    },
    "weaver": {
        "name": "Meena Devi",
        "occupation": "Master Handloom Weaver",
        "years_experience": 20,
        "skills": [
            "silk-weaving", "Banarasi-brocade", "loom-operation",
            "color-dyeing", "pattern-design", "quality-control", "natural-dyes"
        ],
        "tools_detected": [
            "handloom", "shuttle", "bobbin", "warping board",
            "reed", "natural dye vessels"
        ],
        "experience_level": "Expert",
        "confidence_score": 0.94,
        "raw_summary": (
            "Meena has 20 years mastering the art of Banarasi brocade weaving — "
            "a rare, globally recognized skill passed down through generations."
        ),
        "language_detected": "Hindi",
        "input_type": "text",
    },
    "hvac": {
        "name": "Suresh Babu",
        "occupation": "AC & Refrigeration Technician",
        "years_experience": 10,
        "skills": [
            "refrigerant-handling", "electrical-wiring", "compressor-repair",
            "gas-charging", "split-AC-installation", "troubleshooting",
            "multimeter-usage"
        ],
        "tools_detected": [
            "multimeter", "manifold gauge set", "vacuum pump",
            "leak detector", "pipe cutter", "refrigerant cylinder"
        ],
        "experience_level": "Intermediate",
        "confidence_score": 0.88,
        "raw_summary": (
            "Suresh has 10 years of practical HVAC expertise and has independently "
            "serviced hundreds of AC units — a commercially valuable technician."
        ),
        "language_detected": "Tamil",
        "input_type": "text",
    },
}

_DEFAULT_MOCK = {
    "name": "Skilled Worker",
    "occupation": "Multi-trade Artisan",
    "years_experience": 8,
    "skills": [
        "manual-craftsmanship", "quality-inspection", "tool-maintenance",
        "material-selection", "client-communication", "on-site-problem-solving"
    ],
    "tools_detected": ["hand tools", "measuring instruments", "finishing equipment"],
    "experience_level": "Intermediate",
    "confidence_score": 0.82,
    "raw_summary": (
        "This skilled worker brings years of invaluable real-world experience "
        "that demonstrates deep practical knowledge valued in the modern economy."
    ),
    "language_detected": "Hindi",
    "input_type": "text",
}


def _mock_extract(
    transcript: Optional[str],
    image_path: Optional[str],
    text_input: Optional[str],
) -> dict:
    """Return a realistic mock profile based on keyword detection."""
    combined = " ".join(filter(None, [transcript, text_input, image_path or ""])).lower()

    profile_key = "carpenter"  # default
    if any(kw in combined for kw in ["weav", "loom", "saree", "silk", "banarasi", "fabric", "textile"]):
        profile_key = "weaver"
    elif any(kw in combined for kw in ["ac", "hvac", "refriger", "compressor", "cooling", "air condition"]):
        profile_key = "hvac"
    elif any(kw in combined for kw in ["wood", "carpen", "furniture", "chisel", "saw", "lathe", "joiner"]):
        profile_key = "carpenter"
    else:
        # Try to infer from generic construction/trade keywords
        if any(kw in combined for kw in ["construct", "brick", "cement", "plumb", "electric", "weld"]):
            result = _DEFAULT_MOCK.copy()
            result["occupation"] = "Construction Tradesman"
            result["input_type"] = "voice" if transcript else "image" if image_path else "text"
            return result

    result = _MOCK_PROFILES[profile_key].copy()
    result["input_type"] = "voice" if transcript else "image" if image_path else "text"
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_skill_profile(
    transcript: Optional[str] = None,
    image_path: Optional[str] = None,
    text_input: Optional[str] = None,
    force_mock: bool = False,
) -> dict:
    """
    Main entry point for Gemma 4 skill extraction.

    Args:
        transcript:  Transcribed speech from the voice recorder.
        image_path:  Local path to an uploaded work evidence image.
        text_input:  Manual text typed/pasted by the user.
        force_mock:  If True, skip the real API even when credentials are present.

    Returns:
        A dict conforming to the Livelihood Skill Profile schema.
    """
    if not any([transcript, image_path, text_input]):
        raise ValueError("Provide at least one input: transcript, image_path, or text_input.")

    use_real_api = (
        GENAI_AVAILABLE
        and bool(GEMMA_API_KEY)
        and not force_mock
    )

    try:
        if use_real_api:
            logger.info("Calling Gemma 4 via Google GenAI SDK …")
            profile = _extract_with_gemma(transcript, image_path, text_input)
        else:
            logger.info("Using mock extraction (no API key or SDK).")
            profile = _mock_extract(transcript, image_path, text_input)

        # Ensure all required fields exist
        required_fields = [
            "name", "occupation", "years_experience", "skills",
            "tools_detected", "experience_level", "confidence_score",
            "raw_summary", "language_detected", "input_type",
        ]
        for field in required_fields:
            if field not in profile:
                profile[field] = "" if isinstance(profile.get(field), str) else []

        return profile

    except Exception as exc:
        logger.exception(f"Gemma extraction failed: {exc}. Falling back to mock.")
        return _mock_extract(transcript, image_path, text_input)


# ---------------------------------------------------------------------------
# CLI test harness
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_transcript = (
        "Mera naam Rajesh hai. Main 15 saal se lakdi ka kaam karta hoon. "
        "Maine bahut saari custom almari aur dining table banaye hain. "
        "Main haath ke auzaar use karta hoon — saw, chisel, sandpaper."
    )
    result = extract_skill_profile(transcript=test_transcript, force_mock=True)
    print(json.dumps(result, indent=2, ensure_ascii=False))
