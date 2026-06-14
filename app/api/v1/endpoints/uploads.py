from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.models import Upload
from app.schemas.schemas import UploadOut
from app.services.pipeline_service import process_upload, save_upload_file

router = APIRouter(prefix="/uploads", tags=["Upload & Pipeline"])


@router.post("", response_model=UploadOut, status_code=202)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Hanya file .csv yang diizinkan")

    filename, file_path = await save_upload_file(file, current_user.id)

    upload = Upload(
        user_id=current_user.id,
        filename=filename,
        file_path=file_path,
        status="pending",
    )
    db.add(upload)
    await db.flush()

    # Jalankan pipeline di background agar response langsung kembali
    background_tasks.add_task(process_upload, upload.id, file_path)


    return upload


@router.get("", response_model=list[UploadOut])
async def list_uploads(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Upload)
        .where(Upload.user_id == current_user.id)
        .order_by(Upload.uploaded_at.desc())
    )
    return result.scalars().all()


@router.get("/{upload_id}", response_model=UploadOut)
async def get_upload(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    upload = await db.get(Upload, upload_id)
    if not upload or upload.user_id != current_user.id:
        raise HTTPException(404, "Upload tidak ditemukan")
    return upload


@router.delete("/{upload_id}", status_code=204)
async def delete_upload(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    upload = await db.get(Upload, upload_id)
    if not upload or upload.user_id != current_user.id:
        raise HTTPException(404, "Upload tidak ditemukan")
    await db.delete(upload)
    await db.commit()
