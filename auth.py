from jose import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET=os.getenv("JWT_SECRET")
ALGORITHIM="HS256"

def create_access_token(data: dict, expires_at: timedelta=timedelta(hours=1)):
    to_encode=data.copy()
    expire=datetime.utcnow()+expires_at
    to_encode.update({"exp": expire})
    encoded_jwt=jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHIM)
    return encoded_jwt