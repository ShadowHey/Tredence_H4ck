#!/usr/bin/env python3
"""CLI tool for direct SQLite database inspection, verification, and testing of CLIP product embeddings."""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from app.db.database import SessionLocal, init_db
from app.db.models import Product
from app.services.embedding_service import embedding_service
from app.services import product_service
from app.api.schemas.product import ProductCreate


def list_products_table() -> None:
    """Print all products in the database with their embedding status and dimensions."""
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.id.asc()).all()
        print("\n" + "=" * 90)
        print(f"📦 ShelfSense AI — Product Catalog Vector Embeddings ({len(products)} products)")
        print("=" * 90)
        print(f"{'ID':<4} | {'SKU':<20} | {'Name':<24} | {'Category':<12} | {'Dim':<5} | {'Embedding Preview'}")
        print("-" * 90)
        
        embedded_count = 0
        for p in products:
            emb = p.embedding
            if emb and isinstance(emb, list):
                embedded_count += 1
                dim_str = str(len(emb))
                preview = "[" + ", ".join(f"{x:.4f}" for x in emb[:4]) + ", ...]"
            else:
                dim_str = "None"
                preview = "❌ Not generated"
            
            print(f"{p.id:<4} | {p.sku:<20} | {p.name[:23]:<24} | {(p.category or 'General')[:11]:<12} | {dim_str:<5} | {preview}")
        
        print("-" * 90)
        print(f"Total: {len(products)} products | With Embedding: {embedded_count}/{len(products)} ({embedded_count/max(1,len(products))*100:.1f}%)")
        print("=" * 90 + "\n")
    finally:
        db.close()


def backfill_all() -> None:
    """Compute and store embeddings for all products in the database."""
    db = SessionLocal()
    try:
        print("\n⚙ Starting bulk embedding backfill for catalog...")
        init_db()
        summary = embedding_service.backfill_all_products(db, overwrite=True)
        print(f"✔ Backfill complete: {summary['success_count']} of {summary['total_processed']} products embedded.")
        if summary["errors"]:
            print(f"⚠ Errors encountered ({len(summary['errors'])}):")
            for err in summary["errors"]:
                print(f"  - Product ID {err['id']} (SKU: {err['sku']}): {err['image_path']}")
        list_products_table()
    finally:
        db.close()


def compare_two_products(id_a: int, id_b: int) -> None:
    """Compare two products in the database and display cosine similarity."""
    db = SessionLocal()
    try:
        p_a = db.query(Product).filter(Product.id == id_a).first()
        p_b = db.query(Product).filter(Product.id == id_b).first()
        if not p_a:
            print(f"❌ Product with ID {id_a} not found.")
            return
        if not p_b:
            print(f"❌ Product with ID {id_b} not found.")
            return

        emb_a = p_a.embedding or embedding_service.generate_and_store_product_embedding(db, p_a.id)
        emb_b = p_b.embedding or embedding_service.generate_and_store_product_embedding(db, p_b.id)

        if not emb_a or not emb_b:
            print("❌ Could not obtain embeddings for comparison.")
            return

        sim = embedding_service.cosine_similarity(emb_a, emb_b)
        print("\n" + "=" * 70)
        print("🔍 Pairwise Vector Similarity Comparison")
        print("=" * 70)
        print(f"Product A: [#{p_a.id}] {p_a.name} (SKU: {p_a.sku}, Category: {p_a.category})")
        print(f"Product B: [#{p_b.id}] {p_b.name} (SKU: {p_b.sku}, Category: {p_b.category})")
        print(f"Image A  : {p_a.image_path}")
        print(f"Image B  : {p_b.image_path}")
        print("-" * 70)
        print(f"Cosine Similarity : {sim:.6f}")
        print(f"Percentage Match  : {sim * 100:.2f}%")
        print("=" * 70 + "\n")
    finally:
        db.close()


def run_identical_copy_test(target_id: Optional[int] = None) -> bool:
    """Take an existing product, create a duplicate with the same image, and verify similarity == 1.0000."""
    db = SessionLocal()
    try:
        init_db()
        # Find target product
        if target_id is not None:
            original = db.query(Product).filter(Product.id == target_id).first()
        else:
            original = db.query(Product).first()

        if not original:
            print("❌ No products found in database to test copy.")
            return False

        print("\n" + "=" * 75)
        print(f"🧪 Running Duplicate Copy Embedding Test on Product #{original.id}")
        print("=" * 75)
        print(f"Original Product : {original.name} (SKU: {original.sku})")
        print(f"Original Image   : {original.image_path}")

        # Ensure original has embedding
        orig_emb = original.embedding
        if not orig_emb:
            print("▶ Computing original product embedding...")
            orig_emb = embedding_service.generate_and_store_product_embedding(db, original.id)
            if not orig_emb:
                print("❌ Failed to generate embedding for original product.")
                return False

        # Create identical copy
        copy_sku = f"{original.sku}_COPY_{int(time.time())}"
        print(f"\n▶ Adding identical product copy with SKU: {copy_sku}...")
        product_in = ProductCreate(
            sku=copy_sku,
            name=f"{original.name} (Duplicate Copy)",
            category=original.category,
            description=f"Automated test copy of {original.name} with identical image.",
            price=original.price,
            currency=original.currency,
            width_cm=original.width_cm,
            height_cm=original.height_cm,
            depth_cm=original.depth_cm,
            image_path=original.image_path,
            is_sample=False,
        )

        copy_product = product_service.create_product(db, product_in)
        print(f"✔ Product created with ID #{copy_product.id}.")

        # Retrieve copy's embedding
        copy_emb = copy_product.embedding
        if not copy_emb:
            print("▶ Triggering embedding computation for copy...")
            copy_emb = embedding_service.generate_and_store_product_embedding(db, copy_product.id)

        if not copy_emb:
            print("❌ Copy embedding was not generated!")
            return False

        print(f"✔ Copy embedding computed: {len(copy_emb)} dimensions.")

        # Compare original and copy
        sim = embedding_service.cosine_similarity(orig_emb, copy_emb)
        print("\n" + "-" * 75)
        print(f"Original Vector Preview : [{', '.join(f'{x:.4f}' for x in orig_emb[:4])}, ...]")
        print(f"Copy Vector Preview     : [{', '.join(f'{x:.4f}' for x in copy_emb[:4])}, ...]")
        print(f"Cosine Similarity       : {sim:.8f}")
        print(f"Similarity Percentage   : {sim * 100:.4f}%")
        print("-" * 75)

        is_identical = sim >= 0.9999
        if is_identical:
            print("✅ TEST PASSED: Duplicate product copy returned the exact same vector embedding!")
        else:
            print(f"❌ TEST FAILED: Cosine similarity {sim} is less than 0.9999")

        print("=" * 75 + "\n")
        return is_identical
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="ShelfSense AI — Product Vector Embeddings Inspector")
    parser.add_argument("--list", action="store_true", help="List all products and their embedding status")
    parser.add_argument("--backfill", action="store_true", help="Generate embeddings for all products in database")
    parser.add_argument("--compare", nargs=2, type=int, metavar=("ID1", "ID2"), help="Compare cosine similarity of two product IDs")
    parser.add_argument("--test-copy", type=int, nargs="?", const=1, metavar="PRODUCT_ID", help="Add an identical product copy and test similarity == 1.0000")

    args = parser.parse_args()

    init_db()

    if args.list:
        list_products_table()
    elif args.backfill:
        backfill_all()
    elif args.compare:
        compare_two_products(args.compare[0], args.compare[1])
    elif args.test_copy is not None:
        run_identical_copy_test(args.test_copy)
    else:
        # Default action: list products
        list_products_table()


if __name__ == "__main__":
    main()
