"""Temporary endpoint to upload a DB file directly to the volume."""
import os
import shutil
from fastapi import APIRouter, UploadFile, File, Header, HTTPException

router = APIRouter(prefix="/api/admin", tags=["admin"])

UPLOAD_SECRET = os.environ.get("DB_UPLOAD_SECRET", "")


@router.post("/upload-db")
async def upload_db(
    file: UploadFile = File(...),
    x_upload_secret: str = Header(...),
):
    if not UPLOAD_SECRET or x_upload_secret != UPLOAD_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    db_path = os.environ.get("REEPO_DB_PATH", "/data/reepo.db")
    tmp_path = db_path + ".uploading"

    with open(tmp_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    size = os.path.getsize(tmp_path)
    shutil.move(tmp_path, db_path)

    return {"status": "ok", "size": size, "path": db_path}
