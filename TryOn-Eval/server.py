# server.py — Google Cloud Creative Studio Web Application Backend
import base64
import io
import json
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from vto.agentic_vto import (
    call_virtual_try_on,
    _evaluate_vto_output,
    agentic_plan_next_step,
    call_nano_banana_edit,
    craft_effective_recovery_prompt,
    _compute_fitness,
    is_static_demo_pair,
    get_static_demo_pair_id,
    get_static_demo_image_bytes,
    select_champion_candidate,
)
from vto.pose_estimator import describe_pose_from_landmarks




app = FastAPI(
    title="Google Cloud Creative Studio — Agentic Virtual Try-On",
    description="Stunning Web Application for Autonomous Agentic Virtual Try-On & Evaluation",
)

@app.get("/api/v1/health")
@app.get("/livez")
@app.get("/readyz")
async def health_check():
    """Liveness & Readiness probe for Google Cloud Run and GKE."""
    return {
        "status": "HEALTHY",
        "service": "tryon-eval",
        "version": "1.0.0",
        "model": "gemini-2.5-flash"
    }

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "webapp" / "static"
ASSETS_DIR = BASE_DIR / "assets"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


from PIL import Image as PIL_Image


def _bytes_to_base64_url(image_data, mime_type: str = "image/png") -> str:
    if image_data is None:
        return ""
    if isinstance(image_data, PIL_Image.Image):
        buf = io.BytesIO()
        image_data.save(buf, format="PNG")
        raw_bytes = buf.getvalue()
    elif isinstance(image_data, bytes):
        raw_bytes = image_data
    else:
        return ""
    b64 = base64.b64encode(raw_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"



@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_html = STATIC_DIR / "index.html"
    return HTMLResponse(content=index_html.read_text(), status_code=200)


@app.get("/api/samples")
async def list_sample_images():
    person_dir = ASSETS_DIR / "sample_images" / "person"
    garment_dir = ASSETS_DIR / "sample_images" / "garments"

    person_samples = [
        f"/assets/sample_images/person/{f.name}"
        for f in sorted(person_dir.glob("*"))
        if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
    ]
    garment_samples = [
        f"/assets/sample_images/garments/{f.name}"
        for f in sorted(garment_dir.glob("*"))
        if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
    ]
    return JSONResponse({"person": person_samples, "garments": garment_samples})


async def _stream_agentic_loop(
    person_bytes: bytes,
    garment_bytes: bytes,
    max_iterations: int,
    is_demo: bool = False,
    demo_folder: str = "",
    nano_banana_threshold: float = 0.75,
) -> AsyncGenerator[str, None]:
    history = []

    # Iteration 0: Base Virtual Try-On
    if is_demo:
        await asyncio.sleep(5)
        iter0_vto_bytes = get_static_demo_image_bytes(0, demo_folder)
    else:
        iter0_vto_bytes = call_virtual_try_on(
            person_image_bytes=person_bytes,
            product_image_bytes=garment_bytes,
        )

    (
        iter0_img,
        iter0_similarity,
        iter0_pose_img,
        iter0_attributes,
    ) = await _evaluate_vto_output(
        person_bytes,
        garment_bytes,
        iter0_vto_bytes,
        is_offline_demo=is_demo,
        iter_num=0,
        demo_folder=demo_folder,
    )

    goal_met = (
        iter0_similarity is not None
        and iter0_similarity > 0.90
        and len(iter0_attributes) == 0
    )

    history.append(
        {
            "iteration": 0,
            "tool": "vto",
            "prompt": "Base Virtual Try-On generation",
            "similarity_score": iter0_similarity,
            "attribute_differences": iter0_attributes,
        }
    )

    payload = {
        "iteration": 0,
        "tool": "vto",
        "prompt": "Base Virtual Try-On generation",
        "image_url": _bytes_to_base64_url(iter0_vto_bytes),
        "similarity_score": iter0_similarity,
        "pose_image_url": _bytes_to_base64_url(iter0_pose_img) if iter0_pose_img else "",
        "attributes": iter0_attributes,
        "goal_met": goal_met,
    }
    yield f"data: {json.dumps(payload)}\n\n"

    if goal_met:
        return

    current_image_bytes = iter0_vto_bytes
    best_candidate = {
        "image_bytes": iter0_vto_bytes,
        "similarity_score": iter0_similarity,
        "pose_img": iter0_pose_img,
        "attributes": iter0_attributes,
        "fitness": _compute_fitness(iter0_similarity, iter0_attributes),
    }
    all_candidates = [best_candidate]

    best_pose_score = iter0_similarity
    retained_pose_prompt = "Keep exact pose."

    # Agentic Loop
    for iter_num in range(1, max_iterations + 1):
        if is_demo:
            await asyncio.sleep(5)
            chosen_tool = "nano_banana" if iter_num >= 1 else "vto"
            prompt_text = "Applying Corrective actions..."
            candidate_bytes = get_static_demo_image_bytes(iter_num, demo_folder)
        else:
            plan = agentic_plan_next_step(
                person_image_bytes=person_bytes,
                product_image_bytes=garment_bytes,
                current_image_bytes=current_image_bytes,
                similarity_score=best_candidate["similarity_score"],
                attribute_differences=best_candidate["attributes"],
                iteration=iter_num,
                history=history,
                nano_banana_threshold=nano_banana_threshold,
            )

            chosen_tool = plan["tool"]
            pose_needs_fix = (
                best_candidate["similarity_score"] is not None
                and best_candidate["similarity_score"] <= 0.90
            )
            effective_prompt = craft_effective_recovery_prompt(
                chosen_tool,
                best_candidate["attributes"],
                pose_needs_fix,
                iteration=iter_num,
                retained_pose_prompt=retained_pose_prompt,
                person_image_bytes=person_bytes,
                product_image_bytes=garment_bytes,
            )

            prompt_text = effective_prompt if effective_prompt else plan["prompt"]

            if chosen_tool == "nano_banana":
                try:
                    candidate_bytes = call_nano_banana_edit(
                        person_image_bytes=person_bytes,
                        product_image_bytes=garment_bytes,
                        current_image_bytes=current_image_bytes,
                        edit_prompt=prompt_text,
                    )
                except Exception as e:
                    print(f"Nano Banana edit failed on iter {iter_num}: {e}. Fallback to VTO.")
                    chosen_tool = "vto"
                    candidate_bytes = call_virtual_try_on(
                        person_image_bytes=person_bytes,
                        product_image_bytes=garment_bytes,
                        prompt=prompt_text,
                        person_description=describe_pose_from_landmarks(person_bytes),
                    )
            else:
                candidate_bytes = call_virtual_try_on(
                    person_image_bytes=person_bytes,
                    product_image_bytes=garment_bytes,
                    prompt=prompt_text,
                    person_description=describe_pose_from_landmarks(person_bytes),
                )

        (
            cand_img,
            cand_similarity,
            cand_pose_img,
            cand_attributes,
        ) = await _evaluate_vto_output(
            person_bytes,
            garment_bytes,
            candidate_bytes,
            is_offline_demo=is_demo,
            iter_num=iter_num,
            demo_folder=demo_folder,
        )

        cand_fitness = _compute_fitness(cand_similarity, cand_attributes)
        current_cand = {
            "image_bytes": candidate_bytes,
            "similarity_score": cand_similarity,
            "pose_img": cand_pose_img,
            "attributes": cand_attributes,
            "fitness": cand_fitness,
        }
        all_candidates.append(current_cand)

        if cand_fitness > best_candidate["fitness"]:
            best_candidate = current_cand
            best_pose_score = cand_similarity
            retained_pose_prompt = "Keep exact pose."
            current_image_bytes = candidate_bytes

        history.append(
            {
                "iteration": iter_num,
                "tool": chosen_tool,
                "prompt": prompt_text,
                "similarity_score": cand_similarity,
                "attribute_differences": cand_attributes,
            }
        )

        goal_met = (
            cand_similarity is not None
            and cand_similarity > 0.90
            and len(cand_attributes) == 0
        )

        payload = {
            "iteration": iter_num,
            "tool": chosen_tool,
            "prompt": prompt_text,
            "image_url": _bytes_to_base64_url(candidate_bytes),
            "similarity_score": cand_similarity,
            "pose_image_url": _bytes_to_base64_url(cand_pose_img) if cand_pose_img else "",
            "attributes": cand_attributes,
            "goal_met": goal_met,
        }
        yield f"data: {json.dumps(payload)}\n\n"

        if goal_met:
            break

    # Yield Overall Champion Output (highest pose score within 0.10 band & lowest attribute difference across all iterations)
    champion = select_champion_candidate(all_candidates)
    champion_payload = {
        "iteration": "FINAL CHAMPION",
        "tool": "best_selection",
        "prompt": "Overall Champion Output selected with highest pose similarity and lowest attribute differences within 0.10 pose limit.",
        "image_url": _bytes_to_base64_url(champion["image_bytes"]),
        "similarity_score": champion["similarity_score"],
        "pose_image_url": _bytes_to_base64_url(champion["pose_img"]) if champion.get("pose_img") else "",
        "attributes": champion["attributes"],
        "goal_met": True,
        "is_champion": True,
    }
    yield f"data: {json.dumps(champion_payload)}\n\n"



@app.post("/api/agentic-vto-stream")
async def start_agentic_vto_stream(
    person_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    max_iterations: int = Form(4),
    nano_banana_threshold: float = Form(0.75),
    online_mode: str = Form("true"),
):
    person_bytes = await person_image.read()
    garment_bytes = await garment_image.read()
    is_online = str(online_mode).lower() in ("true", "1", "yes", "on")
    demo_folder = get_static_demo_pair_id(
        person_image.filename or "",
        garment_image.filename or "",
        person_bytes,
        garment_bytes,
        force_offline=not is_online,
    )

    return StreamingResponse(
        _stream_agentic_loop(
            person_bytes,
            garment_bytes,
            max_iterations,
            is_demo=bool(demo_folder) and not is_online,
            demo_folder=demo_folder,
            nano_banana_threshold=nano_banana_threshold,
        ),
        media_type="text/event-stream",
    )


import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
