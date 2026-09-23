import base64
import os
from datetime import date
from typing import Literal, Optional

import anthropic
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from auth import get_current_user
from categories import CATEGORIES
import models, schemas

router = APIRouter(prefix="/receipts", tags=["receipts"])

MODEL = "claude-opus-5"
MAX_BYTES = 5 * 1024 * 1024
MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}

PROMPT = f"""Read this receipt and extract the purchase details.

- merchant: the store or business name, cleaned up (e.g. "Tim Hortons", not "TIM HORTONS #4521").
- total: the final amount paid, including tax and tip. Use the grand total, not the subtotal.
- date: the purchase date as YYYY-MM-DD, or null if it isn't visible.
- category: the best fit from this list: {", ".join(CATEGORIES)}.
- summary: a short note of what was bought (e.g. "2 coffees, bagel"), max 100 characters.

If the image is not a receipt, set total to 0."""


class ReceiptFields(BaseModel):
    merchant: str
    total: float
    date: Optional[str] = Field(description="YYYY-MM-DD or null")
    category: Literal[tuple(CATEGORIES)]
    summary: str


def sniff_image_type(data: bytes) -> str | None:
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return next((mime for magic, mime in MAGIC.items() if data.startswith(magic)), None)


def _client() -> anthropic.Anthropic | None:
    key = os.getenv("AI_API_KEY")
    if not key:
        return None
    return anthropic.Anthropic(api_key=key, timeout=60.0)


@router.get("/enabled")
def enabled() -> dict:
    return {"enabled": bool(os.getenv("AI_API_KEY"))}


@router.post("/scan", response_model=schemas.ReceiptScan)
def scan(file: UploadFile = File(...), user: models.User = Depends(get_current_user)):
    client = _client()
    if client is None:
        raise HTTPException(status_code=503, detail="Receipt scanning isn't set up. Add AI_API_KEY to .env.")

    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image is larger than 5 MB.")
    media_type = sniff_image_type(data)
    if media_type is None:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, GIF or WebP photo.")

    try:
        response = client.beta.messages.parse(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_format=ReceiptFields,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": media_type,
                        "data": base64.standard_b64encode(data).decode(),
                    }},
                    {"type": "text", "text": PROMPT},
                ],
            }],
        )
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=502, detail="The AI API key is invalid.")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Too many scans right now. Try again in a minute.")
    except (anthropic.APIStatusError, anthropic.APIConnectionError):
        raise HTTPException(status_code=502, detail="Couldn't reach the AI service. Try again.")

    fields = response.parsed_output
    if response.stop_reason == "refusal" or fields is None:
        raise HTTPException(status_code=422, detail="Couldn't read this receipt. Try a clearer photo.")
    if fields.total <= 0:
        raise HTTPException(status_code=422, detail="That doesn't look like a receipt.")

    try:
        purchase_date = date.fromisoformat(fields.date) if fields.date else None
    except ValueError:
        purchase_date = None

    return schemas.ReceiptScan(
        title=fields.merchant[:200],
        amount=round(fields.total, 2),
        date=purchase_date,
        category=fields.category,
        notes=fields.summary[:1000],
    )
