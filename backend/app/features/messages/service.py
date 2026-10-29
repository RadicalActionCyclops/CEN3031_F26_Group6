from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from .models import Message
from .schemas import MessageCreate
from app.features.auth.models import User
from app.features.profiles.models import Profile

def send_message(db: Session, message: MessageCreate, sender_id: str):
    db_message = Message(
        sender_id=sender_id,
        receiver_id=message.receiver_id,
        content=message.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_history(db: Session, current_user_id: str, other_user_id: str):
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user_id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == current_user_id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    # Mark received messages as read
    unread_messages = [m for m in messages if m.receiver_id == current_user_id and not m.is_read]
    for msg in unread_messages:
        msg.is_read = True
    if unread_messages:
        db.commit()
        
    return messages

def get_inbox(db: Session, user_id: str):
    # FORCE the user_id to be a standard string so SQLite can match it
    user_id_str = str(user_id)
    
    # Fetch all messages where the user is involved
    messages = db.query(Message).filter(
        or_(Message.sender_id == user_id_str, Message.receiver_id == user_id_str)
    ).order_by(desc(Message.timestamp)).all()
    
    inbox_dict = {}
    
    for msg in messages:
        other_id = msg.receiver_id if msg.sender_id == user_id_str else msg.sender_id
        
        if other_id not in inbox_dict:
            # We now know the name lives in the User table!
            other_user = db.query(User).filter(User.id == other_id).first()
            
            # Grab the display_name. If missing, use email. If still missing, use "Member".
            if other_user and getattr(other_user, 'display_name', None):
                display_name = other_user.display_name
            elif other_user and getattr(other_user, 'email', None):
                display_name = other_user.email
            else:
                display_name = "Member"
            
            inbox_dict[other_id] = {
                "user_id": other_id,
                "username": display_name,
                "last_message": msg.content,
                "timestamp": msg.timestamp,
                "unread_count": 0 if msg.is_read or msg.sender_id == user_id_str else 1
            }
        else:
            if not msg.is_read and msg.receiver_id == user_id_str:
                inbox_dict[other_id]["unread_count"] += 1
                
    return list(inbox_dict.values())