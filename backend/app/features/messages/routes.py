from typing import List, Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from . import schemas, service
from app.core.database import get_db
from app.core.security import require_verified_member
from app.features.auth.models import User

router = APIRouter(
    prefix="/api/messages", 
    tags=["Messages"],
    dependencies=[Depends(require_verified_member)]
)

Database = Annotated[Session, Depends(get_db)]
Member = Annotated[User, Depends(require_verified_member)]

@router.get("/inbox", response_model=List[schemas.InboxItem])
def get_inbox(database: Database, user: Member):
    return service.get_inbox(db=database, user_id=user.id)

@router.get("/{other_user_id}", response_model=List[schemas.MessageResponse])
def read_chat_history(other_user_id: str, database: Database, user: Member):
    return service.get_chat_history(
        db=database, 
        current_user_id=user.id, 
        other_user_id=other_user_id
    )

@router.post("/", response_model=schemas.MessageResponse)
def send_message(message: schemas.MessageCreate, database: Database, user: Member):
    return service.send_message(
        db=database, 
        message=message, 
        sender_id=user.id
    )