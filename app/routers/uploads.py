from fastapi import APIRouter, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..models import FormFileUpload
from ..database import SessionLocal
import os, uuid

router = APIRouter(prefix="/api/forms", tags=["Uploads"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-file")
async def upload_file(
    formId: str = Form(...),
    fileType: str = Form(...),
    file: UploadFile = File(...)
):
    file_ext = file.filename.split(".")[-1]
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    db: Session = SessionLocal()
    file_record = FormFileUpload(
        form_id=formId,
        filename=file.filename,
        file_extension=file_ext,
        file_type=fileType,
        status="New",
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    db.close()

    return {
        "message": "File uploaded successfully",
        "fileId": file_record.id,
        "filename": file.filename,
        "fileType": fileType,
    }

@router.get("/upload-info")
async def get_upload_info(formId: str, uploadIds: str):
    db: Session = SessionLocal()
    upload_ids_list = uploadIds.split(",")
    files = db.query(FormFileUpload).filter(
        FormFileUpload.form_id == formId,
        FormFileUpload.id.in_(upload_ids_list)
    ).all()

    print(files)
    db.close()

    return {
        "formId": formId,
        "files": {
            file.id: {
                "filename": file.filename,
                "fileType": file.file_type,
                "fileExtension": file.file_extension,
            }
            for file in files
        },
    }
