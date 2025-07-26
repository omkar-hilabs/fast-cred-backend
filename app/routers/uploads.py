from fastapi import APIRouter, UploadFile, File, Form, Query
from typing import Optional
from sqlalchemy.orm import Session
from ..models import FormFileUpload, FormData, Application
from ..database import SessionLocal
import os
import ast

router = APIRouter(prefix="/api/forms", tags=["Uploads"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-file")
async def upload_file(
    formId: str = Form(...),
    fileType: str = Form(...),
    file: UploadFile = File(...)
):  
    filename_without_ext = ".".join(file.filename.split(".")[:-1])
    file_ext = file.filename.split(".")[-1]
    new_filename = f"{filename_without_ext}__{formId}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, new_filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    db: Session = SessionLocal()

    try:
        # 1. Mark previous file as replaced, if exists
        previous_record = db.query(FormFileUpload).filter(
            FormFileUpload.form_id == formId,
            FormFileUpload.file_type == fileType,
            FormFileUpload.status != "Replaced"
        ).first()  # optional: based on latest

        if previous_record:
            previous_record.status = "Replaced"
            db.flush()

        # 2. Insert new file record
        new_file_record = FormFileUpload(
            form_id=formId,
            filename=file.filename,
            file_extension=file_ext,
            file_type=fileType,
            status="New"
        )
        db.add(new_file_record)
        db.flush()

        # 3. Update reference in FormData
        form = db.query(FormData).filter(FormData.form_id == formId).first()
        if form:
            field_name = f"{fileType}_upload_id"
            setattr(form, field_name, new_file_record.id)

        db.commit()
        db.refresh(new_file_record)

        return {
            "message": "File uploaded successfully",
            "fileId": new_file_record.id,
            "filename": file.filename,
            "fileType": fileType,
        }

    finally:
        db.close()


def get_progress(type):
    if type == "npi":
        return 100
    elif type == "dl":
        return 90
    elif type == "degree":
        return 75
    elif type == "cv/resume":
        return 60
    

@router.get("/upload-info")
async def get_upload_info( uploadIds: str, formId: Optional[str] = Query(None),
    appId: Optional[str] = Query(None)):
    db: Session = SessionLocal()
    upload_ids_list = uploadIds.split(",")

    if appId:
        application = db.query(Application).filter(Application.id == appId).first()
        formId = application.form_id

    files = db.query(FormFileUpload).filter(
        FormFileUpload.form_id == formId,
        FormFileUpload.id.in_(upload_ids_list)
    ).all()
    db.close()

    return {
        "formId": formId,
        "files": {
            file.file_type: {
                "filename": file.filename,
                "fileType": file.file_type,
                "fileExtension": file.file_extension,
                "fileId": file.id,
                "status": file.status,
                "progress": get_progress(file.file_type),  # Assuming progress is 0 for new files
                "pdfMatch": ast.literal_eval(file.pdf_match) if file.pdf_match else {},
                "ocrData": ast.literal_eval(file.ocr_output) if file.ocr_output else {},
            }
            for file in files
        },
    }
