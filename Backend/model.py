from datetime import datetime
from sqlalchemy import String ,Integer,Column,DateTime, func

from database import Base,engine




class  Task(Base):
    __tablename__='Task'
    task_id=Column(Integer,primary_key=True,autoincrement=True)
    name= Column(String,nullable=False)
    description= Column(String,nullable=True) 
    status= Column(String,nullable=False,default='Pending')  
    due_date= Column(DateTime,nullable=False)
    creation_date=Column(DateTime,nullable=False)
    completed_date= Column(DateTime,nullable=True)
    assigned_to= Column(String,nullable=False)
    priority= Column(String,nullable=False)
    
    def update_status(self,status:str):
        self.status = status
       
    def update_due_date(self,new_due_date:datetime):
        self.due_date = new_due_date

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
   




def create_table():
    Base.metadata.create_all(engine)