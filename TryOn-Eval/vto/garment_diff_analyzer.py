# garment_diff_analyzer.py

import json
import traceback
from typing import Dict, Any
from google import genai
from google.genai import types

from utils import CONFIG
from vto import prompt


def _parse_llm_json(raw_text: str) -> Any:
    cleaned = raw_text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for i, char in enumerate(cleaned):
            if char in ('[', '{'):
                try:
                    obj, _ = decoder.raw_decode(cleaned[i:])
                    return obj
                except json.JSONDecodeError:
                    continue
        return []


def compare_apparel_attributes(
        img1_bytes: bytes,
        img2_bytes: bytes,
        img3_bytes: bytes
) -> Dict[str, Any]:
    """
    Compares specific apparel attributes between an apparel item in the first image, person which will wear that apparel
    in the second image and a VTO output in the thord image.

    """

    try:
        client = genai.Client(vertexai=True, project=CONFIG["project"]["id"], location="global")

        # Load images
        try:
            image_part_1 = types.Part.from_bytes(data=img1_bytes, mime_type='image/png')
            image_part_2 = types.Part.from_bytes(data=img2_bytes, mime_type='image/png')
            image_part_3 = types.Part.from_bytes(data=img3_bytes, mime_type='image/png')
        except Exception as e:
            raise RuntimeError(f"Failed to load image files: {e}. Ensure image bytes are provided correctly.")

        # LLM call
        try:
            content_list = [prompt.GARMENT_DIFF_ANALYSIS_PROMPT, image_part_1, image_part_2, image_part_3]
            response = client.models.generate_content(
                model=CONFIG['gemini']['model_name'],
                contents=content_list,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get response from LLM for pose estimation: {e}. "
                               f"Traceback: {traceback.format_exc()}")

        # Process LLM output
        comparison_result = _parse_llm_json(response.text)

        return {
            "status": "success",
            "report": "Apparel attribute comparison completed.",
            "details": comparison_result
        }

    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred during apparel comparison: {e}"
                           f"Traceback: {traceback.format_exc()}")
