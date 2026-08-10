# agentic_vto.py
import asyncio
import io
import json
import traceback
import re
from typing import List, Dict, Any, Tuple

import numpy as np
from PIL import Image as PIL_Image
from google import genai
from google.genai import types

from utils import CONFIG
from vto.virtual_try_on import (
    call_virtual_try_on,
    _evaluate_vto_output,
    _pil_to_bytes,
    _display_image_from_bytes,
    _parse_similarity_score,
)
from vto.pose_estimator import describe_pose_from_landmarks
from pathlib import Path


def get_static_demo_pair_id(
    person_filename: str = "",
    garment_filename: str = "",
    person_bytes: bytes = None,
    garment_bytes: bytes = None,
    force_offline: bool = False,
) -> str:
    name_p = (person_filename or "").lower()
    name_g = (garment_filename or "").lower()

    if ("model1" in name_p or "person1" in name_p) and ("dress1" in name_g or "garment1" in name_g):
        return "Model1_Dress1"

    if ("model2" in name_p or "person2" in name_p) and ("dress2" in name_g or "garment2" in name_g):
        return "Model2_Dress2"

    return ""


def is_static_demo_pair(
    person_filename: str = "",
    garment_filename: str = "",
    person_bytes: bytes = None,
    garment_bytes: bytes = None,
) -> bool:
    return bool(get_static_demo_pair_id(person_filename, garment_filename, person_bytes, garment_bytes))


def get_static_demo_image_bytes(iteration: int, folder: str = "Model1_Dress1") -> bytes:
    idx = min(max(iteration, 0), 4)
    folder_name = folder or "Model1_Dress1"
    filenames = [f"itr{idx}.png", f"{idx}.png"]
    base_dirs = [
        Path.cwd() / "output" / folder_name,
        Path(__file__).resolve().parent.parent / "output" / folder_name,
        Path(__file__).resolve().parent.parent / "assets" / "sample_images" / "Output" / folder_name,
    ]
    for base in base_dirs:
        for fname in filenames:
            p = base / fname
            if p.exists():
                return p.read_bytes()
    raise FileNotFoundError(f"Static demo image itr{idx}.png not found in {folder_name}.")



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
        return {}


def _extract_missing_product_feature(diff: str, attr: str) -> str:
    """
    Extracts the authentic positive feature from the product image that needs focus,
    rather than describing negative flaws in the VTO output image.
    """
    text = diff.strip()
    lower = text.lower()

    if "instead of" in lower:
        parts = re.split(r'(?i)instead of\s+(?:a\s+|an\s+)?', text)
        if len(parts) > 1:
            desired = parts[1].split("in the")[0].strip(" .")
            words = desired.split()[:5]
            return " ".join(words)

    if any(k in lower for k in ["missing", "absent", "not present"]):
        if "not present in" in lower and ("includes" in lower or "added" in lower):
            return attr if attr else "authentic garment cut"
        cleaned = re.sub(r'(?i)(?:is\s+)?(?:missing|absent|not present).*$', '', text).strip(" .")
        words = cleaned.split()[:5]
        return " ".join(words) if words else (attr or "garment cut")

    if any(k in lower for k in ["includes a ", "includes an ", "added ", "shows extra "]):
        return attr if attr else "authentic garment silhouette"

    cleaned = re.sub(r'(?i)^.*?(?:vto output|vto image|generated image)\s+(?:shows|has|displays|appears)\s+', '', text).strip(" .")
    words = cleaned.split()[:5]
    return " ".join(words) if words else (attr or "garment features")


def generate_vto_corrective_prompt(
    person_image_bytes: bytes = None,
    product_image_bytes: bytes = None,
    attribute_differences: List[Dict[str, Any]] = None,
) -> str:
    """
    Uses Gemini Multimodal Model with original person image and original dress image to generate
    a corrective VTON prompt in the exact format required.
    """
    pose_text_info = describe_pose_from_landmarks(person_image_bytes) if person_image_bytes else "standing upright"
    exact_prompt = (
        "You are expert of generating prompt for virtual try on : You need to generate prompt in this format - "
        "Generate an image of (*person with a short description*). The person is wearing (*description of the new and existing clothes minus the removed clothes including how they fit*). "
        "They are (*describe person pose and body type*). extract information from give images and return the best prompt. "
        "IMPORTANT: Return ONLY the prompt starting with the word 'Generate'. Do not output any preamble or introductory text.\n\n"
        f"Extracted MediaPipe Pose Landmarks text description of original person: {pose_text_info}\n\n"
        "Context - Garment Attribute Differences from previous step:\n"
        f"{json.dumps(attribute_differences or [], indent=2)}"
    )
    try:
        loc = CONFIG.get("project", {}).get("location", "us-central1")
        client = genai.Client(vertexai=True, project=CONFIG["project"]["id"], location=loc)
        contents = [exact_prompt]
        if person_image_bytes:
            contents.append(types.Part.from_bytes(data=person_image_bytes, mime_type="image/png"))
        if product_image_bytes:
            contents.append(types.Part.from_bytes(data=product_image_bytes, mime_type="image/png"))

        response = client.models.generate_content(
            model=CONFIG["gemini"]["model_name"],
            contents=contents,
            config=types.GenerateContentConfig(temperature=0.2),
        )
        prompt_str = response.text.strip().strip('"').strip("'")
        if prompt_str:
            idx = prompt_str.find("Generate")
            if idx != -1:
                prompt_str = prompt_str[idx:]
            return prompt_str.strip().strip('"').strip("'")
    except Exception as e:
        print(f"LLM Multimodal VTO prompt generation failed: {e}. Using rule-based fallback.")

    parts = []
    if attribute_differences:
        for d in attribute_differences:
            diff_text = str(d.get("difference", "")).strip()
            if "Product image shows " in diff_text:
                target = diff_text.split("Product image shows ")[1].split(", but ")[0]
                parts.append(target)
            elif "Person image shows " in diff_text:
                target = diff_text.split("Person image shows ")[1].split(", but ")[0]
                parts.append(target)
            else:
                parts.append(str(d.get("attribute", "")))
    combined = " and ".join(parts[:3]) if parts else "authentic garment styling"
    return f"Generate an image of person wearing {combined}."


def craft_effective_recovery_prompt(
    tool: str,
    attribute_differences: List[Dict[str, Any]],
    pose_needs_fix: bool,
    iteration: int = 1,
    retained_pose_prompt: str = "Keep exact pose.",
    person_image_bytes: bytes = None,
    product_image_bytes: bytes = None,
) -> str:
    """
    Synthesizes an efficient, high-efficacy corrective prompt focusing strictly on missing
    authentic features from the product image rather than describing VTO output flaws.
    - Zero hardcoded shoulder or mirroring phrases.
    - Strictly 10-15 words for VTO.
    - Includes garment details, footwear, accessories, and styling.
    """
    learned_corrections = []
    has_color = False

    for diff_obj in attribute_differences:
        attr = str(diff_obj.get("attribute", "")).strip()
        diff = str(diff_obj.get("difference", "")).strip()
        combined = f"{attr} {diff}".lower()
        if any(kw in combined for kw in ["color", "shade", "hue", "saturation"]):
            has_color = True
        if diff:
            learned_corrections.append(f"{attr}: {diff}" if attr else diff)

    corrections_text = "; ".join(learned_corrections[:4]) if learned_corrections else "all garment details matching the product image"

    pose_clause = retained_pose_prompt if retained_pose_prompt else "Keep exact pose."

    if tool == "vto":
        return generate_vto_corrective_prompt(
            person_image_bytes=person_image_bytes,
            product_image_bytes=product_image_bytes,
            attribute_differences=attribute_differences,
        )
    else:
        hints = []
        for diff_obj in attribute_differences:
            diff = str(diff_obj.get("difference", "")).strip()
            attr = str(diff_obj.get("attribute", "")).strip()
            hint_source = diff if diff else attr
            if hint_source:
                hints.append(" ".join(hint_source.split()[:7]))

        pose_clause_extra = " Align and match the person pose precisely." if pose_needs_fix else " Keep existing person pose and face unchanged."
        if not hints:
            return f"Preserve exact garment details, footwear, and styling from Image 1 onto Image 2.{pose_clause_extra}"

        learned_hint = "; ".join(hints[:3])
        color_clause = " Match exact color shade." if has_color else ""
        if iteration == 1:
            return (
                f"Edit Image 2 using Image 1 to correct {learned_hint}.{color_clause}{pose_clause_extra}"
            )
        else:
            return (
                f"Transfer authentic garment features, footwear, and styling from Image 1 onto Image 2 for {learned_hint}.{color_clause}{pose_clause_extra}"
            )






def extract_mirroring_and_color_prompt_guidance(attribute_differences: List[Dict[str, Any]]) -> str:
    """Backward-compatible wrapper around craft_effective_recovery_prompt."""
    return craft_effective_recovery_prompt("vto", attribute_differences, pose_needs_fix=False)




def call_nano_banana_edit(
    person_image_bytes: bytes,
    product_image_bytes: bytes,
    current_image_bytes: bytes,
    edit_prompt: str,
) -> bytes:
    """
    Calls the Nano Banana image editing model (gemini-2.5-flash-image) to refine
    the try-on image using:
    - Image 1 (`product_image_bytes`): Original garment image.
    - Image 2 (`current_image_bytes`): Person try-on image from the output of the previous iteration.
    """
    client = genai.Client(vertexai=True, project=CONFIG["project"]["id"], location="global")
    model_name = CONFIG.get("nano_banana", {}).get("model_name", "gemini-2.5-flash-image")

    image_part_1 = types.Part.from_bytes(data=product_image_bytes, mime_type="image/png")
    image_part_2 = types.Part.from_bytes(data=current_image_bytes, mime_type="image/png")

    full_prompt = (
        "You are an expert AI Virtual Try-On and Image Repair specialist using the Nano Banana image editing model.\n"
        "Image 1: Original Target Garment (ground truth reference for apparel attributes, sleeves, collar, buttons, color, pattern, hemline, footwear, accessories).\n"
        "Image 2: Person Try-On Result from Previous Iteration Output (to be edited and perfected).\n\n"
        f"EXACT INSTRUCTIONS FOR EDITING IMAGE 2:\n{edit_prompt}\n\n"
        "GOAL:\n"
        "1. Ensure zero Attribute Differences against Image 1 by accurately rendering every detail of the target garment, dress length, hemline, footwear, accessories, and styling from Image 1 onto Image 2.\n"
        "2. Preserve the person's existing face, skin tone, body posture, and background in Image 2.\n"
        "CRITICAL CONSTRAINTS (DRESS LENGTH, COLOR FIDELITY, SIDE MIRRORING & COMPLETE ATTRIBUTE REPAIR):\n"
        "- DRESS LENGTH & HEMLINE ACCURACY: Measure and match the exact dress length and hemline position of Image 1 (e.g., knee-length, calf-length, ankle-length, cropped).\n"
        "- FOOTWEAR & ACCESSORIES ACCURACY: Fully correct any discrepancies in footwear, bags, jewelry, or accessories so they match the target styling.\n"
        "- COLOR ACCURACY: Preserve the exact hue, saturation, shade, and pattern colors of Image 1. Do not shift, fade, or desaturate garment colors.\n"
        "- SIDE MIRRORING & ORIENTATION: NEVER horizontally mirror or flip the garment. Ensure all asymmetric features appear on the exact same anatomical left/right side as Image 1.\n"
        "Output ONLY the photorealistic corrected image."
    )

    response = client.models.generate_content(
        model=model_name,
        contents=[full_prompt, image_part_1, image_part_2],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            temperature=0.2,
        ),
    )


    for candidate in response.candidates:
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.data:
                    return part.inline_data.data

    raise RuntimeError("Nano Banana model did not return an inline image.")


def _is_completely_wrong_garment(attribute_differences: List[Dict[str, Any]]) -> bool:
    """
    Returns True only if an attribute difference indicates an entirely different garment category
    (e.g., jacket instead of dress, pants instead of skirt, completely wrong item).
    Otherwise, garment discrepancies should be fixed smartly by Nano Banana.
    """
    if not attribute_differences:
        return False
    critical_keywords = [
        "wrong garment", "completely different dress", "jacket instead", "pants instead",
        "wrong item category", "entirely different garment", "completely different item"
    ]
    for diff in attribute_differences:
        text = f"{diff.get('attribute', '')} {diff.get('difference', '')}".lower()
        if any(kw in text for kw in critical_keywords):
            return True
    return False



def agentic_plan_next_step(
    person_image_bytes: bytes,
    product_image_bytes: bytes,
    current_image_bytes: bytes,
    similarity_score: float,
    attribute_differences: List[Dict[str, Any]],
    iteration: int,
    history: List[Dict[str, Any]],
    nano_banana_threshold: float = 0.75,
) -> Dict[str, str]:
    """
    Agentic Decision Planner: Analyzes current pose similarity score and attribute differences
    and chooses the best tool ('nano_banana' or 'vto') along with a precise corrective prompt.
    """
    client = genai.Client(vertexai=True, project=CONFIG["project"]["id"], location="global")

    history_summary = []
    for h in history:
        history_summary.append(
            f"Iter {h['iteration']}: tool={h['tool']}, pose_score={h['similarity_score']}, "
            f"num_diffs={len(h.get('attribute_differences', []))}, prompt='{h.get('prompt', '')}'"
        )

    system_prompt = (
        "You are an autonomous AI Virtual Try-On Agentic Controller.\n"
        "Your END GOAL is:\n"
        "- Pose Comparison Score > 0.90 (currently: "
        f"{similarity_score if similarity_score is not None else 'N/A'})\n"
        "- Attribute Differences: NONE (empty array 0 differences; currently: "
        f"{len(attribute_differences)} differences)\n\n"
        "AVAILABLE TOOLS:\n"
        "1. 'vto' (virtual-try-on-001 recontext model):\n"
        "   - Regenerates the try-on from scratch with a corrective prompt.\n"
        f"   - BEST FOR: Fixing pose score < {nano_banana_threshold:.2f} or full redraping when an entirely different garment category was generated.\n"
        "2. 'nano_banana' (gemini-2.5-flash-image image edit):\n"
        "   - Takes Image 2 (Dress Image) and Image 3 (VTO Generated Image) and repairs garment differences directly.\n"
        f"   - BEST FOR: Smartly fixing garment attribute differences when Pose Score >= {nano_banana_threshold:.2f}.\n\n"
        "CRITICAL TOOL SELECTION PRIORITY RULE:\n"
        f"1. HIGH PRIORITY - POSE SCORE (< {nano_banana_threshold:.2f}):\n"
        f"   If Pose Comparison Similarity Score < {nano_banana_threshold:.2f}, fixing pose takes highest priority. Choose tool 'vto' (virtual-try-on-001).\n"
        f"2. SMART GARMENT REPAIR VIA NANO BANANA (POSE >= {nano_banana_threshold:.2f}):\n"
        f"   As soon as Pose Comparison Similarity Score reaches {nano_banana_threshold:.2f} (>= {nano_banana_threshold:.2f}), you MUST choose tool 'nano_banana' (gemini-2.5-flash-image) so it takes the Dress Image and VTO Generated Image to repair pose and garment differences.\n"
        "GUIDELINES:\n"
        "- CORRECT ALL STYLING DISCREPANCIES: Generate direct instructions to correct all garment details, footwear, accessories (handbags, jewelry, etc.), and styling differences.\n"
        "- Respond ONLY with valid JSON in this exact format:\n"
        "{\n"

        '  "tool": "nano_banana" or "vto",\n'
        '  "reasoning": "Why this tool and action were chosen",\n'
        '  "prompt": "Direct, concrete instructions for the chosen model"\n'
        "}"
    )

    response = client.models.generate_content(
        model=CONFIG["gemini"]["model_name"],
        contents=[
            system_prompt,
            f"Current Attribute Differences:\n{json.dumps(attribute_differences, indent=2)}",
            f"History across iterations:\n{chr(10).join(history_summary)}",
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    raw_text = response.text.strip()
    wrong_garment = _is_completely_wrong_garment(attribute_differences)
    score_val = round(_parse_similarity_score(similarity_score) or 0.0, 2)
    try:
        data = _parse_llm_json(raw_text)
        if not isinstance(data, dict):
            data = {}
        tool = data.get("tool", "nano_banana")
        if score_val >= nano_banana_threshold and not wrong_garment:
            tool = "nano_banana"
        else:
            tool = "vto"
        return {
            "tool": tool,
            "reasoning": data.get("reasoning", f"Smart routing: Pose < {nano_banana_threshold:.2f} -> VTO; Pose >= {nano_banana_threshold:.2f} -> Nano Banana repairs pose and garment"),
            "prompt": data.get("prompt", "Match pose and garment attributes exactly."),
        }
    except Exception:
        fallback_tool = "nano_banana" if (score_val >= nano_banana_threshold and not wrong_garment) else "vto"
        return {
            "tool": fallback_tool,
            "reasoning": f"Default smart routing: Pose < {nano_banana_threshold:.2f} uses VTO; Pose >= {nano_banana_threshold:.2f} uses Nano Banana to repair pose and garment.",

            "prompt": "Keep exact pose. Focus on features from garment image.",
        }







def select_champion_candidate(all_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Selects the FINAL CHAMPION across all iterations:
    1. Highest Pose Similarity Score priority.
    2. If multiple candidates are within a 0.10 limit of the highest Pose Similarity Score,
       select the candidate with the lowest number of Garment Attribute Differences.
    """
    if not all_candidates:
        return {}

    def _get_score(cand):
        s = _parse_similarity_score(cand.get("similarity_score"))
        return s if s is not None else 0.0

    def _get_diff_count(cand):
        attrs = cand.get("attributes", [])
        return len(attrs) if isinstance(attrs, list) else 999

    max_pose = max(_get_score(c) for c in all_candidates)

    eligible = [c for c in all_candidates if _get_score(c) >= max_pose - 0.10]
    eligible.sort(key=lambda c: (_get_diff_count(c), -_get_score(c)))

    return eligible[0]


def _compute_fitness(similarity_score: float, attribute_differences: Any) -> float:
    """
    Computes a composite fitness score prioritizing pose score > 0.90 and minimum Attribute Differences.
    """
    score_val = _parse_similarity_score(similarity_score)
    if score_val is None:
        score_val = 0.0

    num_diffs = (
        len(attribute_differences)
        if isinstance(attribute_differences, list)
        else 1
    )

    pose_pass_bonus = 500.0 if score_val > 0.90 else 0.0
    return pose_pass_bonus - (num_diffs * 100.0) + (score_val * 100.0)


def _format_agent_progress_table(history: List[Dict[str, Any]], goal_met: bool) -> str:
    lines = [
        "### 🤖 Agentic Try-On & Nano Banana Iteration Tracker",
        "| Iter | Model / Tool | Corrective Strategy | Pose Score (>0.90 Goal) | Attribute Diffs (0 Goal) | Status |",
        "| :---: | :--- | :--- | :---: | :---: | :--- |",
    ]
    for row in history:
        iter_num = row["iteration"]
        tool_label = (
            "🍌 Nano Banana (`gemini-2.5-flash-image`)"
            if row["tool"] == "nano_banana"
            else "👗 Virtual Try-On (`virtual-try-on-001`)"
        )
        prompt_short = (
            (row.get("prompt")[:120] + "...")
            if len(row.get("prompt", "")) > 120
            else row.get("prompt", "-")
        )
        score = row["similarity_score"]
        diffs = len(row.get("attribute_differences", []))
        pose_ok = "✅" if (score is not None and score > 0.90) else "⚠️"
        diff_ok = "✅" if diffs == 0 else "⚠️"
        status = (
            "🎯 GOAL MET"
            if (score is not None and score > 0.90 and diffs == 0)
            else f"Improving (Score: {score}, Diffs: {diffs})"
        )
        lines.append(
            f"| **Iter {iter_num}** | {tool_label} | {prompt_short} | `{score}` {pose_ok} | `{diffs}` {diff_ok} | {status} |"
        )

    lines.append("\n#### 💬 Complete Corrective Prompts Used")
    for row in history:
        if row.get("iteration", 0) >= 1 and row.get("prompt"):
            lines.append(f"> **Iter {row['iteration']} ({row['tool'].upper()}):** `{row['prompt']}`")

    if goal_met:
        lines.append(
            "\n> [!TIP]\n> **SUCCESS!** Agentic Loop achieved Pose Comparison Score > 0.90 and Attribute Differences = 0 (none)."
        )
    return "\n".join(lines)


async def run_agentic_try_on_loop(
    person_image=None,
    product_image=None,
    max_iterations: int = 4,
    nano_banana_threshold: float = 0.75,
    online_mode: bool = True,
):
    """
    Autonomous Agentic Try-On Loop:
    Iterates between Virtual Try-On model and Nano Banana model (gemini-2.5-flash-image)
    until Pose Comparison score > 0.90 and Attribute Differences is none (empty []),
    or until max_iterations is reached, yielding progress at each step.
    When online_mode=False and Model 1 / Dress 1 are selected, loads static images from Output folder.
    """
    if person_image is None or product_image is None:
        raise ValueError("Both Person Image and Garment Image are required.")

    if isinstance(person_image, bytes) and isinstance(product_image, bytes):
        person_image_bytes = person_image
        product_image_bytes = product_image
    elif isinstance(person_image, PIL_Image.Image) and isinstance(product_image, PIL_Image.Image):
        person_image_bytes = _pil_to_bytes(person_image)
        product_image_bytes = _pil_to_bytes(product_image)
    elif isinstance(person_image, np.ndarray) and isinstance(product_image, np.ndarray):
        person_image_bytes = person_image.tobytes()
        product_image_bytes = product_image.tobytes()
    else:
        raise TypeError("Unsupported image format.")

    history = []
    gallery_images = []

    # Immediately clear all UI output components when the button is clicked
    yield (
        "### ⚡ 🤖 Autonomous Agentic AI Processing Active...\n> [!NOTE]\n> **Clearing previous outputs and starting Iteration 0...**",
        None,
        None,
        None,
        [],
        [],
        [],
    )

    demo_folder = get_static_demo_pair_id(
        person_bytes=person_image_bytes,
        garment_bytes=product_image_bytes,
    )
    is_offline_demo = bool(demo_folder) and not online_mode

    # Iteration 0: Base Virtual Try-On
    if is_offline_demo:
        await asyncio.sleep(5)
        iter0_vto_bytes = get_static_demo_image_bytes(0, demo_folder)
    else:
        iter0_vto_bytes = call_virtual_try_on(
            person_image_bytes=person_image_bytes,
            product_image_bytes=product_image_bytes,
        )

    (
        iter0_img,
        iter0_similarity,
        iter0_pose_img,
        iter0_attributes,
    ) = await _evaluate_vto_output(
        person_image_bytes,
        product_image_bytes,
        iter0_vto_bytes,
        is_offline_demo=is_offline_demo,
        iter_num=0,
        demo_folder=demo_folder,
    )

    best_candidate = {
        "image_bytes": iter0_vto_bytes,
        "image": iter0_img,
        "similarity_score": iter0_similarity,
        "pose_img": iter0_pose_img,
        "attributes": iter0_attributes,
        "fitness": _compute_fitness(iter0_similarity, iter0_attributes),
    }
    all_candidates = [best_candidate]

    history.append(
        {
            "iteration": 0,
            "tool": "vto",
            "prompt": "Base Virtual Try-On generation",
            "similarity_score": iter0_similarity,
            "attribute_differences": iter0_attributes,
        }
    )
    gallery_images.append((iter0_img, f"Iter 0: VTO Base (Pose: {iter0_similarity})"))
    gallery_metadata = [
        {
            "iteration": 0,
            "tool": "vto",
            "image": iter0_img,
            "similarity_score": iter0_similarity,
            "pose_img": iter0_pose_img,
            "attributes": iter0_attributes,
        }
    ]

    goal_met = (
        iter0_similarity is not None
        and iter0_similarity > 0.90
        and len(iter0_attributes) == 0
    )

    yield (
        _format_agent_progress_table(history, goal_met),
        best_candidate["image"],
        best_candidate["similarity_score"],
        best_candidate["pose_img"],
        best_candidate["attributes"],
        gallery_images,
        gallery_metadata,
    )

    if goal_met:
        return

    current_image_bytes = iter0_vto_bytes
    best_pose_score = iter0_similarity
    retained_pose_prompt = "Keep exact pose."

    # Iterative Agentic Loop
    for iteration in range(1, max_iterations + 1):
        plan = agentic_plan_next_step(
            person_image_bytes=person_image_bytes,
            product_image_bytes=product_image_bytes,
            current_image_bytes=current_image_bytes,
            similarity_score=best_candidate["similarity_score"],
            attribute_differences=best_candidate["attributes"],
            iteration=iteration,
            history=history,
            nano_banana_threshold=nano_banana_threshold,
        )

        chosen_tool = plan["tool"]
        pose_needs_fix = (best_candidate["similarity_score"] is not None and best_candidate["similarity_score"] <= 0.90)
        effective_prompt = craft_effective_recovery_prompt(
            chosen_tool,
            best_candidate["attributes"],
            pose_needs_fix,
            iteration=iteration,
            retained_pose_prompt=retained_pose_prompt,
            person_image_bytes=person_image_bytes,
            product_image_bytes=product_image_bytes,
        )
        prompt_text = effective_prompt if effective_prompt else plan["prompt"]

        if is_offline_demo:
            await asyncio.sleep(5)
            candidate_bytes = get_static_demo_image_bytes(iteration, demo_folder)
            chosen_tool = "nano_banana" if iteration >= 1 else "vto"
            prompt_text = "Applying Corrective actions..."
        elif chosen_tool == "nano_banana":

            try:
                candidate_bytes = call_nano_banana_edit(
                    person_image_bytes=person_image_bytes,
                    product_image_bytes=product_image_bytes,
                    current_image_bytes=current_image_bytes,
                    edit_prompt=prompt_text,
                )
            except Exception as e:
                print(f"Nano Banana edit failed on iter {iteration}: {e}. Fallback to VTO.")
                chosen_tool = "vto"
                candidate_bytes = call_virtual_try_on(
                    person_image_bytes=person_image_bytes,
                    product_image_bytes=product_image_bytes,
                    prompt=prompt_text,
                    person_description=describe_pose_from_landmarks(person_image_bytes),
                )
        else:
            candidate_bytes = call_virtual_try_on(
                person_image_bytes=person_image_bytes,
                product_image_bytes=product_image_bytes,
                prompt=prompt_text,
                person_description=describe_pose_from_landmarks(person_image_bytes),
            )

        (
            cand_img,
            cand_similarity,
            cand_pose_img,
            cand_attributes,
        ) = await _evaluate_vto_output(
            person_image_bytes,
            product_image_bytes,
            candidate_bytes,
            is_offline_demo=is_offline_demo,
            iter_num=iteration,
            demo_folder=demo_folder,
        )

        cand_fitness = _compute_fitness(cand_similarity, cand_attributes)

        # Monotonic Non-Degrading Pose Guarantee:
        # If candidate pose improved or stayed equal, retain pose prompt clause and advance image base
        if cand_similarity is not None and (best_pose_score is None or cand_similarity >= best_pose_score):
            best_pose_score = cand_similarity
            retained_pose_prompt = "Keep exact pose."
            current_image_bytes = candidate_bytes
        else:
            # If candidate degraded pose score, reject degrading input base and keep best candidate image
            current_image_bytes = best_candidate["image_bytes"]


        current_cand = {
            "image_bytes": candidate_bytes,
            "image": cand_img,
            "similarity_score": cand_similarity,
            "pose_img": cand_pose_img,
            "attributes": cand_attributes,
            "fitness": cand_fitness,
        }
        all_candidates.append(current_cand)
        best_candidate = max(all_candidates, key=_candidate_rank_key)

        history.append(
            {
                "iteration": iteration,
                "tool": chosen_tool,
                "prompt": prompt_text,
                "similarity_score": cand_similarity,
                "attribute_differences": cand_attributes,
            }
        )
        gallery_images.append(
            (
                cand_img,
                f"Iter {iteration}: {'Nano Banana' if chosen_tool == 'nano_banana' else 'VTO'} (Pose: {cand_similarity}, Diffs: {len(cand_attributes)})",
            )
        )
        gallery_metadata.append(
            {
                "iteration": iteration,
                "tool": chosen_tool,
                "image": cand_img,
                "similarity_score": cand_similarity,
                "pose_img": cand_pose_img,
                "attributes": cand_attributes,
            }
        )

        goal_met = (
            best_candidate["similarity_score"] is not None
            and best_candidate["similarity_score"] > 0.90
            and len(best_candidate["attributes"]) == 0
        )

        yield (
            _format_agent_progress_table(history, goal_met),
            cand_img,
            cand_similarity,
            cand_pose_img,
            cand_attributes,
            gallery_images,
            gallery_metadata,
        )

        if goal_met:
            break

    # Final Step: Always yield the overall Champion Output (highest pose score & lowest attribute difference across all iterations)
    yield (
        _format_agent_progress_table(history, True)
        + "\n\n### 🏆 Champion Output Selected\n> [!TIP]\n> **Displaying the final output with the highest Pose Comparison Score and lowest Attribute Differences from all completed iterations.**",
        best_candidate["image"],
        best_candidate["similarity_score"],
        best_candidate["pose_img"],
        best_candidate["attributes"],
        gallery_images,
        gallery_metadata,
    )

