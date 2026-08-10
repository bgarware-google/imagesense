# pose_estimator.py

from typing import Dict, Any
from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2

import urllib.request
import ssl
try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = ssl.create_default_context()

model_asset_path = Path(__file__).parent.parent / "assets/models/pose_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
_pose_detector = None


def _ensure_model_exists():
    """Downloads pose_landmarker.task if it does not already exist."""
    if not model_asset_path.exists():
        model_asset_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading pose_landmarker.task from {MODEL_URL}...")
        with urllib.request.urlopen(MODEL_URL, context=_SSL_CONTEXT) as response, open(model_asset_path, "wb") as out_file:
            out_file.write(response.read())
        print(f"Successfully downloaded pose_landmarker.task to {model_asset_path}")


def _get_pose_detector():
    """Initializes and returns the MediaPipe PoseLandmarker."""
    global _pose_detector
    if _pose_detector is None:
        try:
            _ensure_model_exists()
            base_options = python.BaseOptions(model_asset_path=str(model_asset_path))
            options = vision.PoseLandmarkerOptions(base_options=base_options, output_segmentation_masks=True)
            _pose_detector = vision.PoseLandmarker.create_from_options(options)
        except Exception as e:
            print(f"Error initializing PoseLandmarker: {e}. Ensure 'pose_landmarker.task' is available.")
            _pose_detector = None
    return _pose_detector


def _draw_landmarks_on_image(rgb_image: np.ndarray, detection_result) -> np.ndarray:
    pose_landmarks_list = detection_result.pose_landmarks
    annotated_image = np.copy(rgb_image)

    # Loop through the detected poses to visualize.
    for idx in range(len(pose_landmarks_list)):
        pose_landmarks = pose_landmarks_list[idx]

        # Draw the pose landmarks.
        pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        pose_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in pose_landmarks
        ])
        mp.solutions.drawing_utils.draw_landmarks(
            annotated_image,
            pose_landmarks_proto,
            mp.solutions.pose.POSE_CONNECTIONS,
            mp.solutions.drawing_styles.get_default_pose_landmarks_style())
    return annotated_image


def _normalize_pose_landmarks(landmarks):
    """Normalizes landmarks to be scale and translation invariant."""
    if not landmarks:
        return np.array([])

    # Move the origin to the center of the hips.
    left_hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_HIP.value]
    hip_center = np.array([
        (left_hip.x + right_hip.x) * 0.5,
        (left_hip.y + right_hip.y) * 0.5,
    ])

    # Calculate the torso size to normalize the scale.
    left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value]
    shoulder_center = np.array([
        (left_shoulder.x + right_shoulder.x) * 0.5,
        (left_shoulder.y + right_shoulder.y) * 0.5,
    ])

    torso_size = np.linalg.norm(shoulder_center - hip_center)
    if torso_size == 0:
        torso_size = 1e-6  # Avoid division by zero

    # Normalize by translating and scaling.
    normalized_landmarks = []
    for lm in landmarks:
        # We only use x and y for 2D comparison.
        normalized_point = (np.array([lm.x, lm.y]) - hip_center) / torso_size
        normalized_landmarks.append(normalized_point)

    return np.array(normalized_landmarks)


def _calculate_pose_similarity(landmarks1, landmarks2):
    """
    Calculates a similarity score between two poses based on normalized landmark distances.

    The function normalizes each pose to be scale and translation invariant, then
    computes the mean Euclidean distance between corresponding landmarks. This distance
    is converted to a similarity score.
    """
    if not landmarks1 or not landmarks2:
        return 0.0

    # Normalize both sets of landmarks
    norm_landmarks1 = _normalize_pose_landmarks(landmarks1)
    norm_landmarks2 = _normalize_pose_landmarks(landmarks2)

    if norm_landmarks1.shape != norm_landmarks2.shape:
        return 0.0  # Mismatch in number of landmarks or dimensions

    # Calculate the average Euclidean distance between corresponding landmarks
    distance = np.mean(np.linalg.norm(norm_landmarks1 - norm_landmarks2, axis=1))

    # Convert distance to a similarity score (0 to 1).
    similarity = np.exp(-2.0 * distance)  # Scaling factor 2.0 can be tuned

    return similarity


def _bytes_to_mp_image(image_bytes: bytes) -> mp.Image:
    """Converts image bytes to a MediaPipe Image."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError("cv2.imdecode() failed: invalid image bytes")
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)


def _combine_pose_side_by_side(img1: np.ndarray, img2: np.ndarray) -> bytes:
    """
    Combines two RGB images side-by-side and returns PNG-encoded image bytes.
    """
    # Ensure both images have same height
    if img1.shape[0] != img2.shape[0]:
        height = min(img1.shape[0], img2.shape[0])
        img1 = cv2.resize(img1, (int(img1.shape[1] * height / img1.shape[0]), height))
        img2 = cv2.resize(img2, (int(img2.shape[1] * height / img2.shape[0]), height))

    # Concatenate side by side
    combined = np.concatenate((img1, img2), axis=1)  # horizontal

    # Encode to PNG bytes
    success, encoded = cv2.imencode('.png', cv2.cvtColor(combined, cv2.COLOR_RGB2BGR))
    if not success:
        raise ValueError("Failed to encode combined image to PNG bytes")

    return encoded.tobytes()


async def compare_poses(
        img1_bytes: bytes,
        img2_bytes: bytes
) -> (float, bytes):
    """
    Compare poses between two uploaded images
    """

    detector = _get_pose_detector()
    if detector is None:
        raise RuntimeError("Pose detection model not initialized. Ensure 'pose_landmarker.task' is available.")

    try:
        # Load bytes into mediapipe image
        image1 = _bytes_to_mp_image(img1_bytes)
        image2 = _bytes_to_mp_image(img2_bytes)

        # Perform pose detection
        detection_result1 = detector.detect(image1)
        detection_result2 = detector.detect(image2)

        # Draw landmarks on image
        annotated_image1 = _draw_landmarks_on_image(image1.numpy_view(), detection_result1)
        annotated_image2 = _draw_landmarks_on_image(image2.numpy_view(), detection_result2)

        image_bytes = _combine_pose_side_by_side(annotated_image1, annotated_image2)

        # For simplicity, compare the first detected pose in each image.
        landmarks1 = detection_result1.pose_landmarks[0] if detection_result1.pose_landmarks else None
        landmarks2 = detection_result2.pose_landmarks[0] if detection_result2.pose_landmarks else None

        similarity_score = _calculate_pose_similarity(landmarks1, landmarks2)

        return similarity_score, image_bytes

    except Exception as e:
        print(f"Error processing images for pose detection: {e}")
        raise


def describe_pose_from_landmarks(image_bytes: bytes) -> str:
    """
    Extracts geometric body posture and stance descriptions in text from MediaPipe PoseLandmarker landmarks.
    Returns a natural language summary of body orientation, arms position, and stance.
    """
    detector = _get_pose_detector()
    if detector is None:
        return "standing upright facing forward with arms relaxed at sides"
    try:
        mp_image = _bytes_to_mp_image(image_bytes)
        detection = detector.detect(mp_image)
        if not detection.pose_landmarks or len(detection.pose_landmarks) == 0:
            return "standing upright facing forward with arms relaxed at sides"

        lms = detection.pose_landmarks[0]
        PL = mp.solutions.pose.PoseLandmark

        ls = lms[PL.LEFT_SHOULDER.value]
        rs = lms[PL.RIGHT_SHOULDER.value]
        lh = lms[PL.LEFT_HIP.value]
        rh = lms[PL.RIGHT_HIP.value]
        lw = lms[PL.LEFT_WRIST.value]
        rw = lms[PL.RIGHT_WRIST.value]

        # Orientation check
        shoulder_span = abs(ls.x - rs.x)
        z_diff = ls.z - rs.z
        if abs(z_diff) > 0.18 or shoulder_span < 0.12:
            orientation = "angled sideways/quarter-turn"
        else:
            orientation = "facing directly forward"

        # Arm descriptions
        arm_descs = []
        if lw.y < ls.y:
            arm_descs.append("left arm raised above shoulder")
        elif lw.y < lh.y - 0.05:
            arm_descs.append("left arm bent with hand near waist/torso")
        else:
            arm_descs.append("left arm resting straight down")

        if rw.y < rs.y:
            arm_descs.append("right arm raised above shoulder")
        elif rw.y < rh.y - 0.05:
            arm_descs.append("right arm bent with hand near waist/torso")
        else:
            arm_descs.append("right arm resting straight down")

        arms_str = " and ".join(arm_descs)
        return f"standing upright {orientation}, with {arms_str}"
    except Exception as e:
        print(f"Failed to describe pose from landmarks: {e}")
        return "standing upright facing forward with arms relaxed at sides"
