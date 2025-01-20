
import uvicorn;
from fastapi import FastAPI, HTTPException;
from fastapi.middleware.cors import CORSMiddleware;
from pydantic import BaseModel;
from typing import List,Optional;
from datetime import datetime, timedelta
import secure_routes
import model 
from database import SessionLocal
# import routes
# import routes_v2 as test
# import test

app= FastAPI()

origins =[
     
    #  "http:localhost:3000"
     '*'
]

app.add_middleware(
     CORSMiddleware,
     allow_origins=origins,
     allow_credentials=True,
     allow_methods=['*'],
     allow_headers=['*']

)
# app.include_router(test.router)/
app.include_router(secure_routes.router)


if __name__=="__main__":
     uvicorn.run(app,host="0.0.0.0",port=3002)