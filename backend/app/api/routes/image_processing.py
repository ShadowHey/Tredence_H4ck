from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.schemas.image_processing import (
    ExportRequest,
    InputImageResponse,
    ProcessImageRequest,
    ProcessedOutputResponse,
    CutoutsResponse,
    OutputAnalysisResponse,
)
from app.db.database import get_db
from app.services import image_processing_service as service
from app.services import cutout_service

router = APIRouter(tags=["Image Processing"])


@router.post("/input-images", response_model=list[InputImageResponse], status_code=201)
def upload_input_images(files: Annotated[list[UploadFile], File(...)], db: Session = Depends(get_db)):
    return service.create_input_images(db, files)


@router.get("/input-images", response_model=list[InputImageResponse])
def get_input_images(db: Session = Depends(get_db)):
    return service.list_input_images(db)


@router.post("/input-images/{input_image_id}/process", response_model=InputImageResponse)
def process_input_image(input_image_id: int, target: ProcessImageRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    item = service.queue_input_image(db, input_image_id, target.planogram_id, target.shelf_id)
    background_tasks.add_task(service.process_pending_jobs)
    return item


@router.delete("/input-images/{input_image_id}")
def remove_input_image(input_image_id: int, db: Session = Depends(get_db)):
    service.delete_input_image(db, input_image_id)
    return {"message": "Input image and any derived output were deleted."}


@router.get("/outputs", response_model=list[ProcessedOutputResponse])
def get_outputs(db: Session = Depends(get_db)):
    return service.list_outputs(db)


@router.post("/outputs/export")
def export_outputs(request: ExportRequest, db: Session = Depends(get_db)):
    archive = service.build_export_zip(db, request.output_ids)
    return StreamingResponse(archive, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=shelfsense-outputs.zip"})


@router.delete("/outputs")
def remove_outputs(request: ExportRequest, db: Session = Depends(get_db)):
    count = service.delete_outputs(db, request.output_ids)
    return {"message": f"Deleted {count} processed output(s)."}


@router.get("/outputs/{output_id}/cutouts", response_model=CutoutsResponse)
def get_output_cutouts(output_id: int, db: Session = Depends(get_db)):
    return cutout_service.get_output_cutouts(db, output_id)


@router.get("/outputs/{output_id}/analysis", response_model=OutputAnalysisResponse)
def get_output_analysis(output_id: int, db: Session = Depends(get_db)):
    return cutout_service.get_output_analysis(db, output_id)


@router.post("/outputs/{output_id}/analyze", response_model=OutputAnalysisResponse)
def analyze_output(output_id: int, db: Session = Depends(get_db)):
    return cutout_service.extract_cutouts_and_analyze(db, output_id, force_recompute=True)

