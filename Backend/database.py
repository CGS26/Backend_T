from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker



username:str ="postgres"
password:str="root"
engine:str = "localhost"

# SQLALCHEMY_DATABASE_URL:str=f'postgresql://{username}:{password}@localhost/FastApi'
SQLALCHEMY_DATABASE_URL:str=f'postgresql://{username}:{password}@localhost/Xyenta'


engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()