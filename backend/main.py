"""
CrisisMind - Multi-Crisis AI Operations Platform Backend
FastAPI + WebSockets + NetworkX + Scikit-Learn Risk Engine
"""
import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional


def _load_env():
    """Tiny .env loader (no extra dependency)."""
    f = Path(__file__).resolve().parent / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from algorithms.networkx_routing import calculate_dynamic_routes
from algorithms.risk_engine import simulate_what_if
from database import database as db

@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    print(f"✓ CrisisMind SQL database ready at {db.DB_PATH}")
    yield


app = FastAPI(
    title="CrisisMind Operations API",
    description="Multi-Crisis Decision & Route Intelligence Engine",
    version="2.5.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WhatIfRequest(BaseModel):
    scenario_id: str
    close_route_a: bool = False
    deploy_f02: bool = False
    pre_alert_hospital_b: bool = False
    open_shelter_2: bool = False
    evacuate_sector_4: bool = False

class RegisterReq(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=30)
    role: str = "operator"
    city: Optional[str] = Field(default=None, max_length=80)


class ProfileReq(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    phone: Optional[str] = Field(default=None, max_length=30)
    city: Optional[str] = Field(default=None, max_length=80)
    address: Optional[str] = Field(default=None, max_length=300)
    bloodGroup: Optional[str] = Field(default=None, max_length=5)
    emergencyContactName: Optional[str] = Field(default=None, max_length=80)
    emergencyContactPhone: Optional[str] = Field(default=None, max_length=30)


class LoginReq(BaseModel):
    email: str
    password: str


class ReportReq(BaseModel):
    category: str = Field(pattern="^(fire|flood|accident|chemical|crowd|storm|other)$")
    title: str = Field(min_length=3, max_length=140)
    description: Optional[str] = Field(default=None, max_length=2000)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    address: Optional[str] = Field(default=None, max_length=300)


class ActionReq(BaseModel):
    action: str = Field(min_length=1, max_length=200)
    scenario: str = "fire"
    payload: Optional[dict] = None


def _token(authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def optional_user(authorization: Optional[str] = Header(default=None)):
    return db.get_user_by_token(_token(authorization))


def required_user(user=Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Please sign in first")
    return user


@app.post("/api/auth/register")
def register(req: RegisterReq):
    role = req.role if req.role in ("operator", "commander", "citizen") else "operator"
    user = db.create_user(req.name, req.email, req.password, req.phone, role, req.city)
    if not user:
        raise HTTPException(status_code=409, detail="This email is already registered")
    return {"token": db.create_session(user["id"]), "user": user}


@app.post("/api/auth/login")
def login(req: LoginReq):
    user = db.verify_login(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return {"token": db.create_session(user["id"]), "user": user}


@app.get("/api/auth/me")
def me(user=Depends(required_user)):
    return {"user": user}


@app.put("/api/auth/profile")
def update_profile(req: ProfileReq, user=Depends(required_user)):
    return {"user": db.update_profile(user["id"], req.model_dump(exclude_unset=True))}


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(default=None)):
    t = _token(authorization)
    if t:
        db.delete_session(t)
    return {"ok": True}


@app.post("/api/reports")
def create_report(req: ReportReq, user=Depends(required_user)):
    report = db.add_report(user["id"], req.model_dump())
    db.log_action(user["id"], req.category, f"Reported incident: {req.title}", {"reportId": report["id"]})
    return report


@app.get("/api/reports")
def get_reports(mine: bool = False, user=Depends(optional_user)):
    if mine and not user:
        raise HTTPException(status_code=401, detail="Please sign in first")
    return db.list_reports(user["id"] if mine else None)


@app.delete("/api/reports/{report_id}")
def remove_report(report_id: int, user=Depends(required_user)):
    if not db.delete_report(report_id, user["id"]):
        raise HTTPException(status_code=404, detail="Report not found")
    return {"ok": True}


@app.post("/api/actions")
def post_action(req: ActionReq, user=Depends(optional_user)):
    db.log_action(user["id"] if user else None, req.scenario, req.action, req.payload)
    return {"ok": True}


@app.get("/api/actions")
def get_actions(user=Depends(required_user)):
    return db.list_actions(user["id"])


@app.get("/api/simulations")
def get_simulations(user=Depends(required_user)):
    return db.list_simulations(user["id"])


@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {
        "status": "OPERATIONAL",
        "system": "CrisisMind Decision Engine",
        "version": "2.5.0",
        "endpoints": [
            "/api/crisis/current",
            "/api/routes/intelligence",
            "/api/cascade/graph",
            "/api/what-if/simulate",
            "/api/fleet/status",
            "/api/hospitals/capacity",
            "/api/integrity/ledger",
            "/api/auth/register", "/api/auth/login", "/api/reports", "/api/actions",
            "/docs"
        ]
    }

@app.get("/api/crisis/current")
def get_current_crisis(scenario: str = "fire"):
    return db.get_scenario_data(scenario)

@app.get("/api/routes/intelligence")
def get_route_intelligence(
    scenario: str = "fire",
    time_offset: int = Query(0, description="Minutes from NOW: 0, 15, 30, 45, 60")
):
    routes = calculate_dynamic_routes(scenario, time_offset)
    return {
        "time_offset_min": time_offset,
        "recommended_route": routes["recommended"],
        "avoid_route": routes["avoid"],
        "backup_route": routes["backup"],
        "why_explanation": routes["why_explanation"],
        "expected_blockage_time_min": routes.get("blockage_time", 18)
    }

@app.post("/api/what-if/simulate")
def run_simulation(req: WhatIfRequest, user=Depends(optional_user)):
    actions = {
        "close_route_a": req.close_route_a,
        "deploy_f02": req.deploy_f02,
        "pre_alert_hospital_b": req.pre_alert_hospital_b,
        "open_shelter_2": req.open_shelter_2,
        "evacuate_sector_4": req.evacuate_sector_4,
    }
    result = simulate_what_if(scenario_id=req.scenario_id, actions=actions)
    db.save_simulation(user["id"] if user else None, req.scenario_id, actions, result)
    return result

@app.get("/api/cascade/graph")
def get_cascade_graph(scenario: str = "fire"):
    return db.get_cascade_nodes(scenario)

@app.get("/api/integrity/ledger")
def get_integrity_ledger():
    return db.get_ledger_records()

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        t = 0
        while True:
            t += 1
            payload = {
                "timestamp": time.strftime("%H:%M:%S UTC"),
                "tick": t,
                "air_quality_index": 380 + (t % 15) * 4,
                "wind_speed_kmh": 18.4 + (t % 5) * 0.8,
                "flame_perimeter_meters": 450 + t * 5,
                "route_a_visibility_meters": max(10, 80 - t * 6)
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        print("Client disconnected from telemetry stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=True)
