from pydantic import BaseModel
from typing import List

class ProjectFileOut(BaseModel):
    filename: str
    path: str

    class Config:
        orm_mode = True

class ProjectOut(BaseModel):
    id: int
    title: str
    description: str
    files: List[ProjectFileOut]

    class Config:
        orm_mode = True