import os
from fastapi.responses import StreamingResponse
import pandas as pd
from fastapi import  Depends, HTTPException, BackgroundTasks,APIRouter,Response
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from Authentication import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user, get_password_hash, verify_password
import model
from database import SessionLocal
from apscheduler.schedulers.background import BackgroundScheduler
import sendgrid
from sendgrid.helpers.mail import Mail
import logging
import ssl
import io
from dotenv import  load_dotenv
from analysis import generate_csv_report, plot_completed_tasks_per_day, plot_completion_trends, plot_task_priority_distribution, plot_time_vs_priority, preprocess_data,calculate_task_completion_time



ssl._create_default_https_context=ssl._create_unverified_context

router = APIRouter()
oauth_scheme=OAuth2PasswordBearer(tokenUrl="token")
load_dotenv()
db = SessionLocal()
SENDGRID_API_KEY =os.getenv("SENDGRID_API_KEY","")
FROM_EMAIL = os.getenv("FROM_EMAIL","")
SENDGRID_CLIENT = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

class OurBaseModel(BaseModel):
    class Config:
        orm_mode = True
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

   
class Task(BaseModel):
    task_id: int
    name: str
    description: Optional[str] = None
    # status: str
    status: Optional[str] = 'Pending'
    creation_date: Optional[datetime] = None
    due_date: datetime
    completed_date: Optional[datetime] = None
    assigned_to: str
    priority: str

class NTask(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = 'Pending'
    due_date: datetime
    creation_date: Optional[datetime]
    completed_date: Optional[datetime] = None
    assigned_to: str
    priority: str

    def __init__(self, **kwargs):
        if not kwargs.get("creation_date"):
            kwargs["creation_date"] = datetime.now()
        super().__init__(**kwargs)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str

    class Config:
        orm_mode = True
memory = {"Tasks": []}

def send_email_notification(task: Task):
   
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
    
    now = datetime.now()
    one_hour_later = now + timedelta(hours=24)

    tasks_due_soon = db.query(model.Task).filter(
        model.Task.due_date >= now, model.Task.due_date <= one_hour_later
    ).all()

    for task in tasks_due_soon:
        send_email_notification(task)

scheduler = BackgroundScheduler()
scheduler.add_job(check_and_notify_due_tasks, 'interval', hours=24)
# scheduler.start()


@router.get("/users/me")
def get_me(current_user: model.User = Depends(get_current_user)):
    return current_user

@router.post("/token")
async def token_generate(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(model.User).filter(model.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
def register_user(user: UserCreate):
    db_user = db.query(model.User).filter(model.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = model.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully!"}

@router.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int,token :str=Depends(get_current_user)):
    task = db.query(model.Task).filter(model.Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/addTasks", response_model=NTask)
async def create_task(task: NTask,token :str=Depends(get_current_user)):
    db_task = model.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.post("/addTasks/multiple",)
async def create_task(tasks: List[NTask],token :str=Depends(get_current_user)):
    for task in tasks:
        db_task = model.Task(**task.dict())
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
    return "done"

@router.get("/tasks/mail/{task_id}", response_model=str)
def mail_task(task_id: int,token :str=Depends(get_current_user)):
    task = db.query(model.Task).filter(model.Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    send_email_notification(task)
    return "mailed user"



@router.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: Task,token :str=Depends(get_current_user)):
    db_task = db.query(model.Task).filter(model.Task.task_id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    for key, value in task.dict().items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task


@router.put("/tasks/Status/{task_id}", response_model=Task)
def update_task_status(task_id: int, status: str,token :str=Depends(get_current_user)):
    db_task = db.query(model.Task).filter(model.Task.task_id == task_id).first()
    db_task.update_status(status)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.put("/tasks/duedate/{task_id}", response_model=Task)
def update_task_status(task_id: int, duedate: datetime,token :str=Depends(get_current_user)):
    db_task = db.query(model.Task).filter(model.Task.task_id == task_id).first()
    db_task.update_due_date(duedate) 
    db.commit()
    db.refresh(db_task)
    return db_task



@router.delete("/tasks/{task_id}", response_model=Task)
def delete_task(task_id: int,token :str=Depends(get_current_user)):
    db_task = db.query(model.Task).filter(model.Task.task_id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    return db_task

@router.get("/tasks", response_model=List[Task])
def list_tasks(token :str=Depends(get_current_user)):
    tasks = db.query(model.Task).all()
    return tasks
@router.get("/statstics/tasks/")
def get_statistics(token :str=Depends(get_current_user)):
    db_task_query = db.query(model.Task)
    df_from_query = pd.read_sql_query(db_task_query.statement, db.bind)
    df_Preprocess=preprocess_data(df_from_query)
    df_Preprocess=calculate_task_completion_time(df_from_query)
    avg_completion_time = df_Preprocess['completion_time'].mean()
    min_completion_time = df_Preprocess['completion_time'].min()
    max_completion_time = df_Preprocess['completion_time'].max()
    overdue_tasks_count = len(df_Preprocess[df_Preprocess['completed_date'] > df_Preprocess['due_date']])
    pending_tasks_count = len(df_Preprocess[df_Preprocess['completed_date'].isna()])

    return {
        "AvgCompletionTime": avg_completion_time,
        "MinCompletionTime": min_completion_time,
        "MaxCompletionTime": max_completion_time,
        "NumberOfOverdueTasks": overdue_tasks_count,
        "PendingTasks": pending_tasks_count
    }

    

@router.get('/download-report')
async def download_report(token :str=Depends(get_current_user)):
    db_task_query = db.query(model.Task)
    df_from_query = pd.read_sql_query(db_task_query.statement, db.bind)
    df_Preprocess=preprocess_data(df_from_query)
    df_csv = generate_csv_report(df_Preprocess)
    buf = io.BytesIO()
    buf.write(df_csv.encode())
    buf.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="report.csv"'
    }
    return StreamingResponse(buf, media_type='text/csv', headers=headers)



@router.get('/visulaise/{plot}')
def get_img(plot:str,background_tasks: BackgroundTasks,token :str=Depends(get_current_user)):

    db_task_query = db.query(model.Task)
    df_from_query = pd.read_sql_query(db_task_query.statement, db.bind)
    df_Preprocess=preprocess_data(df_from_query)
    df_test=calculate_task_completion_time(df_Preprocess)
    if(plot=='line'):
        img_buf = plot_completion_trends(df_test)    
    elif(plot=='pie'):
        img_buf = plot_task_priority_distribution(df_test)
    elif(plot=='bar'):
        img_buf = plot_completed_tasks_per_day(df_test)
    else:
        img_buf = plot_time_vs_priority(df_test)


    
    bufContents: bytes = img_buf.getvalue()
    background_tasks.add_task(img_buf.close)
    headers = {'Content-Disposition': 'inline; filename="out.png"'}
    return Response(bufContents, headers=headers, media_type='image/png')