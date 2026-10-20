"""ShelfSense AI — Retail Shelf Image Parsing, Product Detection, Shelf Rows & Empty Space."""

from .config import PipelineConfig, load_config
from .detector import ProductEmptySpaceDetector
from .empty_space import EmptySpaceRefiner
from .pipeline import ShelfImageParsingPipeline
from .row_segmenter import ShelfRowSegmenter
from .schemas import DetectionItem, ImageParsingResult, ImageParsingSummary, ShelfRowItem
from .visualization import ShelfVisualizer

__version__ = "0.1.0"

__all__ = [
    "PipelineConfig",
    "load_config",
    "ProductEmptySpaceDetector",
    "ShelfRowSegmenter",
    "EmptySpaceRefiner",
    "ShelfVisualizer",
    "ShelfImageParsingPipeline",
    "DetectionItem",
    "ShelfRowItem",
    "ImageParsingSummary",
    "ImageParsingResult",
]
