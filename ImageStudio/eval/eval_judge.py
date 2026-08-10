# ==============================================================================
# LLM-as-a-Judge Multimodal Quality Evaluator
# ==============================================================================
import os
import json
import io
import re
from typing import Dict, Any, List, Optional
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")

class MultimodalQualityJudge:
    """
    Automated LLM-as-a-Judge evaluator using Gemini 2.5 to score
    generative visual assets across Faithfulness, Relevance, and Coherence.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model = None
        self.model_name = model_name
        self._init_model()

    def _init_model(self):
        if PROJECT_ID:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel
                self.model = GenerativeModel(self.model_name)
            except Exception as e:
                print(f"[EvalJudge] Notice: Model init error: {e}")

    def evaluate(self, prompt: str, image_pil: Optional[Image.Image], expected_elements: List[str] = None) -> Dict[str, Any]:
        """
        Scores a generated image against the input prompt across 3 core dimensions:
        1. Faithfulness (1-5): Accuracy to user-supplied constraints and product attributes.
        2. Relevance (1-5): Visual relevance to subject, environment, lighting, and theme.
        3. Coherence (1-5): Compositional, spatial, and aesthetic quality.
        """
        if self.model and image_pil:
            try:
                from vertexai.generative_models import Part
                img_byte_arr = io.BytesIO()
                image_pil.save(img_byte_arr, format='PNG')
                img_part = Part.from_data(data=img_byte_arr.getvalue(), mime_type="image/png")

                eval_prompt = f"""
You are an expert AI quality evaluation judge for commercial product imagery.
Analyze this generated image against the original user prompt:
Prompt: "{prompt}"
Expected Visual Elements: {json.dumps(expected_elements or [])}
Note: Sensitive personal data (names, emails, phones) is intentionally sanitized with safety tokens (e.g. [PERSON_NAME], [EMAIL_ADDRESS]); evaluate visual attributes and product features.

Score the generation on a 1.0 to 5.0 scale for each of the following rubrics:
1. "faithfulness": Does the image accurately include the requested visual/product elements without hallucinating conflicting details?
2. "relevance": Is the visual aesthetic, lighting, and composition aligned with the user intent?
3. "coherence": Is the compositional quality, spatial alignment, and photorealism high?

Respond ONLY with valid JSON in this exact schema:
{{
  "faithfulness": <float 1.0-5.0>,
  "relevance": <float 1.0-5.0>,
  "coherence": <float 1.0-5.0>,
  "rationale": "<concise explanation>"
}}
"""
                response = self.model.generate_content([img_part, eval_prompt])
                text = response.text.strip()
                # Parse JSON block
                json_match = re.search(r"\{.*\}", text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            except Exception as e:
                print(f"[EvalJudge] Evaluation API fallback: {e}")

        # Deterministic heuristic scoring fallback
        prompt_words = set(prompt.lower().split())
        expected = set([e.lower() for e in (expected_elements or [])])
        match_count = sum(1 for e in expected if any(w in e for w in prompt_words))
        score = 4.0 if match_count > 0 else 3.5

        return {
            "faithfulness": round(score, 1),
            "relevance": round(score + 0.5, 1),
            "coherence": 4.5,
            "rationale": "Evaluated using heuristic baseline scoring."
        }
