from sqlalchemy import create_engine, Column, Integer, ForeignKey, TIMESTAMP, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
from config import DATABASE_URL
from pydantic import BaseModel

load_dotenv()

#connect to the database
engine=create_engine(DATABASE_URL, echo=True)
SessionLocal=sessionmaker(autoflush=False, autocommit=False, bind=engine)
Base=declarative_base()

#create table user
class User(Base):
    __tablename__="users"
    id=Column(Integer, primary_key=True, index=True)
    username=Column(String)
    email=Column(String, unique=True, index=True)
    picture=Column(String, nullable=True)

#a table for projects
class Project(Base):
    __tablename__="projects"
    id = Column(Integer, primary_key=True, index=True)
    title =Column(String, nullable=False)
    description = Column(Text, nullable=False)
    files= relationship("ProjectFile", back_populates="project")
    created_at= Column(DateTime, default=datetime.utcnow)

class ProjectFile(Base):
    __tablename__="projectFile"
    id= Column(Integer, primary_key=True, index=True) 
    filename = Column(String)
    path= Column(String)
    project_id=Column(Integer, ForeignKey("projects.id"))
    project= relationship("Project", back_populates="files")

class UpdateProject(BaseModel):
    title: Optional[str]
    description: Optional[str]

    
Base.metadata.create_all(bind=engine)