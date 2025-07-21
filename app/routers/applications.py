from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import desc 
from sqlalchemy.orm import Session
from app.schemas import ApplicationCreate, ApplicationResponse
from app.models import Application
from typing import List
from datetime import datetime
import json
from app.models import FormData, FormFileUpload
from app.utils import generate_next_id, get_db

router = APIRouter(prefix="/api/applications", tags=["Applications"])

def model_to_response(application: Application) -> ApplicationResponse:
    return ApplicationResponse(
        id=application.id,
        formId=application.form_id,
        providerId=application.provider_id,
        name=application.name,
        providerLastName=application.last_name,
        status=application.status,
        progress=application.progress,
        assignee=application.assignee,
        source=application.source,
        market=application.market,
        specialty=application.specialty,
        address=application.address,
        npi=application.npi,
        create_dt=application.create_dt,
        last_updt_dt=application.last_updt_dt
    )

@router.post("/", response_model=ApplicationResponse)
def create_application(app_data: ApplicationCreate, db: Session = Depends(get_db)):
    application_id = generate_next_id(db)
    application = Application(id=application_id, **app_data.dict(by_alias=False, exclude={"id"}))
    now = datetime.now()
    application.create_dt = now
    application.last_updt_dt = now
    db.add(application)
    db.commit()
    db.refresh(application)
    return model_to_response(application)

@router.get("/", response_model=List[ApplicationResponse])
def get_all_applications(db: Session = Depends(get_db)):
    applications = db.query(Application).order_by(desc(Application.create_dt)).all()
    if not applications:
        raise HTTPException(status_code=404, detail="No applications found")
    return [model_to_response(app) for app in applications]

@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application_by_id(app_id: str, db: Session = Depends(get_db)):
    application = db.query(Application).filter_by(id=app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return model_to_response(application)


@router.get("/aiissues/{app_id}")
def get_ai_issues(app_id: str, db: Session = Depends(get_db)):
    # Get application with form_id
    application = db.query(Application).filter_by(id=app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Get form data
    form_data = db.query(FormData).filter_by(form_id=application.form_id).first()
    if not form_data:
        raise HTTPException(status_code=404, detail="Form data not found")

    # Get related file upload with OCR data
    file_upload = db.query(FormFileUpload).filter_by(form_id=application.form_id).first()
    if not file_upload:
        raise HTTPException(status_code=404, detail="OCR/Match data not found")

    issues = []

    # ---------- 1. Parse JSON match ----------
    if file_upload.json_match:
        try:
            json_match_data = json.loads(file_upload.json_match)
            for field, data in json_match_data.items():
                if not data.get("match"):
                    issues.append({
                        "field": field.upper(),
                        "issue": f"{field.upper()} field mismatch.",
                        "confidence": float(data.get("extracted_confident_score", 0)),
                        "value": data.get("extracted"),
                        "reasoning": f"Extracted value '{data.get('extracted')}' does not match provided value '{data.get('provided')}'."
                    })
        except Exception:
            raise HTTPException(status_code=500, detail="Error parsing json_match")

    # # ---------- 2. Parse PDF Match ----------
    # if file_upload.pdf_match:
    #     try:
    #         pdf_data = json.loads(file_upload.pdf_match)
    #         if not pdf_data.get("match"):
    #             issues.append({
    #                 "field": "PDF Document",
    #                 "issue": "PDF and extracted layout mismatch.",
    #                 "confidence": float(pdf_data.get("confidance_score", 0)),
    #                 "value": "",
    #                 "reasoning": pdf_data.get("reason")
    #             })
    #     except Exception:
    #         raise HTTPException(status_code=500, detail="Error parsing pdf_match")

    # ---------- 3. Add mock/derived logic issues ----------
    # Example hardcoded issues — you can replace this with ML/validation logic later
    if form_data.npi == "0987654321":
        issues.append({
            "field": "NPI",
            "issue": "NPI number not found in national registry.",
            "confidence": 0.82,
            "value": form_data.npi,
            "reasoning": "The NPI provided did not return a valid result from the NPPES NPI Registry. This could be a typo or an inactive NPI."
        })

    issues.append({
        "field": "Address",
        "issue": "ZIP code mismatch with state.",
        "confidence": 0.95,
        "value": form_data.address,
        "reasoning": "The ZIP code 90210 belongs to California, which matches the provided state. However, cross-referencing with USPS database suggests a potential discrepancy in the street address format."
    })

    issues.append({
        "field": "CV/Resume",
        "issue": "Gap in employment history (3 months).",
        "confidence": 0.65,
        "value": "Missing: Jan 2020 - Mar 2020",
        "reasoning": "A 3-month gap was detected between two listed employment periods. This may require clarification from the provider."
    })

    return {"issues": issues}