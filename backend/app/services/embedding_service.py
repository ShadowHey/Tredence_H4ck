"""CLIP vector embedding service for product packshots and visual-semantic similarity."""

import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from PIL import Image

import torch
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Product

logger = logging.getLogger(__name__)

# Model configuration
DEFAULT_MODEL_NAME = "ViT-B-32-quickgelu"
DEFAULT_PRETRAINED = "openai"
EMBEDDING_DIM = 512


class ClipEmbeddingService:
    """Singleton service for generating and querying CLIP vector embeddings."""

    _instance: Optional["ClipEmbeddingService"] = None
    _model = None
    _preprocess = None
    _device = "cpu"

    def __new__(cls) -> "ClipEmbeddingService":
        if cls._instance is None:
            cls._instance = super(ClipEmbeddingService, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, pretrained: str = DEFAULT_PRETRAINED):
        self.model_name = model_name
        self.pretrained = pretrained
        # Select device: mps or cpu
        if torch.backends.mps.is_available():
            self._device = "mps"
        else:
            self._device = "cpu"

    def _ensure_model_loaded(self) -> None:
        """Lazily load and cache the CLIP model and torchvision preprocessing transforms."""
        if self._model is not None and self._preprocess is not None:
            return

        import open_clip

        logger.info(f"Loading CLIP model '{self.model_name}' (pretrained='{self.pretrained}') on {self._device}...")
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(
                self.model_name,
                pretrained=self.pretrained,
                device=self._device,
            )
            model.eval()
            self._model = model
            self._preprocess = preprocess
            logger.info("CLIP model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load CLIP model '{self.model_name}': {e}")
            raise RuntimeError(f"Could not initialize CLIP model: {e}") from e

    def resolve_image_path(self, raw_path: str) -> Optional[Path]:
        """Resolve a product image_path to a concrete local file system path."""
        if not raw_path:
            return None

        clean_path = raw_path.strip().lstrip("/")
        base_dir = Path(__file__).resolve().parent.parent.parent.parent  # repo root

        uploads_dir = getattr(settings, "UPLOADS_DIR", base_dir / "backend" / "uploads")
        candidates = [
            Path(raw_path),
            base_dir / clean_path,
            uploads_dir / clean_path,
            uploads_dir / "products" / Path(clean_path).name,
            base_dir / "backend" / "uploads" / clean_path,
            base_dir / "backend" / "uploads" / "products" / Path(clean_path).name,
            base_dir / "sample_assets" / clean_path,
            base_dir / "sample_assets" / "images" / Path(clean_path).name,
        ]

        # Check candidate paths
        for cand in candidates:
            if cand.is_file():
                # If SVG, look for matching .png companion
                if cand.suffix.lower() == ".svg":
                    png_companion = cand.with_suffix(".png")
                    if png_companion.is_file():
                        return png_companion
                return cand

        # If .svg was passed but not found, try looking for .png with same basename
        if clean_path.lower().endswith(".svg"):
            png_name = Path(clean_path).stem + ".png"
            for cand in [
                base_dir / "sample_assets" / "images" / png_name,
                uploads_dir / "products" / png_name,
            ]:
                if cand.is_file():
                    return cand

        return None

    def compute_image_embedding(
        self,
        image_input: Union[str, Path, Image.Image],
    ) -> List[float]:
        """Compute an L2-normalized 512-dimensional CLIP embedding vector from an image."""
        self._ensure_model_loaded()

        if isinstance(image_input, (str, Path)):
            resolved = self.resolve_image_path(str(image_input))
            if resolved is None or not resolved.is_file():
                raise FileNotFoundError(f"Product image file not found: '{image_input}'")
            pil_image = Image.open(resolved).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_image = image_input.convert("RGB")
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        tensor = self._preprocess(pil_image).unsqueeze(0).to(self._device)

        with torch.no_grad():
            features = self._model.encode_image(tensor)
            # L2 unit normalization so dot product == cosine similarity
            features = features / features.norm(dim=-1, keepdim=True)
            vector: List[float] = features[0].cpu().tolist()

        return vector

    def compute_image_embeddings_batch(
        self,
        images: List[Union[str, Path, Image.Image]],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """Compute L2-normalized 512-dim embeddings for a list of images in batches."""
        if not images:
            return []

        self._ensure_model_loaded()

        pil_images: List[Image.Image] = []
        for img_input in images:
            if isinstance(img_input, (str, Path)):
                resolved = self.resolve_image_path(str(img_input))
                if resolved is None or not resolved.is_file():
                    raise FileNotFoundError(f"Image file not found: '{img_input}'")
                pil_images.append(Image.open(resolved).convert("RGB"))
            elif isinstance(img_input, Image.Image):
                pil_images.append(img_input.convert("RGB"))
            else:
                raise ValueError(f"Unsupported image input type: {type(img_input)}")

        all_vectors: List[List[float]] = []

        for i in range(0, len(pil_images), batch_size):
            chunk = pil_images[i : i + batch_size]
            tensors = torch.stack([self._preprocess(img) for img in chunk]).to(self._device)
            with torch.no_grad():
                features = self._model.encode_image(tensors)
                features = features / features.norm(dim=-1, keepdim=True)
                chunk_vectors = features.cpu().tolist()
                all_vectors.extend(chunk_vectors)

        return all_vectors

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two L2-normalized vectors."""
        if not vec_a or not vec_b:
            return 0.0
        if len(vec_a) != len(vec_b):
            raise ValueError(f"Vector dimensions do not match: {len(vec_a)} vs {len(vec_b)}")

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        # Clamp to [-1.0, 1.0] to guard against floating-point inaccuracies
        return max(-1.0, min(1.0, float(dot)))

    def generate_and_store_product_embedding(
        self,
        db: Session,
        product_id: int,
    ) -> Optional[List[float]]:
        """Compute and persist the vector embedding for a specific product."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            logger.warning(f"Product with ID {product_id} not found.")
            return None

        try:
            vec = self.compute_image_embedding(product.image_path)
            product.embedding = vec
            db.commit()
            db.refresh(product)
            logger.info(f"Generated embedding for product ID {product.id} (SKU: {product.sku}, dim={len(vec)})")
            return vec
        except Exception as e:
            logger.error(f"Error computing embedding for product ID {product_id}: {e}")
            db.rollback()
            return None

    def backfill_all_products(self, db: Session, overwrite: bool = False) -> Dict[str, Any]:
        """Compute embeddings for all products in the database."""
        query = db.query(Product)
        if not overwrite:
            query = query.filter(Product.embedding.is_(None))

        products = query.all()
        success_count = 0
        error_items = []

        for p in products:
            vec = self.generate_and_store_product_embedding(db, p.id)
            if vec is not None:
                success_count += 1
            else:
                error_items.append({"id": p.id, "sku": p.sku, "image_path": p.image_path})

        return {
            "total_processed": len(products),
            "success_count": success_count,
            "errors": error_items,
        }


# Global singleton instance
embedding_service = ClipEmbeddingService()
