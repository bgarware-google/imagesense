
# virtual_try_on.py
import io
import json
import numpy as np
from google import genai
from PIL import Image as PIL_Image
from google.genai.types import (
    Image,
    ProductImage,
    RecontextImageConfig,
    RecontextImageSource,
)

from utils import CONFIG
from vto.pose_estimator import compare_poses, describe_pose_from_landmarks
from vto.garment_diff_analyzer import compare_apparel_attributes


def _pil_to_bytes(image: PIL_Image.Image, format: str = "PNG") -> bytes:
    """
    Converts a PIL Image object to a bytes object in the specified format.
    """
    if not isinstance(image, PIL_Image.Image):
        raise TypeError("Input must be a PIL Image object.")

    byte_arr = io.BytesIO()
    image.save(byte_arr, format=format)
    return byte_arr.getvalue()


def _display_image_from_bytes(image_bytes):
    """
    Gets image bytes, converts them to a PIL Image,
    and returns it for display in Gradio.
    """
    if not image_bytes:
        return None
    try:
        return PIL_Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        print(f"Error converting bytes to image: {e}")
        return None


def call_virtual_try_on(
        person_image_bytes=None,
        product_image_bytes=None,
        prompt=None,
        person_description=None,
):
    source_kwargs = {
        "person_image": Image(image_bytes=person_image_bytes),
        "product_images": [
            ProductImage(product_image=Image(image_bytes=product_image_bytes))
        ],
    }
    if prompt:
        source_kwargs["prompt"] = prompt

    VTO_ENVIRONMENT = "autopush"
    VTO_PROJECT_ID = "cloud-lvm-training-nonprod"
    VTO_LOCATION = "us-central1"

    if VTO_ENVIRONMENT == "preprod":
        if VTO_LOCATION != "us-central1":
            raise ValueError("The preprod environment is only available in location us-central1.")
        api_regional_endpoint = f"{VTO_LOCATION}-preprod-aiplatform.googleapis.com"
    elif VTO_ENVIRONMENT == "autopush":
        if VTO_LOCATION != "us-central1":
            raise ValueError("The autopush environment is only available in location us-central1.")
        api_regional_endpoint = f"{VTO_LOCATION}-autopush-aiplatform.sandbox.googleapis.com"
    else:
        api_regional_endpoint = f"{VTO_LOCATION}-aiplatform.googleapis.com"

    client = genai.Client(
        vertexai=True,
        project=VTO_PROJECT_ID,
        location=VTO_LOCATION,
        http_options={"base_url": f"https://{api_regional_endpoint}"},
    )
    response = client.models.recontext_image(
        model=CONFIG["vto"]["model_name"],
        source=RecontextImageSource(**source_kwargs),
        config=RecontextImageConfig(
            seed=None,
            base_steps=CONFIG["vto"]["base_steps"],
            number_of_images=CONFIG["vto"]["number_of_images"],
            output_mime_type=CONFIG["vto"]["output_mime_type"],
            safety_filter_level=CONFIG["vto"]["safety_filter_level"],
            person_generation=CONFIG["vto"]["person_generation"],
            enhance_prompt=True
        ),
    )
    # todo: check capability to add multiple product_images on single person

    return response.generated_images[0].image.image_bytes



async def _evaluate_vto_output(person_image_bytes: bytes, product_image_bytes: bytes, vto_image_bytes: bytes, is_offline_demo: bool = False, iter_num: int = 0, demo_folder: str = ""):
    similarity_score, pose_comparison_bytes = await compare_poses(
        img1_bytes=person_image_bytes,
        img2_bytes=vto_image_bytes
    )

    if is_offline_demo:
        if demo_folder == "Model2_Dress2":
            offline_attrs = {
                0: [{"attribute": "sleeve", "difference": "Product image shows full sleeve on left hand, but generated image shows sleeveless dress "}],
                1: [],
                2: [],
                3: [],
                4: [],
            }
        else:
            offline_attrs = {
                0: [{"attribute": "Handbag", "difference": "Product image shows a white handbag"}],
                1: [{"attribute": "Handbag", "difference": "Product image shows a white handbag"}],
                2: [{"attribute": "Handbag", "difference": "Product image shows a white handbag"}],
                3: [{"attribute": "Dress Length", "difference": "Produt image shows dress lenght is more"}],
                4: [],
            }
        attrs = offline_attrs.get(iter_num, [])
        return (
            _display_image_from_bytes(vto_image_bytes),
            round(float(similarity_score), 2),
            _display_image_from_bytes(pose_comparison_bytes),
            attrs,
        )

    apparel_attributes_result = compare_apparel_attributes(
        img1_bytes=product_image_bytes,
        img2_bytes=person_image_bytes,
        img3_bytes=vto_image_bytes
    )
    attribute_comparison_json = apparel_attributes_result["details"]

    return (
        _display_image_from_bytes(vto_image_bytes),
        round(float(similarity_score), 2),
        _display_image_from_bytes(pose_comparison_bytes),
        attribute_comparison_json,
    )


async def perform_vto_with_eval(person_image=None, product_image=None):
    """
    Perform VTO, pose comparison and attribute analysis of 2 images. Saves output image as artifact.
    """
    # Check image bytes
    if isinstance(person_image, bytes) and isinstance(product_image, bytes):
        person_image_bytes = person_image
        product_image_bytes = product_image
    elif isinstance(person_image, np.ndarray) and isinstance(product_image, np.ndarray):
        person_image_bytes = person_image.tobytes()
        product_image_bytes = product_image.tobytes()
    elif isinstance(person_image, PIL_Image.Image) and isinstance(product_image, PIL_Image.Image):
        person_image_bytes = _pil_to_bytes(person_image)
        product_image_bytes = _pil_to_bytes(product_image)
    else:
        raise ValueError("Both person_image and product_image must be bytes, pil image or numpy arrays.")

    # Perform VTO
    vto_image_bytes = call_virtual_try_on(
        person_image_bytes=person_image_bytes,
        product_image_bytes=product_image_bytes
    )

    return await _evaluate_vto_output(person_image_bytes, product_image_bytes, vto_image_bytes)


def _parse_similarity_score(similarity_score) -> float:
    if similarity_score is None:
        return None
    if isinstance(similarity_score, dict):
        val = similarity_score.get('label')
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
    try:
        return float(similarity_score)
    except (ValueError, TypeError):
        return None

