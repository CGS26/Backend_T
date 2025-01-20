import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks,APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import model
from database import SessionLocal
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging
import ssl
import os
ssl._create_default_https_context=ssl._create_unverified_context

router = APIRouter()


db = SessionLocal()

SENDGRID_API_KEY =os.getenv("SENDGRID_API_KEY","")
FROM_EMAIL = os.getenv("FROM_EMAIL","")
SENDGRID_CLIENT = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

class OurBaseModel(BaseModel):
    class Config:
        orm_mode = True

class Task(BaseModel):
    task_id: int
    name: str
    description: Optional[str] = None
    status: str
    creation_date: Optional[datetime] = None
    due_date: datetime
    completed_date: Optional[datetime] = None
    assigned_to: str
    priority: str

class NTask(BaseModel):
    name: str
    description: Optional[str] = None
    status: str
    due_date: datetime
    creation_date: Optional[datetime]
    completed_date: Optional[datetime] = None
    assigned_to: str
    priority: str

    def __init__(self, **kwargs):
        if not kwargs.get("creation_date"):
            kwargs["creation_date"] = datetime.now()
        super().__init__(**kwargs)

memory = {"Tasks": []}

def send_email_notification(task: Task):
    """
    Sends an email notification when a task is due.
    """
    to_email = 'gauravsushant267@gmail.com'
    subject = f"Reminder: Task '{task.name}' is due soon!"
    content = f"Hi there!\n\nThis is a reminder that the task '{task.name}' is due on {task.due_date}. Please make sure to complete it.\n\nBest regards, Your Task Management System."

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=content,
    )

    try:
        response = SENDGRID_CLIENT.send(message)
        logging.info(f"Notification sent to {to_email}: {response.status_code}")
    except Exception as e:
        logging.error(f"Failed to send notification: {str(e)}")

def check_and_notify_due_tasks():
    """
    Checks for tasks that are due soon (within the next 60 minutes) and sends notifications.
    """
    now = datetime.now()
    one_hour_later = now + timedelta(hours=24)

    tasks_due_soon = db.query(model.Task).filter(
        model.Task.due_date >= now, model.Task.due_date <= one_hour_later
    ).all()

    for task in tasks_due_soon:
        send_email_notification(task)

scheduler = BackgroundScheduler()
scheduler.add_job(check_and_notify_due_tasks, 'interval', minutes=60)
scheduler.start()

@router.post("/addTasks", response_model=NTask)
async def create_task(task: NTask):
    db_task = model.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    task = db.query(model.Task).filter(model.Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: Task):
    db_task = db.query(model.Task).filter(model.Task.task_id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    for key, value in task.dict().items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/tasks/{task_id}", response_model=Task)
def delete_task(task_id: int):
    db_task = db.query(model.Task).filter(model.Task.task_id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    return db_task

@router.get("/tasks", response_model=List[Task])
def list_tasks():
    tasks = db.query(model.Task).all()
    return tasks

