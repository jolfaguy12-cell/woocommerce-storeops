from fastapi import APIRouter

router = APIRouter()


@router.post("/telegram/test")
def send_test_message() -> dict[str, str]:
    return {"status": "queued", "message": "Telegram test message will be handled by the Core Server worker"}
