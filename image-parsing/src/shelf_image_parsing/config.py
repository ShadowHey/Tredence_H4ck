"""Configuration management for ShelfSense AI image parsing pipeline."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class ModelConfig:
    path: str
    confidence: float = 0.25
    iou: float = 0.45
    class_mapping: Dict[int, str] = field(default_factory=dict)


@dataclass
class VisualElementConfig:
    color_bgr: List[int]
    thickness: int = 2
    label_prefix: str = ""
    show_confidence: bool = True
    fill_translucent: bool = False
    fill_alpha: float = 0.2
    font_scale: float = 0.45


@dataclass
class PipelineConfig:
    # Model settings
    detection_model: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            path="models/detect_product_empty_space.pt",
            confidence=0.25,
            iou=0.45,
            class_mapping={0: "empty_space", 1: "product"},
        )
    )
    segmentation_model: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            path="models/segment_shelf_rows.pt",
            confidence=0.25,
            iou=0.50,
            class_mapping={0: "shelf_row"},
        )
    )

    # Refinement settings
    # Product detections below this score are retained only as uncertainty
    # diagnostics; they are not passed to crop generation or matching.
    product_confidence_threshold: float = 0.60
    row_filter_width_ratio: float = 0.40
    empty_assignment_mode: str = "center_band"
    empty_nms_threshold: float = 0.50

    # Visual settings
    product_style: VisualElementConfig = field(
        default_factory=lambda: VisualElementConfig(
            color_bgr=[255, 229, 0],  # Cyan (#00E5FF in BGR)
            thickness=2,
            label_prefix="PRODUCT",
            show_confidence=True,
            font_scale=0.45,
        )
    )
    empty_space_style: VisualElementConfig = field(
        default_factory=lambda: VisualElementConfig(
            color_bgr=[183, 57, 23],  # Dark royal blue (#1739B7 in BGR)
            thickness=2,
            label_prefix="EMPTY SPACE",
            show_confidence=True,
            fill_translucent=True,
            fill_alpha=0.25,
            font_scale=0.45,
        )
    )
    shelf_row_style: VisualElementConfig = field(
        default_factory=lambda: VisualElementConfig(
            color_bgr=[0, 176, 255],  # Amber (#FFB000 in BGR)
            thickness=2,
            label_prefix="ROW",
            fill_translucent=True,
            fill_alpha=0.15,
            font_scale=0.55,
        )
    )

    # Output settings
    save_annotated_image: bool = True
    save_json: bool = True
    save_csv: bool = True
    default_output_dir: str = "outputs"
    device: str = "cpu"


def load_config(config_path: Optional[str] = None) -> PipelineConfig:
    """Load configuration from a YAML file, falling back to built-in defaults."""
    cfg = PipelineConfig()

    if config_path is None:
        default_path = Path(__file__).resolve().parent.parent.parent / "config" / "default.yaml"
        if default_path.is_file():
            config_path = str(default_path)

    if config_path and Path(config_path).is_file():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = yaml.safe_load(f) or {}

            # Parse models
            models_data = data.get("models", {})
            if "detection" in models_data:
                det = models_data["detection"]
                cfg.detection_model = ModelConfig(
                    path=det.get("path", cfg.detection_model.path),
                    confidence=float(det.get("confidence", cfg.detection_model.confidence)),
                    iou=float(det.get("iou", cfg.detection_model.iou)),
                    class_mapping=det.get("class_mapping", cfg.detection_model.class_mapping),
                )
            if "segmentation" in models_data:
                seg = models_data["segmentation"]
                cfg.segmentation_model = ModelConfig(
                    path=seg.get("path", cfg.segmentation_model.path),
                    confidence=float(seg.get("confidence", cfg.segmentation_model.confidence)),
                    iou=float(seg.get("iou", cfg.segmentation_model.iou)),
                    class_mapping=seg.get("class_mapping", cfg.segmentation_model.class_mapping),
                )

            # Parse refinement
            ref = data.get("refinement", {})
            cfg.product_confidence_threshold = float(
                ref.get("product_confidence_threshold", cfg.product_confidence_threshold)
            )
            if not 0.0 <= cfg.product_confidence_threshold <= 1.0:
                raise ValueError("refinement.product_confidence_threshold must be between 0 and 1")
            cfg.row_filter_width_ratio = float(ref.get("row_filter_width_ratio", cfg.row_filter_width_ratio))
            cfg.empty_assignment_mode = str(ref.get("empty_assignment_mode", cfg.empty_assignment_mode))
            cfg.empty_nms_threshold = float(ref.get("empty_nms_threshold", cfg.empty_nms_threshold))

            # Parse visualization
            vis = data.get("visualization", {})
            if "product" in vis:
                p = vis["product"]
                cfg.product_style.color_bgr = p.get("color_bgr", cfg.product_style.color_bgr)
                cfg.product_style.thickness = int(p.get("thickness", cfg.product_style.thickness))
                cfg.product_style.label_prefix = str(p.get("label_prefix", cfg.product_style.label_prefix))
                cfg.product_style.show_confidence = bool(p.get("show_confidence", cfg.product_style.show_confidence))
                cfg.product_style.font_scale = float(p.get("font_scale", cfg.product_style.font_scale))

            if "empty_space" in vis:
                e = vis["empty_space"]
                cfg.empty_space_style.color_bgr = e.get("color_bgr", cfg.empty_space_style.color_bgr)
                cfg.empty_space_style.thickness = int(e.get("thickness", cfg.empty_space_style.thickness))
                cfg.empty_space_style.label_prefix = str(e.get("label_prefix", cfg.empty_space_style.label_prefix))
                cfg.empty_space_style.show_confidence = bool(e.get("show_confidence", cfg.empty_space_style.show_confidence))
                cfg.empty_space_style.fill_translucent = bool(e.get("fill_translucent", cfg.empty_space_style.fill_translucent))
                cfg.empty_space_style.fill_alpha = float(e.get("fill_alpha", cfg.empty_space_style.fill_alpha))
                cfg.empty_space_style.font_scale = float(e.get("font_scale", cfg.empty_space_style.font_scale))

            if "shelf_row" in vis:
                r = vis["shelf_row"]
                cfg.shelf_row_style.color_bgr = r.get("color_bgr", cfg.shelf_row_style.color_bgr)
                cfg.shelf_row_style.thickness = int(r.get("thickness", cfg.shelf_row_style.thickness))
                cfg.shelf_row_style.label_prefix = str(r.get("label_prefix", cfg.shelf_row_style.label_prefix))
                cfg.shelf_row_style.fill_translucent = bool(r.get("fill_translucent", cfg.shelf_row_style.fill_translucent))
                cfg.shelf_row_style.fill_alpha = float(r.get("fill_alpha", cfg.shelf_row_style.fill_alpha))
                cfg.shelf_row_style.font_scale = float(r.get("font_scale", cfg.shelf_row_style.font_scale))

            # Outputs
            out = data.get("outputs", {})
            cfg.save_annotated_image = bool(out.get("save_annotated_image", cfg.save_annotated_image))
            cfg.save_json = bool(out.get("save_json", cfg.save_json))
            cfg.save_csv = bool(out.get("save_csv", cfg.save_csv))
            cfg.default_output_dir = str(out.get("default_output_dir", cfg.default_output_dir))

        except Exception as err:
            print(f"[WARNING] Failed to load config from {config_path}: {err}. Using default settings.")

    return cfg
