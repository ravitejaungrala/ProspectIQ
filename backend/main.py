from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import connect_db, close_db
from config import get_settings
from routers import campaigns, leads, outreach, replies, dashboard, analytics, agents

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="ProspectIQ API",
    description="AI-powered lead generation and outreach platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(campaigns.router)
app.include_router(leads.router)
app.include_router(outreach.router)
app.include_router(replies.router)
app.include_router(analytics.router)
app.include_router(agents.router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ProspectIQ API"}
