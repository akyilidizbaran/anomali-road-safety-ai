#!/usr/bin/env python3
"""Benchmark driver upper-body pose models using the selected YuNet face anchor."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch

try:
    from driver_pose_utils import (
        associate_driver_pose,
        driver_arm_focus_roi_bbox,
        driver_face_global_bbox,
        hand_anchor_summary,
        intersect_bbox,
        pose_inference_gate,
        TemporalKeypointStabilizer,
        temporal_pose_summary,
        torso_from_keypoints,
        upper_body_cabin_roi_bbox,
        upper_body_roi_bbox,
        xyxy_to_local,
    )
except ImportError:
    from scripts.benchmarks.driver_pose_utils import (
        associate_driver_pose,
        driver_arm_focus_roi_bbox,
        driver_face_global_bbox,
        hand_anchor_summary,
        intersect_bbox,
        pose_inference_gate,
        TemporalKeypointStabilizer,
        temporal_pose_summary,
        torso_from_keypoints,
        upper_body_cabin_roi_bbox,
        upper_body_roi_bbox,
        xyxy_to_local,
    )


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CABIN_SUMMARY = (
    ROOT
    / "models"
    / "benchmarks"
    / "artifacts"
    / "CABIN-EXP-004-opencv_yunet_2026may-summary.json"
)
DEFAULT_YOLO_POSE_MODEL = ROOT / "yolo11n-pose.pt"
DEFAULT_MEDIAPIPE_POSE_MODEL = (
    ROOT
    / "models"
    / "checkpoints"
    / "cabin"
    / "pose_landmarker_full.task"
)
DEFAULT_RTMPOSE_MODEL = (
    ROOT
    / "models"
    / "checkpoints"
    / "cabin"
    / "rtmpose-l_simcc-body7_384x288.onnx"
)
DEFAULT_RTMW_MODEL = (
    ROOT
    / "models"
    / "checkpoints"
    / "cabin"
    / "rtmw-l_simcc-cocktail14_384x288.onnx"
)
DEFAULT_VITPOSE_MODEL = "usyd-community/vitpose-base-simple"
DEFAULT_ARTIFACT_DIR = ROOT / "models" / "benchmarks" / "artifacts"
DEFAULT_REPORT_DIR = ROOT / "testing" / "reports"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "cabin_pose"
DEFAULT_VIDEOS_DIR = ROOT / "Test"

EXPERIMENTS = {
    "POSE-EXP-001": {
        "model_key": "yolo11n_pose_coco17",
        "backend": "ultralytics",
        "model_path": DEFAULT_YOLO_POSE_MODEL,
        "decision": "primary_multi_person_upper_body_baseline",
        "keypoint_confidence": 0.35,
        "hand_keypoint_confidence": 0.30,
        "max_hand_face_distance": 3.0,
    },
    "POSE-EXP-011": {
        "model_key": "yolo11n_pose_arm_focus_coco17",
        "backend": "ultralytics",
        "model_path": DEFAULT_YOLO_POSE_MODEL,
        "decision": "yolo11n_pose_arm_focus_challenger",
        "keypoint_confidence": 0.25,
        "hand_keypoint_confidence": 0.25,
        "max_hand_face_distance": 3.2,
        "roi_policy": "driver_arm_focus",
        "run_on_poor_face_confidence": 0.80,
        "render_policy": "full_pose",
        "enable_arm_anchors": True,
    },
    "POSE-EXP-002": {
        "model_key": "mediapipe_pose_landmarker_full",
        "backend": "mediapipe",
        "model_path": DEFAULT_MEDIAPIPE_POSE_MODEL,
        "decision": "dense_33_landmark_challenger",
        "keypoint_confidence": 0.35,
        "hand_keypoint_confidence": 0.30,
        "max_hand_face_distance": 3.0,
    },
    "POSE-EXP-003": {
        "model_key": "rtmpose_l_body7_384x288_onnx",
        "backend": "rtmpose_onnx",
        "model_path": DEFAULT_RTMPOSE_MODEL,
        "decision": "partial_occlusion_topdown_challenger",
        "keypoint_confidence": 0.35,
        "hand_keypoint_confidence": 0.30,
        "max_hand_face_distance": 3.0,
    },
    "POSE-EXP-004": {
        "model_key": "rtmw_l_cocktail14_wholebody_384x288_onnx",
        "backend": "rtmpose_onnx",
        "model_path": DEFAULT_RTMW_MODEL,
        "decision": "wholebody_upperbody_hand_challenger",
        # RTMW exports raw SimCC peak scores. Body and hand heads use
        # different score scales, so they require model-specific thresholds.
        "keypoint_confidence": 1.5,
        "hand_keypoint_confidence": 4.5,
        "max_hand_face_distance": 1.6,
    },
    "POSE-EXP-005": {
        "model_key": "vitpose_b_simple_coco17_hf",
        "backend": "vitpose_hf",
        "model_path": DEFAULT_VITPOSE_MODEL,
        "decision": "occlusion_robust_transformer_upperbody_challenger",
        "keypoint_confidence": 0.30,
        "hand_keypoint_confidence": 1.0,
        "max_hand_face_distance": 0.0,
        "roi_policy": "cabin_clamped_face_anchor",
    },
    "POSE-EXP-006": {
        "model_key": "vitpose_b_temporal_stabilized_v1",
        "backend": "vitpose_hf",
        "model_path": DEFAULT_VITPOSE_MODEL,
        "decision": "temporal_upperbody_torso_baseline_candidate",
        "keypoint_confidence": 0.30,
        "hand_keypoint_confidence": 1.0,
        "max_hand_face_distance": 0.0,
        "roi_policy": "cabin_clamped_face_anchor",
        "temporal_stabilization": True,
        "temporal_hold_ms": 200,
        "temporal_smoothing_alpha": 0.55,
        "temporal_max_jump_face_units": 1.25,
    },
    "POSE-EXP-007": {
        "model_key": "vitpose_b_temporal_hysteresis_v2",
        "backend": "vitpose_hf",
        "model_path": DEFAULT_VITPOSE_MODEL,
        "decision": "upperbody_arm_continuity_baseline_candidate",
        "keypoint_confidence": 0.30,
        "hand_keypoint_confidence": 1.0,
        "max_hand_face_distance": 0.0,
        "roi_policy": "cabin_clamped_face_anchor",
        "temporal_stabilization": True,
        "temporal_hold_ms": 200,
        "temporal_smoothing_alpha": 0.55,
        "temporal_max_jump_face_units": 1.25,
        "temporal_continuation_confidence": 0.10,
        "temporal_max_continuation_ms": 500,
        "temporal_continuation_max_jump_face_units": 0.45,
    },
    "POSE-EXP-008": {
        "model_key": "vitpose_b_visibility_decoupled_v3",
        "backend": "vitpose_hf",
        "model_path": DEFAULT_VITPOSE_MODEL,
        "decision": "upperbody_continuity_with_evidence_only_poor_frames",
        "keypoint_confidence": 0.30,
        "hand_keypoint_confidence": 1.0,
        "max_hand_face_distance": 0.0,
        "roi_policy": "cabin_clamped_face_anchor",
        "temporal_stabilization": True,
        "temporal_hold_ms": 200,
        "temporal_smoothing_alpha": 0.55,
        "temporal_max_jump_face_units": 1.25,
        "temporal_continuation_confidence": 0.10,
        "temporal_max_continuation_ms": 500,
        "temporal_continuation_max_jump_face_units": 0.45,
        "run_on_poor_face_confidence": 0.80,
    },
    "POSE-EXP-009": {
        "model_key": "vitpose_b_final_torso_baseline_v1",
        "backend": "vitpose_hf",
        "model_path": DEFAULT_VITPOSE_MODEL,
        "decision": "selected_upperbody_torso_baseline",
        "keypoint_confidence": 0.30,
        "hand_keypoint_confidence": 1.0,
        "max_hand_face_distance": 0.0,
        "roi_policy": "cabin_clamped_face_anchor",
        "temporal_stabilization": True,
        "temporal_hold_ms": 200,
        "temporal_smoothing_alpha": 0.55,
        "temporal_max_jump_face_units": 1.25,
        "run_on_poor_face_confidence": 0.80,
        "render_policy": "torso_only",
        "enable_arm_anchors": False,
    },
    "POSE-EXP-010": {
        "model_key": "vitpose_b_arm_focus_observations_v1",
        "backend": "vitpose_hf",
        "model_path": DEFAULT_VITPOSE_MODEL,
        "decision": "arm_state_observation_source",
        "keypoint_confidence": 0.22,
        "hand_keypoint_confidence": 1.0,
        "max_hand_face_distance": 0.0,
        "roi_policy": "driver_arm_focus",
        "run_on_poor_face_confidence": 0.80,
        "render_policy": "full_pose",
        "enable_arm_anchors": True,
    },
}

COCO_NAMES = [
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]
MEDIAPIPE_NAMES = {
    0: "nose",
    2: "left_eye",
    5: "right_eye",
    7: "left_ear",
    8: "right_ear",
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
}
WHOLEBODY_NAMES = (
    COCO_NAMES
    + [f"foot_{index}" for index in range(6)]
    + [f"face_{index}" for index in range(68)]
    + [f"left_hand_{index}" for index in range(21)]
    + [f"right_hand_{index}" for index in range(21)]
)
SKELETON = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
]


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(sum(values) / len(values)), 3)


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * 0.95))
    return round(float(ordered[index]), 3)


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class UltralyticsPoseDetector:
    def __init__(self, model_path: Path, confidence: float, device: str, imgsz: int):
        from ultralytics import YOLO

        self.model = YOLO(str(model_path))
        self.confidence = confidence
        self.device = device
        self.imgsz = imgsz

    def close(self) -> None:
        return None

    def detect(self, image_bgr: np.ndarray, timestamp_ms: int) -> list[dict[str, Any]]:
        del timestamp_ms
        result = self.model.predict(
            image_bgr,
            conf=self.confidence,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )[0]
        if result.boxes is None or result.keypoints is None:
            return []
        boxes = result.boxes.xyxy.cpu().tolist()
        box_confidences = result.boxes.conf.cpu().tolist()
        keypoint_data = result.keypoints.data.cpu().tolist()
        poses = []
        for bbox, box_confidence, points in zip(
            boxes, box_confidences, keypoint_data
        ):
            keypoints = {}
            for name, point in zip(COCO_NAMES, points):
                confidence = float(point[2]) if len(point) > 2 else 1.0
                keypoints[name] = {
                    "x": round(float(point[0]), 2),
                    "y": round(float(point[1]), 2),
                    "confidence": round(confidence, 4),
                }
            poses.append(
                {
                    "bbox": [round(float(value), 2) for value in bbox],
                    "confidence": round(float(box_confidence), 4),
                    "keypoints": keypoints,
                }
            )
        return poses


class MediaPipePoseDetector:
    def __init__(
        self,
        model_path: Path,
        confidence: float,
        device: str,
        imgsz: int,
    ):
        del device, imgsz
        import mediapipe as mp

        self.mp = mp
        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            # The face-anchored crop moves and changes size every frame. VIDEO
            # tracking assumes a stable image coordinate system, so using it on
            # these dynamic ROIs can propagate invalid landmarks.
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_poses=4,
            min_pose_detection_confidence=confidence,
            min_pose_presence_confidence=confidence,
            min_tracking_confidence=confidence,
            output_segmentation_masks=False,
        )
        self.detector = mp.tasks.vision.PoseLandmarker.create_from_options(options)

    def close(self) -> None:
        self.detector.close()

    def detect(self, image_bgr: np.ndarray, timestamp_ms: int) -> list[dict[str, Any]]:
        del timestamp_ms
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        image = self.mp.Image(
            image_format=self.mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(rgb),
        )
        result = self.detector.detect(image)
        height, width = image_bgr.shape[:2]
        poses = []
        for landmarks in result.pose_landmarks:
            keypoints = {}
            bbox_points = []
            confidences = []
            for index, landmark in enumerate(landmarks):
                confidence = min(
                    float(getattr(landmark, "visibility", 0.0)),
                    float(getattr(landmark, "presence", 0.0)),
                )
                x = float(landmark.x) * width
                y = float(landmark.y) * height
                if confidence >= 0.20:
                    bbox_points.append((x, y))
                    confidences.append(confidence)
                name = MEDIAPIPE_NAMES.get(index)
                if name:
                    keypoints[name] = {
                        "x": round(x, 2),
                        "y": round(y, 2),
                        "confidence": round(confidence, 4),
                    }
            if not bbox_points:
                continue
            xs = [point[0] for point in bbox_points]
            ys = [point[1] for point in bbox_points]
            poses.append(
                {
                    "bbox": [
                        round(max(0.0, min(xs)), 2),
                        round(max(0.0, min(ys)), 2),
                        round(min(float(width), max(xs)), 2),
                        round(min(float(height), max(ys)), 2),
                    ],
                    "confidence": round(mean(confidences) or 0.0, 4),
                    "keypoints": keypoints,
                }
            )
        return poses


class RTMPoseONNXDetector:
    """Top-down RTMPose inference adapted from OpenMMLab's ONNX example."""

    def __init__(
        self,
        model_path: Path,
        confidence: float,
        device: str,
        imgsz: int,
    ):
        del confidence, imgsz
        import onnxruntime as ort

        available = ort.get_available_providers()
        requested_provider = {
            "cuda": "CUDAExecutionProvider",
            "coreml": "CoreMLExecutionProvider",
        }.get(device)
        providers = (
            [requested_provider, "CPUExecutionProvider"]
            if requested_provider in available
            else ["CPUExecutionProvider"]
        )
        self.session = ort.InferenceSession(str(model_path), providers=providers)
        input_shape = self.session.get_inputs()[0].shape
        self.input_size = (int(input_shape[3]), int(input_shape[2]))

    def close(self) -> None:
        return None

    @staticmethod
    def _fix_aspect_ratio(scale: np.ndarray, aspect_ratio: float) -> np.ndarray:
        width, height = float(scale[0]), float(scale[1])
        if width > height * aspect_ratio:
            height = width / aspect_ratio
        else:
            width = height * aspect_ratio
        return np.array([width, height], dtype=np.float32)

    @staticmethod
    def _third_point(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        direction = a - b
        return b + np.array([-direction[1], direction[0]], dtype=np.float32)

    def _preprocess(
        self,
        image_bgr: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        height, width = image_bgr.shape[:2]
        center = np.array([width / 2.0, height / 2.0], dtype=np.float32)
        scale = np.array([width, height], dtype=np.float32) * 1.25
        input_width, input_height = self.input_size
        scale = self._fix_aspect_ratio(
            scale,
            input_width / input_height,
        )
        source_direction = np.array(
            [0.0, -scale[0] * 0.5],
            dtype=np.float32,
        )
        destination_direction = np.array(
            [0.0, -input_width * 0.5],
            dtype=np.float32,
        )
        source = np.zeros((3, 2), dtype=np.float32)
        source[0] = center
        source[1] = center + source_direction
        source[2] = self._third_point(source[0], source[1])
        destination = np.zeros((3, 2), dtype=np.float32)
        destination[0] = [input_width * 0.5, input_height * 0.5]
        destination[1] = destination[0] + destination_direction
        destination[2] = self._third_point(destination[0], destination[1])
        matrix = cv2.getAffineTransform(source, destination)
        resized = cv2.warpAffine(
            image_bgr,
            matrix,
            (input_width, input_height),
            flags=cv2.INTER_LINEAR,
        )
        mean_values = np.array([123.675, 116.28, 103.53], dtype=np.float32)
        std_values = np.array([58.395, 57.12, 57.375], dtype=np.float32)
        normalized = (resized.astype(np.float32) - mean_values) / std_values
        return normalized, center, scale

    @staticmethod
    def _decode(
        outputs: list[np.ndarray],
        input_size: tuple[int, int],
        center: np.ndarray,
        scale: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        simcc_x, simcc_y = outputs
        batch, keypoint_count, _ = simcc_x.shape
        x_flat = simcc_x.reshape(batch * keypoint_count, -1)
        y_flat = simcc_y.reshape(batch * keypoint_count, -1)
        x_locations = np.argmax(x_flat, axis=1)
        y_locations = np.argmax(y_flat, axis=1)
        scores = np.minimum(
            np.max(x_flat, axis=1),
            np.max(y_flat, axis=1),
        ).reshape(batch, keypoint_count)
        keypoints = np.stack((x_locations, y_locations), axis=-1).astype(
            np.float32
        )
        keypoints = keypoints.reshape(batch, keypoint_count, 2) / 2.0
        keypoints = (
            keypoints / np.array(input_size, dtype=np.float32) * scale
            + center
            - scale / 2.0
        )
        return keypoints, scores

    def detect(self, image_bgr: np.ndarray, timestamp_ms: int) -> list[dict[str, Any]]:
        del timestamp_ms
        normalized, center, scale = self._preprocess(image_bgr)
        input_name = self.session.get_inputs()[0].name
        output_names = [output.name for output in self.session.get_outputs()]
        outputs = self.session.run(
            output_names,
            {input_name: np.expand_dims(normalized.transpose(2, 0, 1), axis=0)},
        )
        keypoint_batches, score_batches = self._decode(
            outputs,
            self.input_size,
            center,
            scale,
        )
        poses = []
        for points, scores in zip(keypoint_batches, score_batches):
            named_keypoints = {}
            visible_points = []
            names = WHOLEBODY_NAMES if len(points) == 133 else COCO_NAMES
            for name, point, score in zip(names, points, scores):
                confidence = float(score)
                x, y = float(point[0]), float(point[1])
                named_keypoints[name] = {
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "confidence": round(confidence, 4),
                }
                if confidence >= 0.10:
                    visible_points.append((x, y))
            if not visible_points:
                continue
            xs = [point[0] for point in visible_points]
            ys = [point[1] for point in visible_points]
            poses.append(
                {
                    "bbox": [
                        round(max(0.0, min(xs)), 2),
                        round(max(0.0, min(ys)), 2),
                        round(min(float(image_bgr.shape[1]), max(xs)), 2),
                        round(min(float(image_bgr.shape[0]), max(ys)), 2),
                    ],
                    "confidence": round(float(np.mean(scores)), 4),
                    "keypoints": named_keypoints,
                }
            )
        return poses


class VitPoseHFDetector:
    """Top-down ViTPose inference through the official Transformers API."""

    def __init__(
        self,
        model_path: str | Path,
        confidence: float,
        device: str,
        imgsz: int,
        allow_model_download: bool = False,
    ):
        del confidence, imgsz
        from transformers import AutoProcessor, VitPoseForPoseEstimation

        self.device = torch.device(device)
        model_ref = str(model_path)
        try:
            self.processor = AutoProcessor.from_pretrained(
                model_ref,
                local_files_only=not allow_model_download,
            )
            self.model = VitPoseForPoseEstimation.from_pretrained(
                model_ref,
                local_files_only=not allow_model_download,
            )
        except OSError as exc:
            if allow_model_download:
                raise
            raise RuntimeError(
                "ViTPose model is not available in the local Hugging Face cache. "
                "Re-run with --allow-model-download once to download it, or pass "
                "--pose-model with a local model directory."
            ) from exc
        self.model.to(self.device)
        self.model.eval()

    def close(self) -> None:
        return None

    def detect(self, image_bgr: np.ndarray, timestamp_ms: int) -> list[dict[str, Any]]:
        del timestamp_ms
        from PIL import Image

        height, width = image_bgr.shape[:2]
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image_rgb)
        boxes = np.array([[[0.0, 0.0, float(width), float(height)]]], dtype=np.float32)
        inputs = self.processor(
            image,
            boxes=boxes,
            return_tensors="pt",
        ).to(self.device)
        with torch.inference_mode():
            outputs = self.model(**inputs)
        pose_results = self.processor.post_process_pose_estimation(
            outputs,
            boxes=boxes,
        )[0]
        poses = []
        for pose_result in pose_results:
            points = pose_result["keypoints"].detach().cpu().numpy()
            scores = pose_result["scores"].detach().cpu().numpy()
            named_keypoints = {}
            visible_points = []
            for name, point, score in zip(COCO_NAMES, points, scores):
                confidence = float(score)
                x, y = float(point[0]), float(point[1])
                named_keypoints[name] = {
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "confidence": round(confidence, 4),
                }
                if confidence >= 0.10:
                    visible_points.append((x, y))
            if not visible_points:
                continue
            xs = [point[0] for point in visible_points]
            ys = [point[1] for point in visible_points]
            poses.append(
                {
                    "bbox": [
                        round(max(0.0, min(xs)), 2),
                        round(max(0.0, min(ys)), 2),
                        round(min(float(width), max(xs)), 2),
                        round(min(float(height), max(ys)), 2),
                    ],
                    "confidence": round(float(np.mean(scores)), 4),
                    "keypoints": named_keypoints,
                }
            )
        return poses


def create_detector(
    backend: str,
    model_path: str | Path,
    confidence: float,
    device: str,
    imgsz: int,
    allow_model_download: bool = False,
) -> (
    UltralyticsPoseDetector
    | MediaPipePoseDetector
    | RTMPoseONNXDetector
    | VitPoseHFDetector
):
    if backend == "ultralytics":
        return UltralyticsPoseDetector(model_path, confidence, device, imgsz)
    if backend == "mediapipe":
        return MediaPipePoseDetector(model_path, confidence, device, imgsz)
    if backend == "rtmpose_onnx":
        return RTMPoseONNXDetector(model_path, confidence, device, imgsz)
    if backend == "vitpose_hf":
        return VitPoseHFDetector(
            model_path,
            confidence,
            device,
            imgsz,
            allow_model_download=allow_model_download,
        )
    raise ValueError(f"Unsupported pose backend: {backend}")


def draw_label(
    image: np.ndarray,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    cv2.putText(
        image,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        color,
        2,
        cv2.LINE_AA,
    )


def draw_pose(
    image: np.ndarray,
    keypoints: dict[str, dict[str, float]],
    offset_x: int,
    offset_y: int,
    min_confidence: float,
    keypoint_bounds: list[float] | None = None,
    render_policy: str = "full_pose",
) -> None:
    def visible(point: dict[str, float] | None) -> bool:
        if not point:
            return False
        if float(point.get("confidence") or 0.0) < min_confidence:
            return False
        if keypoint_bounds is None:
            return True
        x1, y1, x2, y2 = keypoint_bounds
        return (
            x1 <= float(point["x"]) <= x2
            and y1 <= float(point["y"]) <= y2
        )

    skeleton = (
        [
            ("left_shoulder", "right_shoulder"),
            ("left_shoulder", "left_hip"),
            ("right_shoulder", "right_hip"),
            ("left_hip", "right_hip"),
        ]
        if render_policy == "torso_only"
        else SKELETON
    )
    rendered_names = {name for edge in skeleton for name in edge}
    for start_name, end_name in skeleton:
        start = keypoints.get(start_name)
        end = keypoints.get(end_name)
        if not visible(start) or not visible(end):
            continue
        start_point = (
            offset_x + int(round(float(start["x"]))),
            offset_y + int(round(float(start["y"]))),
        )
        end_point = (
            offset_x + int(round(float(end["x"]))),
            offset_y + int(round(float(end["y"]))),
        )
        tracked = any(
            point.get("temporal_source") != "observed"
            for point in (start, end)
        )
        color = (0, 165, 255) if tracked else (255, 0, 255)
        cv2.line(image, start_point, end_point, color, 2, cv2.LINE_AA)
    for name in COCO_NAMES:
        if render_policy == "torso_only" and name not in rendered_names:
            continue
        point = keypoints.get(name)
        if not visible(point):
            continue
        center = (
            offset_x + int(round(float(point["x"]))),
            offset_y + int(round(float(point["y"]))),
        )
        cv2.circle(image, center, 3, (0, 255, 255), -1, cv2.LINE_AA)


def draw_hands(
    image: np.ndarray,
    keypoints: dict[str, dict[str, float]],
    offset_x: int,
    offset_y: int,
    min_confidence: float,
) -> None:
    fingers = ((0, 1, 2, 3, 4), (0, 5, 6, 7, 8), (0, 9, 10, 11, 12),
               (0, 13, 14, 15, 16), (0, 17, 18, 19, 20))
    for side, color in (("left", (255, 255, 0)), ("right", (0, 165, 255))):
        for finger in fingers:
            for start_index, end_index in zip(finger, finger[1:]):
                start = keypoints.get(f"{side}_hand_{start_index}")
                end = keypoints.get(f"{side}_hand_{end_index}")
                if not start or not end:
                    continue
                if min(
                    float(start.get("confidence") or 0.0),
                    float(end.get("confidence") or 0.0),
                ) < min_confidence:
                    continue
                cv2.line(
                    image,
                    (
                        offset_x + int(round(float(start["x"]))),
                        offset_y + int(round(float(start["y"]))),
                    ),
                    (
                        offset_x + int(round(float(end["x"]))),
                        offset_y + int(round(float(end["y"]))),
                    ),
                    color,
                    1,
                    cv2.LINE_AA,
                )


def process_video(
    video_path: Path,
    cabin_video: dict[str, Any],
    experiment_id: str,
    experiment: dict[str, Any],
    detector: Any,
    args: argparse.Namespace,
    device: str,
) -> dict[str, Any]:
    frame_meta = cabin_video.get("frame_meta") or {}
    width = int(frame_meta.get("width") or 0)
    height = int(frame_meta.get("height") or 0)
    fps = float(frame_meta.get("fps") or 25.0)
    records = cabin_video.get("per_frame") or []
    selected_records = records[:: max(1, args.frame_stride)]
    by_frame = {int(item["frame"]): item for item in selected_records}
    print(
        f"\n=== {video_path.name}: driver upper-body pose ===\n"
        f"backend={experiment['backend']}, evaluable input={len(selected_records)}, "
        f"stride={args.frame_stride}"
    )

    run_dir = args.runs_root / experiment_id.lower().replace("-", "_")
    roi_dir = run_dir / "rois" / video_path.stem
    annotated_dir = run_dir / "annotated"
    roi_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)
    annotated_path = (
        annotated_dir / f"{video_path.stem}_{experiment['model_key']}.mp4"
    )

    output_width = max(1, int(width * args.video_scale))
    output_height = max(1, int(height * args.video_scale))
    writer = cv2.VideoWriter(
        str(annotated_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (output_width, output_height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not create annotated video: {annotated_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        writer.release()
        raise RuntimeError(f"Could not open video: {video_path}")

    frame_results = []
    latencies = []
    frame_number = 0
    stabilizer = None
    if experiment.get("temporal_stabilization"):
        stabilizer = TemporalKeypointStabilizer(
            min_confidence=args.keypoint_conf,
            hold_frames=max(
                1,
                int(
                    round(
                        fps
                        * float(experiment["temporal_hold_ms"])
                        / 1000.0
                    )
                ),
            ),
            smoothing_alpha=float(experiment["temporal_smoothing_alpha"]),
            max_jump_face_units=float(
                experiment["temporal_max_jump_face_units"]
            ),
            continuation_confidence=experiment.get(
                "temporal_continuation_confidence"
            ),
            max_continuation_frames=max(
                0,
                int(
                    round(
                        fps
                        * float(
                            experiment.get(
                                "temporal_max_continuation_ms",
                                0,
                            )
                        )
                        / 1000.0
                    )
                ),
            ),
            continuation_max_jump_face_units=float(
                experiment.get(
                    "temporal_continuation_max_jump_face_units",
                    0.45,
                )
            ),
        )
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            record = by_frame.get(frame_number)
            if record:
                visibility = str(record.get("visibility") or "not_visible")
                face_bbox = driver_face_global_bbox(record)
                driver_face_confidence = None
                driver_face_index = record.get("driver_face_index")
                faces = record.get("faces") or []
                if (
                    driver_face_index is not None
                    and 0 <= int(driver_face_index) < len(faces)
                ):
                    driver_face_confidence = float(
                        faces[int(driver_face_index)].get("confidence") or 0.0
                    )
                vehicle_bbox = record.get("vehicle_bbox_xyxy")
                result_record: dict[str, Any] = {
                    "frame": frame_number,
                    "visibility": visibility,
                    "visibility_score": record.get("visibility_score"),
                    "role_assignment_status": record.get("role_assignment_status"),
                    "driver_face_bbox": face_bbox,
                    "driver_face_confidence": driver_face_confidence,
                    "pose_evidence_only": False,
                    "upper_body_roi_bbox": None,
                    "pose_count": 0,
                    "driver_pose_index": None,
                    "driver_pose_detected": None,
                    "raw_driver_pose_detected": None,
                    "pose_association_status": "not_evaluable",
                    "pose_association_score": None,
                    "pose_confidence": None,
                    "anchor_confidence": None,
                    "shoulders_visible": None,
                    "hips_visible": None,
                    "arm_chain_count": 0,
                    "hand_anchor_count": 0,
                    "hand_near_face_count": 0,
                    "hands": {},
                    "seatbelt_anchor_ready": None,
                    "phone_anchor_ready": None,
                    "torso_status": "not_evaluable",
                    "torso_bbox_global": None,
                    "upper_body_analysis_ready": None,
                    "driver_analysis_ready": None,
                    "pose_latency_ms": 0.0,
                    "temporal_observed_keypoint_count": 0,
                    "temporal_held_keypoint_count": 0,
                    "temporal_rejected_jump_count": 0,
                    "upper_body_roi_uri": None,
                    "poses": [],
                }
                decision_evaluable = visibility in {"good", "limited"}
                inference_eligible, pose_evidence_only = pose_inference_gate(
                    visibility,
                    driver_face_confidence,
                    bool(
                        face_bbox is not None
                        and vehicle_bbox is not None
                        and record.get("cabin_bbox_xyxy") is not None
                    ),
                    experiment.get("run_on_poor_face_confidence"),
                )
                result_record["pose_evidence_only"] = pose_evidence_only
                if inference_eligible:
                    if experiment.get("roi_policy") == "cabin_clamped_face_anchor":
                        upper_roi = upper_body_cabin_roi_bbox(
                            face_bbox,
                            vehicle_bbox,
                            record["cabin_bbox_xyxy"],
                            width,
                            height,
                        )
                    elif experiment.get("roi_policy") == "driver_arm_focus":
                        upper_roi = driver_arm_focus_roi_bbox(
                            face_bbox,
                            vehicle_bbox,
                            record["cabin_bbox_xyxy"],
                            str(record.get("view_profile") or "unknown"),
                            width,
                            height,
                        )
                    else:
                        upper_roi = upper_body_roi_bbox(
                            face_bbox,
                            vehicle_bbox,
                            width,
                            height,
                        )
                    ux1, uy1, ux2, uy2 = upper_roi
                    crop = frame[uy1:uy2, ux1:ux2].copy()
                    roi_path = roi_dir / f"frame_{frame_number:06d}_upper_body.jpg"
                    cv2.imwrite(
                        str(roi_path),
                        crop,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 95],
                    )
                    started = time.perf_counter()
                    poses = detector.detect(
                        crop,
                        int(frame_number / max(fps, 1.0) * 1000),
                    )
                    latency = (time.perf_counter() - started) * 1000.0
                    latencies.append(latency)
                    local_face = xyxy_to_local(face_bbox, upper_roi)
                    pose_index, association_status, association_score = (
                        associate_driver_pose(poses, local_face)
                    )
                    raw_pose_detected = pose_index is not None
                    temporal_stats = {
                        "observed_keypoint_count": 0,
                        "held_keypoint_count": 0,
                        "rejected_jump_count": 0,
                    }
                    if stabilizer is not None:
                        raw_keypoints = (
                            poses[pose_index]["keypoints"]
                            if pose_index is not None
                            else {}
                        )
                        stabilized_keypoints, temporal_stats = stabilizer.update(
                            raw_keypoints,
                            local_face,
                            frame_number,
                        )
                        if stabilized_keypoints:
                            if pose_index is None:
                                poses = [
                                    {
                                        "bbox": [
                                            0.0,
                                            0.0,
                                            float(max(1, ux2 - ux1)),
                                            float(max(1, uy2 - uy1)),
                                        ],
                                        "confidence": 0.0,
                                        "keypoints": stabilized_keypoints,
                                        "temporal_recovered": True,
                                    }
                                ]
                                pose_index = 0
                                association_status = "temporal_pose_recovered"
                                association_score = None
                            else:
                                poses[pose_index]["keypoints"] = (
                                    stabilized_keypoints
                                )
                                poses[pose_index]["temporal_stabilized"] = True
                    result_record.update(
                        {
                            "upper_body_roi_bbox": upper_roi,
                            "pose_count": len(poses),
                            "driver_pose_index": pose_index,
                            "driver_pose_detected": pose_index is not None,
                            "raw_driver_pose_detected": raw_pose_detected,
                            "pose_association_status": association_status,
                            "pose_association_score": association_score,
                            "pose_latency_ms": round(latency, 3),
                            "temporal_observed_keypoint_count": temporal_stats[
                                "observed_keypoint_count"
                            ],
                            "temporal_held_keypoint_count": temporal_stats[
                                "held_keypoint_count"
                            ],
                            "temporal_rejected_jump_count": temporal_stats[
                                "rejected_jump_count"
                            ],
                            "upper_body_roi_uri": rel(roi_path),
                            "poses": poses,
                        }
                    )
                    cv2.rectangle(frame, (ux1, uy1), (ux2, uy2), (0, 200, 255), 2)
                    draw_label(
                        frame,
                        "driver upper-body ROI",
                        (ux1, max(24, uy1 - 8)),
                        (0, 200, 255),
                    )
                    if pose_index is not None:
                        pose = poses[pose_index]
                        torso = torso_from_keypoints(
                            pose["keypoints"],
                            max(1, ux2 - ux1),
                            max(1, uy2 - uy1),
                            args.keypoint_conf,
                            local_face,
                            xyxy_to_local(
                                record["cabin_bbox_xyxy"],
                                upper_roi,
                            ),
                        )
                        local_torso = torso.get("torso_bbox")
                        global_torso = None
                        if local_torso:
                            global_torso = intersect_bbox(
                                [
                                    ux1 + local_torso[0],
                                    uy1 + local_torso[1],
                                    ux1 + local_torso[2],
                                    uy1 + local_torso[3],
                                ],
                                record["cabin_bbox_xyxy"],
                            )
                            if global_torso:
                                cv2.rectangle(
                                    frame,
                                    (global_torso[0], global_torso[1]),
                                    (global_torso[2], global_torso[3]),
                                    (0, 255, 0),
                                    2,
                                )
                            else:
                                torso.update(
                                    {
                                        "status": "torso_outside_visible_cabin",
                                        "seatbelt_anchor_ready": False,
                                        "phone_anchor_ready": False,
                                    }
                                )
                        geometric_upper_body_ready = bool(
                            torso.get("seatbelt_anchor_ready", False)
                            and global_torso is not None
                        )
                        local_cabin_bounds = xyxy_to_local(
                            record["cabin_bbox_xyxy"],
                            upper_roi,
                        )
                        draw_pose(
                            frame,
                            pose["keypoints"],
                            ux1,
                            uy1,
                            args.keypoint_conf,
                            local_cabin_bounds,
                            str(
                                experiment.get(
                                    "render_policy",
                                    "full_pose",
                                )
                            ),
                        )
                        hand_summary = hand_anchor_summary(
                            pose["keypoints"],
                            local_face,
                            min_confidence=args.hand_keypoint_conf,
                            minimum_points=args.min_hand_points,
                            max_face_distance=args.max_hand_face_distance,
                        )
                        draw_hands(
                            frame,
                            pose["keypoints"],
                            ux1,
                            uy1,
                            args.hand_keypoint_conf,
                        )
                        action_anchor_ready = bool(
                            experiment.get("enable_arm_anchors", True)
                            and (
                                torso.get("phone_anchor_ready", False)
                                or hand_summary["hand_near_face_count"] > 0
                            )
                        )
                        phone_anchor_ready = (
                            torso.get("phone_anchor_ready", False)
                            if experiment.get("enable_arm_anchors", True)
                            else None
                        )
                        result_record.update(
                            {
                                "pose_confidence": pose.get("confidence"),
                                "anchor_confidence": torso.get(
                                    "mean_anchor_confidence"
                                ),
                                "shoulders_visible": torso.get(
                                    "shoulders_visible"
                                ),
                                "hips_visible": torso.get("hips_visible"),
                                "arm_chain_count": torso.get(
                                    "arm_chain_count", 0
                                ),
                                "hand_anchor_count": hand_summary[
                                    "hand_anchor_count"
                                ],
                                "hand_near_face_count": hand_summary[
                                    "hand_near_face_count"
                                ],
                                "hands": hand_summary["hands"],
                                "seatbelt_anchor_ready": torso.get(
                                    "seatbelt_anchor_ready", False
                                ),
                                "phone_anchor_ready": torso.get(
                                    "phone_anchor_ready", False
                                ),
                                "action_anchor_ready": action_anchor_ready,
                                "torso_status": torso.get("status"),
                                "torso_bbox_global": global_torso,
                                "upper_body_analysis_ready": (
                                    geometric_upper_body_ready
                                    if decision_evaluable
                                    else None
                                ),
                                # Compatibility alias for older artifacts.
                                "driver_analysis_ready": (
                                    geometric_upper_body_ready
                                    if decision_evaluable
                                    else None
                                ),
                            }
                        )
                        result_record["phone_anchor_ready"] = (
                            phone_anchor_ready
                        )
                    else:
                        result_record["upper_body_analysis_ready"] = (
                            False if decision_evaluable else None
                        )
                        result_record["driver_analysis_ready"] = (
                            False if decision_evaluable else None
                        )

                if face_bbox:
                    fx1, fy1, fx2, fy2 = face_bbox
                    cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (255, 0, 255), 2)
                    draw_label(
                        frame,
                        "YuNet driver face anchor",
                        (fx1, max(24, fy1 - 8)),
                        (255, 0, 255),
                    )
                if result_record["pose_evidence_only"]:
                    status = "evidence-only"
                else:
                    status = (
                        "ready"
                        if result_record["upper_body_analysis_ready"] is True
                        else result_record["pose_association_status"]
                    )
                if result_record["temporal_held_keypoint_count"] > 0:
                    status += (
                        f" held={result_record['temporal_held_keypoint_count']}"
                    )
                draw_label(frame, f"pose: {status}", (24, 36), (255, 255, 255))
                frame_results.append(result_record)

            output = (
                cv2.resize(
                    frame,
                    (output_width, output_height),
                    interpolation=cv2.INTER_AREA,
                )
                if args.video_scale != 1.0
                else frame
            )
            writer.write(output)
    finally:
        cap.release()
        writer.release()

    temporal = temporal_pose_summary(
        frame_results,
        min_ready_frames=args.min_ready_frames,
        min_ready_rate=args.min_ready_rate,
        fps=fps,
        frame_stride=args.frame_stride,
    )
    return {
        "video": video_path.name,
        "event_id": cabin_video.get("event_id"),
        "status": "completed",
        "view_profile": cabin_video.get("view_profile"),
        "input_frame_count": len(records),
        "processed_frame_count": len(frame_results),
        "frame_stride": args.frame_stride,
        "mean_pose_latency_ms": mean(latencies),
        "p95_pose_latency_ms": p95(latencies),
        "temporal": temporal,
        "annotated_video": rel(annotated_path),
        "roi_dir": rel(roi_dir),
        "per_frame": frame_results,
    }


def build_report(summary: dict[str, Any]) -> str:
    rows = []
    for video in summary.get("videos", []):
        temporal = video.get("temporal") or {}
        rows.append(
            "| {video} | {profile} | {evaluable} | {pose_rate} | {seatbelt_rate} | "
            "{phone_rate} | "
            "{hand_rate} | {hand_face_rate} | {detected} | {miss} | "
            "{miss_seconds} | {jitter} | {mean_ms} | "
            "{p95_ms} |".format(
                video=video.get("video"),
                profile=video.get("view_profile"),
                evaluable=temporal.get("evaluable_driver_frame_count"),
                pose_rate=temporal.get("pose_detection_rate"),
                seatbelt_rate=temporal.get("seatbelt_anchor_rate"),
                phone_rate=temporal.get("phone_anchor_rate"),
                hand_rate=temporal.get("hand_anchor_rate"),
                hand_face_rate=temporal.get("hand_near_face_rate"),
                detected=temporal.get("upper_body_detected"),
                miss=temporal.get("longest_analysis_miss_run"),
                miss_seconds=temporal.get("longest_analysis_miss_seconds"),
                jitter=temporal.get("p95_shoulder_jitter_face_units"),
                mean_ms=video.get("mean_pose_latency_ms"),
                p95_ms=video.get("p95_pose_latency_ms"),
            )
        )
    return "\n".join(
        [
            f"# {summary['experiment_id']} Driver Upper-Body / Pose Baseline",
            "",
            f"Tarih: {summary['created_at_utc']}",
            "",
            "## Zincir",
            "",
            "`YuNet driver face -> face-anchored upper-body ROI -> pose -> torso ROI -> temporal decision`",
            "",
            "## Konfigürasyon",
            "",
            f"* Model: `{summary['model_key']}`",
            f"* Backend: `{summary['backend']}`",
            f"* Model path: `{summary['model_path']}`",
            f"* Cabin input: `{summary['input_cabin_summary']}`",
            f"* Frame stride: `{summary['frame_stride']}`",
            f"* Pose confidence: `{summary['pose_confidence']}`",
            f"* Keypoint confidence: `{summary['keypoint_confidence']}`",
            f"* Temporal stabilization: `{summary.get('temporal_stabilization')}`",
            "",
            "## Otomatik Sonuç",
            "",
            "| Video | Profil | Evaluable | Pose Rate | Seatbelt Anchor | Phone Anchor | "
            "Hand | Hand Near Face | Upper Body | Longest Miss | Miss sec | "
            "P95 Jitter | Mean ms | P95 ms |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|",
            *rows,
            "",
            "## Yorumlama",
            "",
            "* `seatbelt_anchor_ready`, driver yüzüyle anatomik olarak uyumlu iki omuz "
            "ve torso bulunduğunda true olur.",
            "* `phone_anchor_ready`, seatbelt anchor'a ek olarak en az bir güvenilir "
            "omuz-dirsek-bilek zinciri gerektirir.",
            f"* Arm anchors enabled: `{summary.get('arm_anchors_enabled', True)}`. "
            "`False` ise dirsek/bilek yalnız tanısal model çıktısıdır; overlay veya "
            "risk anchor'ı değildir.",
            "* Kalçalar görünmüyorsa torso alt sınırı omuz genişliğinden kontrollü biçimde "
            "tahmin edilir.",
            "* Bu deney seatbelt veya phone sınıflandırması yapmaz; yalnız specialist "
            "modüller için anchor üretir.",
            "* Model seçimi otomatik oranlar ve tam overlay manuel review birlikte "
            "değerlendirildikten sonra yapılır.",
            "",
            "## Manuel Review",
            "",
            "* Şablon: `testing/templates/manual_driver_pose_review.csv`",
            "* Büyük ROI ve overlay çıktıları `runs/cabin_pose/` altında Git dışındadır.",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark driver upper-body pose models from YuNet cabin output."
    )
    parser.add_argument(
        "--experiment",
        choices=sorted(EXPERIMENTS),
        default="POSE-EXP-001",
    )
    parser.add_argument("--cabin-summary", type=Path, default=DEFAULT_CABIN_SUMMARY)
    parser.add_argument("--videos-dir", type=Path, default=DEFAULT_VIDEOS_DIR)
    parser.add_argument("--videos", type=Path, nargs="*")
    parser.add_argument("--pose-model")
    parser.add_argument("--pose-conf", type=float, default=0.25)
    parser.add_argument("--keypoint-conf", type=float)
    parser.add_argument("--hand-keypoint-conf", type=float)
    parser.add_argument("--min-hand-points", type=int, default=4)
    parser.add_argument("--max-hand-face-distance", type=float)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="auto")
    parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help=(
            "Allow Hugging Face model download for vitpose_hf experiments. "
            "Without this flag, the runner uses the local cache only."
        ),
    )
    parser.add_argument("--frame-stride", type=int, default=1)
    parser.add_argument("--min-ready-frames", type=int, default=3)
    parser.add_argument("--min-ready-rate", type=float, default=0.30)
    parser.add_argument("--video-scale", type=float, default=0.50)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    experiment = EXPERIMENTS[args.experiment]
    if args.keypoint_conf is None:
        args.keypoint_conf = float(experiment["keypoint_confidence"])
    if args.hand_keypoint_conf is None:
        args.hand_keypoint_conf = float(experiment["hand_keypoint_confidence"])
    if args.max_hand_face_distance is None:
        args.max_hand_face_distance = float(
            experiment["max_hand_face_distance"]
        )
    cabin_summary_path = args.cabin_summary.resolve()
    if not cabin_summary_path.exists():
        raise SystemExit(f"Cabin summary not found: {cabin_summary_path}")
    model_ref: str | Path = args.pose_model or experiment["model_path"]
    if experiment["backend"] != "vitpose_hf":
        model_ref = Path(model_ref).resolve()
        if not model_ref.exists():
            raise SystemExit(
                f"Pose model not found: {model_ref}\n"
                "Run the download command in "
                "research/08_cabin_risk/upper_body_pose/RUN_DRIVER_POSE_BASELINE.md."
            )

    cabin_summary = json.loads(cabin_summary_path.read_text(encoding="utf-8"))
    selected_names = (
        {path.name for path in args.videos}
        if args.videos
        else {item.get("video") for item in cabin_summary.get("videos", [])}
    )
    cabin_videos = [
        item
        for item in cabin_summary.get("videos", [])
        if item.get("video") in selected_names and item.get("status") == "completed"
    ]
    device = resolve_device(args.device)
    if experiment["backend"] == "rtmpose_onnx" and device == "mps":
        device = "cpu"
    detector = create_detector(
        experiment["backend"],
        model_ref,
        args.pose_conf,
        device,
        args.imgsz,
        allow_model_download=args.allow_model_download,
    )
    results = []
    try:
        for cabin_video in cabin_videos:
            video_path = (args.videos_dir / str(cabin_video["video"])).resolve()
            if not video_path.exists():
                results.append(
                    {
                        "video": cabin_video["video"],
                        "status": "failed",
                        "failure_reason": "source_video_not_found",
                    }
                )
                continue
            results.append(
                process_video(
                    video_path,
                    cabin_video,
                    args.experiment,
                    experiment,
                    detector,
                    args,
                    device,
                )
            )
    finally:
        detector.close()

    summary = {
        "experiment_id": args.experiment,
        "stage": "driver_upper_body_pose_baseline",
        "created_at_utc": now_utc(),
        "decision": experiment["decision"],
        "input_cabin_summary": rel(cabin_summary_path),
        "input_cabin_experiment_id": cabin_summary.get("experiment_id"),
        "model_key": experiment["model_key"],
        "backend": experiment["backend"],
        "inference_mode": (
            "image_per_dynamic_roi"
            if experiment["backend"] == "mediapipe"
            else (
                "topdown_onnx_per_dynamic_roi"
                if experiment["backend"] == "rtmpose_onnx"
                else (
                    "topdown_transformer_per_dynamic_roi"
                    if experiment["backend"] == "vitpose_hf"
                    else "independent_image_prediction"
                )
            )
        ),
        "model_path": rel(model_ref) if isinstance(model_ref, Path) else model_ref,
        "allow_model_download": bool(args.allow_model_download),
        "device": device,
        "frame_stride": args.frame_stride,
        "pose_confidence": args.pose_conf,
        "keypoint_confidence": args.keypoint_conf,
        "hand_keypoint_confidence": args.hand_keypoint_conf,
        "minimum_hand_points": args.min_hand_points,
        "maximum_hand_face_distance": args.max_hand_face_distance,
        "minimum_ready_frames": args.min_ready_frames,
        "minimum_ready_rate": args.min_ready_rate,
        "temporal_stabilization": bool(
            experiment.get("temporal_stabilization")
        ),
        "temporal_hold_ms": experiment.get("temporal_hold_ms"),
        "temporal_smoothing_alpha": experiment.get(
            "temporal_smoothing_alpha"
        ),
        "temporal_max_jump_face_units": experiment.get(
            "temporal_max_jump_face_units"
        ),
        "temporal_continuation_confidence": experiment.get(
            "temporal_continuation_confidence"
        ),
        "temporal_max_continuation_ms": experiment.get(
            "temporal_max_continuation_ms"
        ),
        "run_on_poor_face_confidence": experiment.get(
            "run_on_poor_face_confidence"
        ),
        "render_policy": experiment.get("render_policy", "full_pose"),
        "arm_anchors_enabled": bool(
            experiment.get("enable_arm_anchors", True)
        ),
        "manual_review_template": "testing/templates/manual_driver_pose_review.csv",
        "videos": results,
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = (
        args.artifact_dir
        / f"{args.experiment}-{experiment['model_key']}-summary.json"
    )
    report_path = (
        args.report_dir / f"{args.experiment.lower().replace('-', '_')}_pose_summary.md"
    )
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(build_report(summary) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": rel(summary_path),
                "report": rel(report_path),
                "completed_videos": sum(
                    item.get("status") == "completed" for item in results
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
