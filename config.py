import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL=os.getenv("DATABASE_URL")
CLIENT_ID=os.getenv("CLIENT_ID")
CLIENT_SECRET=os.getenv("CLIENT_SECRET")
JWT_SECRET=os.getenv("JWT_SECRET")
REDIRECT_URL = "https://portfoliobackend-vu5f.onrender.com/callback"
ADMIN_EMAIL=os.getenv("ADMIN_EMAIL")