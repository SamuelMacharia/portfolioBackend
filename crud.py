from sqlalchemy.orm import Session
from database import UpdateProject, Project
def Update(db:Session, project_id: int, updates:UpdateProject):
    project= db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    print("Updates received:", updates.dict(exclude_unset=True))
    update_data= updates.dict(exclude_none=True)
    for key, value in update_data.items():
        print(f"Updating {key} → {value}")
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return project
    
def Delete(db: Session, project_id: int):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    db.delete(project)
    db.commit()
    return project