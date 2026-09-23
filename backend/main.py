import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import auth, budgets, expenses, insights

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Management Platform API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, expenses, budgets, insights):
    app.include_router(r.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Expense Manager API"}
