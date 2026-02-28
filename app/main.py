from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="LLM Verifiability & Trust Layer",
    description="Middleware system for claim extraction and verifiability analysis",
    version="0.1.0"
)

@app.get("/")
def root():
    return {"message": "LLM Verifiability Trust Layer API is running"}