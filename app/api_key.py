from fastapi import Header, HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("VERIFIER_API_KEY")

def verify_api_key(x_api_key: str = Header(...)):
    """Dependency to verify the API key in the request header."""
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key"
        )