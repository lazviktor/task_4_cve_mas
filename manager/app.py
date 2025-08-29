from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid

from .database import SessionLocal, engine
from . import models

# Создаём таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MAS Task 4 — Manager")

templates = Jinja2Templates(directory="manager/templates")

# ------------------------
# Pydantic-схемы
# ------------------------

class ReportCreate(BaseModel):
    hostname: str
    vulnerabilities: Optional[str] = None

class ReportOut(BaseModel):
    id: int
    hostname: str
    vulnerabilities: Optional[str] = None
    analysis: Optional[str] = None

    class Config:
        from_attributes = True   # для Pydantic v2

class AnalysisIn(BaseModel):
    analysis: str

class AgentRegisterOut(BaseModel):
    token: str

# ------------------------
# DB Session dependency
# ------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------
# Эндпоинты API
# ------------------------

@app.post("/api/v1/agents/register", response_model=AgentRegisterOut)
def register_agent():
    # Здесь можно сохранять агента в БД, но пока просто генерим токен
    token = uuid.uuid4().hex
    return {"token": token}

@app.post("/api/v1/reports", response_model=ReportOut)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    db_report = models.Report(
        hostname=report.hostname,
        vulnerabilities=report.vulnerabilities
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

@app.get("/api/v1/reports", response_model=List[ReportOut])
def list_reports(db: Session = Depends(get_db)):
    return db.query(models.Report).all()

@app.post("/api/v1/reports/{report_id}/analysis", response_model=ReportOut)
def add_analysis(report_id: int, analysis: AnalysisIn, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.analysis = analysis.analysis
    db.commit()
    db.refresh(report)
    return report

# ------------------------
# Дашборд (HTML)
# ------------------------

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    reports = db.query(models.Report).all()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "reports": reports}
    )
