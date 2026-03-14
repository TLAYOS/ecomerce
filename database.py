from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
 
load_dotenv()
 
DB_USER     = os.getenv("DB_USER",     "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Kontraseña")
DB_HOST     = os.getenv("DB_HOST",     "127.0.0.1")
DB_PORT     = os.getenv("DB_PORT",     "3306")
DB_NAME     = os.getenv("DB_NAME",     "ecomerce")

if DB_PASSWORD:
    URL_DATABASE = "mysql+pymysql://root:Kontraseña@127.0.0.1:3306/ecomerce"
else:
    URL_DATABASE = "mysql+pymysql://root:Kontraseña@127.0.0.1:3306/ecomerce"
 
engine = create_engine(URL_DATABASE)
 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
Base = declarative_base()
 
 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()