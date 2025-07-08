from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload
from dotenv import load_dotenv
import requests, os
from datetime import datetime, timedelta
from database import User, SessionLocal, Project, ProjectFile, UpdateProject
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URL, JWT_SECRET, ADMIN_EMAIL
from auth import create_access_token
from jose import jwt, jwk
from pathlib import Path
from crud import Update, Delete


app = FastAPI()
load_dotenv()

GOOGLE_URL="https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL="https://oauth2.googleapis.com/token"

FRONTEND_URL="http://localhost:5173/dashboard"
google_keys=requests.get("https://www.googleapis.com/oauth2/v3/certs").json()

UPLOAD_DIR=Path(__file__).resolve().parent /"uploads/project_"

#allow requests from frontend
app.add_middleware(
    CORSMiddleware, 
    allow_origins=['https://portfolio-frontend-gamma-peach.vercel.app', 'http://localhost:5173/'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#make sure the directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

#serve uploaded files
app.mount("/upload", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def home():
    return {"message": "FastApi is working"}

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get('/login')
def login():
    scope=f"openid%20email%20profile"
    auth_url=(
        f"{GOOGLE_URL}?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={REDIRECT_URL}"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
        )
    return RedirectResponse(auth_url)

@app.get("/logout")
def log_out():
    response=JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("access_token")
    return response

@app.get("/callback")
def callback(code:str, db:Session=Depends(get_db)):
    data={
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URL,
        "grant_type": "authorization_code"
    }
    token_response=requests.post(GOOGLE_TOKEN_URL, data=data)
    if token_response.status_code !=200:
        raise HTTPException(status_code=400, detail="Failed to fetch token")
    token_data=token_response.json()
    id_token=token_data.get("id_token")
    access_token=token_data.get("access_token")

    if not id_token:
        raise HTTPException(status_code=400, detail="Id Token not found")
    
    #verify the google token
    user_info=requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}").json()
    email=user_info["email"]
    username=user_info["name"]
    picture=user_info["picture"]

    if not email:
        raise HTTPException(status_code=400, detail="invalid token or user data")
    
    #add user to the data
    user=db.query(User).filter(User.email==email).first()
    if not user:
        user=User(email=email, username=username, picture=picture)
        db.add(user)
        db.commit()
        db.refresh(user)

    #create the JWT
    my_token=jwt.encode({
        "sub":user.id,
        "email":email,
        "exp":datetime.utcnow()+timedelta(days=7)
    },
    JWT_SECRET, algorithm="HS256"
    )
    #set the cookie with the access token
    response= RedirectResponse(url="http://localhost:5173/dashboard")
    #set the cookie with the access token
    response.set_cookie(
        key="access_token",
        value=my_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )
    
    return response

@app.get("/me")
def get_me(request: Request):
    token= request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail="Failed to fetch access token")
    if token:
        headers={"Authorization": f"Bearer {token}"}
        response=requests.get(FRONTEND_URL, headers=headers)
    else:
        raise HTTPException(status_code=401, detail="Access token has expired")
    
    if response.status_code !=200:
        raise HTTPException(status_code=400, detail="Failed to load page")
    
@app.get("/admin")
def is_admin(db:Session=Depends(get_db)):
    user=db.query(User).filter(User.email==ADMIN_EMAIL).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user:
        return {"is_admin": True}
    
@app.post("/upload")
async def upload_files(files: list[UploadFile]=File(...), title: str=Form(...), description: str=Form(...), db:Session=Depends(get_db)):
    
    project=Project(
        title= title,
        description=description,
        
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    folder_path= f"{UPLOAD_DIR}{project.id}"
    os.makedirs(folder_path, exist_ok=True)

    
    
    for file in files:
        file_path=os.path.join(folder_path, file.filename)
        print("Saving file to:", file_path)
        with open(file_path, "wb") as f:
            f.write(file.file.read())

    db.add(ProjectFile(filename=file.filename, path=file_path, project_id=project.id))
    db.commit()
    
    
    
    
    return {
        "message": "Project created at", "project_id":project.id
        }

@app.get("/projects")
def get_projects(db:Session=Depends(get_db)):
    return db.query(Project).options(joinedload(Project.files)).all()


@app.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
    "id": project.id,
    "name": project.title,
    "description": project.description,
    "files": [ {"id": f.id, "filename": f.filename} for f in project.files ]
}

@app.put("/projects/{project_id}")
def update(project_id: int, updates: UpdateProject, db:Session=Depends(get_db)):
    project= Update(db, project_id, updates)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.delete("/projects/{project_id}")
def delete(project_id: int, db: Session=Depends(get_db)):
    success=Delete(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}

