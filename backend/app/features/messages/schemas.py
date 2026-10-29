from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    receiver_id: str
    content: str

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    sender_id: str
    timestamp: datetime
    is_read: bool

    class Config:
        from_attributes = True

class InboxItem(BaseModel):
    user_id: str
    username: str
    last_message: str
    timestamp: datetime
    unread_count: int