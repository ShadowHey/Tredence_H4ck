import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import settings

def save_uploaded_image(file: UploadFile, subfolder: str = "products") -> str:
    """
    Validates and saves an uploaded image file into the configured uploads directory.
    Returns the relative path e.g. 'uploads/products/<unique_name>.ext'.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")
    
    # Check MIME type
    content_type = file.content_type
    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{content_type}'. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )
    
    # Determine extension
    ext = Path(file.filename).suffix.lower()
    if not ext:
        if content_type == "image/jpeg":
            ext = ".jpg"
        elif content_type == "image/png":
            ext = ".png"
        elif content_type == "image/webp":
            ext = ".webp"
        elif content_type == "image/svg+xml":
            ext = ".svg"
        else:
            ext = ".png"
            
    # Destination directory
    target_dir = settings.UPLOADS_DIR / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = target_dir / unique_filename
    
    # Stream and enforce max size
    size = 0
    with open(dest_path, "wb") as buffer:
        while chunk := file.file.read(8192):
            size += len(chunk)
            if size > settings.MAX_UPLOAD_SIZE_BYTES:
                buffer.close()
                if dest_path.exists():
                    os.remove(dest_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB."
                )
            buffer.write(chunk)
            
    # Return relative path
    return f"uploads/{subfolder}/{unique_filename}"
