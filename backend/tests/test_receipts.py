from types import SimpleNamespace

import pytest

from routers import receipts
from routers.receipts import ReceiptFields

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


@pytest.fixture
def fake_ai(monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "test-key")
    state = SimpleNamespace(calls=[], response=None)

    def parse(**kwargs):
        state.calls.append(kwargs)
        return state.response

    client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(parse=parse)))
    monkeypatch.setattr(receipts, "_client", lambda: client)

    def respond(stop_reason="end_turn", **fields):
        values = {"merchant": "Tim Hortons", "total": 6.25, "date": "2026-09-20",
                  "category": "Food & Dining", "summary": "Coffee and a bagel", **fields}
        state.response = SimpleNamespace(parsed_output=ReceiptFields(**values), stop_reason=stop_reason)
    state.respond = respond
    return state


def scan(client, auth, data=JPEG):
    return client.post("/receipts/scan", files={"file": ("r.jpg", data, "image/jpeg")}, headers=auth)


def test_disabled_without_api_key(client, auth):
    assert client.get("/receipts/enabled", headers=auth).json() == {"enabled": False}
    assert scan(client, auth).status_code == 503


def test_scan_maps_fields_and_sends_the_image(client, auth, fake_ai):
    fake_ai.respond()
    r = scan(client, auth)
    assert r.status_code == 200, r.text
    assert r.json() == {"title": "Tim Hortons", "amount": 6.25, "date": "2026-09-20",
                        "category": "Food & Dining", "notes": "Coffee and a bagel"}

    call = fake_ai.calls[0]
    assert call["model"] == receipts.MODEL
    assert call["output_format"] is ReceiptFields
    image = call["messages"][0]["content"][0]
    assert image["type"] == "image" and image["source"]["media_type"] == "image/jpeg"


def test_unreadable_date_becomes_empty(client, auth, fake_ai):
    fake_ai.respond(date="Sept 20th")
    assert scan(client, auth).json()["date"] is None


def test_not_a_receipt_or_refused(client, auth, fake_ai):
    fake_ai.respond(total=0)
    assert scan(client, auth).status_code == 422
    fake_ai.respond(stop_reason="refusal")
    assert scan(client, auth).status_code == 422


def test_rejects_non_images_and_large_files(client, auth, fake_ai):
    assert scan(client, auth, data=b"%PDF-1.4 not an image").status_code == 415
    assert scan(client, auth, data=JPEG + b"\x00" * (5 * 1024 * 1024)).status_code == 413
    assert fake_ai.calls == []


def test_sniff_image_type():
    assert receipts.sniff_image_type(b"\x89PNG\r\n\x1a\n...") == "image/png"
    assert receipts.sniff_image_type(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert receipts.sniff_image_type(b"GIF89a...") == "image/gif"
    assert receipts.sniff_image_type(b"hello") is None
