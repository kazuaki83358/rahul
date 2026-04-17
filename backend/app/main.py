# path: backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import asyncio, json, logging, os

from app.core.config import settings
from app.routers import auth, query, admin
from app.models.base import Base, engine
from app.utils.seed import seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables and seed data automatically on startup
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    seed()
except Exception as e:
    logger.error(f"Startup error: {e}")

app = FastAPI(
    title="Multimodal RAG Code Assistant",
    version="1.0.0",
)

# Set up templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Simplified for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(query.router, prefix="/api/v1/query", tags=["query"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

# Template routes
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self.active[session_id] = ws

    def disconnect(self, session_id: str):
        self.active.pop(session_id, None)

    async def send(self, session_id: str, data: dict):
        ws = self.active.get(session_id)
        if ws:
            await ws.send_text(json.dumps(data))

manager = ConnectionManager()
app.state.ws_manager = manager

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            from app.agents.crew import run_crew_streaming
            async for chunk in run_crew_streaming(payload, session_id):
                await manager.send(session_id, chunk)
    except WebSocketDisconnect:
        manager.disconnect(session_id)

@app.get("/health")
async def health():
    return {"status": "ok"}
