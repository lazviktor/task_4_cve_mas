
from fastapi import FastAPI, Request, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
import json, os, secrets

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True)
    token = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, index=True)
    payload = Column(Text)        # JSON report
    analysis = Column(Text)       # optional LLM analysis text
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task 4 Manager", version="0.2.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RegisterRequest(BaseModel):
    hostname: str

@app.post("/api/v1/agents/register")
async def register_agent(req: RegisterRequest, db: Session = Depends(get_db)):
    token = secrets.token_hex(16)
    existing = db.query(Agent).filter(Agent.hostname == req.hostname).first()
    if existing:
        existing.token = token
        db.add(existing); db.commit()
        return {"hostname": req.hostname, "token": token}
    agent = Agent(hostname=req.hostname, token=token)
    db.add(agent); db.commit()
    return {"hostname": req.hostname, "token": token}

def auth_agent(db: Session, auth_header: Optional[str]) -> str:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth_header.split(" ", 1)[1]
    agent = db.query(Agent).filter(Agent.token == token).first()
    if not agent:
        raise HTTPException(status_code=403, detail="Invalid token")
    return agent.hostname

@app.post("/api/v1/findings")
async def receive_findings(request: Request, db: Session = Depends(get_db), authorization: Optional[str] = Header(None)):
    hostname = auth_agent(db, authorization)
    body = await request.json()
    rec = Finding(hostname=hostname, payload=json.dumps(body))
    db.add(rec); db.commit()
    return {"status": "ok", "report_id": rec.id}

class AnalysisBody(BaseModel):
    report_id: int
    text: str

@app.post("/api/v1/analysis")
async def upload_analysis(body: AnalysisBody, db: Session = Depends(get_db)):
    rec = db.query(Finding).filter(Finding.id == body.report_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Report not found")
    rec.analysis = body.text
    db.add(rec); db.commit()
    return {"status": "ok"}

@app.get("/api/v1/reports")
async def list_reports(db: Session = Depends(get_db), hostname: Optional[str] = None):
    q = db.query(Finding)
    if hostname:
        q = q.filter(Finding.hostname == hostname)
    rows = q.order_by(Finding.created_at.desc()).limit(100).all()
    return [{"id": r.id, "hostname": r.hostname, "created_at": r.created_at.isoformat()} for r in rows]

@app.get("/api/v1/reports/{report_id}")
async def get_report(report_id: int, db: Session = Depends(get_db)):
    r = db.query(Finding).filter(Finding.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return {"json": json.loads(r.payload), "analysis": r.analysis}

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    rows = db.query(Finding).order_by(Finding.created_at.desc()).limit(50).all()
    parsed = []
    totals = {"count": 0}
    for r in rows:
        data = json.loads(r.payload)
        count = len(data.get("report", {}).get("os", [])) + len(data.get("report", {}).get("pip", []))
        totals["count"] += count
        parsed.append({
            "id": r.id,
            "hostname": r.hostname,
            "created_at": r.created_at,
            "count": count,
            "os_count": len(data.get("report", {}).get("os", [])),
            "pip_count": len(data.get("report", {}).get("pip", [])),
            "has_analysis": bool(r.analysis and r.analysis.strip())
        })
    return templates.TemplateResponse("dashboard.html", {"request": request, "rows": parsed, "totals": totals})
