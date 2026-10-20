"""Command-line interface for ShelfSense AI image parsing pipeline."""

import argparse
import sys
from pathlib import Path

from .config import load_config
from .pipeline import ShelfImageParsingPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shelf_image_parsing",
        description="ShelfSense AI — Product Detection, Shelf Rows and Empty-Space Parsing Pipeline",
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        default="sample_inputs",
        help="Path to an input image file or directory of images.",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="outputs",
        help="Directory to save annotated images, JSON detections, and CSV summary.",
    )
    parser.add_argument(
        "-c", "--confidence",
        type=float,
        default=None,
        help="Confidence score threshold for product/empty detections (default: 0.20).",
    )
    parser.add_argument(
        "--row-confidence",
        type=float,
        default=None,
        help="Confidence score threshold for shelf row segmentation (default: 0.15).",
    )
    parser.add_argument(
        "-d", "--device",
        type=str,
        default="cpu",
        help="Inference compute device: 'cpu', 'mps', or 'cuda' (default: cpu).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to custom YAML configuration file.",
    )
    parser.add_argument(
        "--save-json",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Export machine-readable JSON detection results.",
    )
    parser.add_argument(
        "--save-csv",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Export summary metrics CSV table.",
    )
    parser.add_argument(
        "--save-annotated",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save combined annotated image.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(args.config)
    if args.confidence is not None:
        config.detection_model.confidence = args.confidence
    if args.row_confidence is not None:
        config.segmentation_model.confidence = args.row_confidence
    if args.device:
        config.device = args.device

    config.save_annotated_image = args.save_annotated
    config.save_json = args.save_json
    config.save_csv = args.save_csv

    print("=" * 60)
    print("🚀 ShelfSense AI — Image Parsing Pipeline")
    print("=" * 60)
    print(f"▶ Input Path       : {args.input}")
    print(f"▶ Output Directory : {args.output}")
    print(f"▶ Confidence       : {config.detection_model.confidence}")
    print(f"▶ Device           : {config.device}")
    print(f"▶ Detection Model  : {config.detection_model.path}")
    print(f"▶ Segmentation     : {config.segmentation_model.path}")
    print("=" * 60)

    try:
        pipeline = ShelfImageParsingPipeline(config=config)
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}", file=sys.stderr)
        return 1

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"❌ Error: Input path does not exist: {in_path}", file=sys.stderr)
        return 1

    try:
        results = pipeline.process_batch(
            input_path=in_path,
            output_dir=args.output,
            save_csv=args.save_csv,
        )
    except Exception as e:
        print(f"❌ Execution failed: {e}", file=sys.stderr)
        return 1

    print("\n✅ Processing Summary:")
    print("-" * 60)
    for res in results:
        status_icon = "✔" if res.model_status in ("completed", "mocked") else "⚠"
        empty_pct = f"{res.summary.empty_area_percentage:.1f}%" if res.summary.empty_area_percentage is not None else "N/A"
        print(
            f"{status_icon} {res.source_image:<20} | Status: {res.model_status:<10} | "
            f"Products: {res.summary.product_count:<3} | Empty: {res.summary.empty_region_count:<2} | "
            f"Rows: {res.summary.shelf_row_count:<2} | Empty Space: {empty_pct}"
        )
        if res.errors:
            for err in res.errors:
                print(f"    └─ Error: {err}")

    print("-" * 60)
    print(f"Artifacts saved to: {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
