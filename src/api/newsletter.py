"""Reepo API — newsletter routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class SubscribeRequest(BaseModel):
    email: str


@router.post("/api/newsletter/subscribe")
def newsletter_subscribe(body: SubscribeRequest):
    from src.server import get_db_path
    from src.monetization.newsletter import subscribe

    db_path = get_db_path()
    success = subscribe(body.email, path=db_path)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid email or already subscribed")
    return {"status": "subscribed", "email": body.email}


@router.post("/api/newsletter/unsubscribe")
def newsletter_unsubscribe(body: SubscribeRequest):
    from src.server import get_db_path
    from src.monetization.newsletter import unsubscribe

    db_path = get_db_path()
    removed = unsubscribe(body.email, path=db_path)
    if not removed:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"status": "unsubscribed"}


@router.get("/api/newsletter/latest")
def newsletter_latest():
    from src.server import get_db_path
    from src.monetization.newsletter import get_latest_newsletter

    db_path = get_db_path()
    return get_latest_newsletter(path=db_path)
