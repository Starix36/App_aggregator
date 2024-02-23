from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey,Table,Boolean
from sqlalchemy.orm import sessionmaker, relationship,Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel
from bs4 import BeautifulSoup
import requests

# PostgreSQL Database URL
DATABASE_URL = "postgresql://postgres:admin@localhost/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

user_app_purchases = Table(
    'user_app_purchases',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('app_id', Integer, ForeignKey('apps.id'))
)

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String)
    aggregator = relationship("Aggregator", back_populates="user")
    purchased_apps = relationship("App", secondary=user_app_purchases, back_populates="users")


# Aggregator Model
class Aggregator(Base):
    __tablename__ = "aggregators"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="aggregator")

# App Model
class App(Base):
    __tablename__ = 'apps'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    rating = Column(String)
    is_free = Column(Boolean, default=True)
    users = relationship("User", secondary=user_app_purchases, back_populates="purchased_apps")


# Initialize FastAPI App
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class URLInput(BaseModel):
    url: str

class AppPurchase(BaseModel):
    app_id: int

# Endpoints

# Endpoint for Aggregator to create an app
@app.post("/scrape/")
def create_app(url_input: URLInput, db: Session = Depends(get_db)):
    response = requests.get(url_input.url)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch HTML content")

    soup = BeautifulSoup(response.content, 'html.parser')

    app_name = soup.find('h1', class_='Fd93Bb F5UCq xwcR9d').text.strip()
    app_description = soup.find('div', class_='SfzRHd').text.strip()
    app_rating = soup.find('div', class_='jILTFe').text.strip()

    new_app = App(name=app_name, description=app_description, rating=app_rating)

    db.add(new_app)
    db.commit()
    return {"message":"App added and stored successfully"}

# Endpoint for Aggregator to view a list of all applications
@app.get("/aggregator/apps/")
def list_all_apps(db: Session = Depends(get_db)):
    apps = db.query(App).all()
    return apps

# Endpoint for Aggregator to remove/ban a specific app
@app.delete("/aggregator/apps/{app_id}")
def remove_app(app_id: int, db: Session = Depends(get_db)):
    app = db.query(App).filter(App.id == app_id).first()
    if app:
        db.delete(app)
        db.commit()
        return {"message": "App removed successfully"}
    else:
        raise HTTPException(status_code=404, detail="App not found")

# Endpoint for User to view a list of available applications
@app.get("/user/apps/")
def list_available_apps(db: Session = Depends(get_db)):
    apps = db.query(App).filter(App.is_free == True).all()
    return apps


# Endpoint for User to purchase an app
@app.post("/user/apps/purchase/{app_id}")
def purchase_app(app_id: int, db: Session = Depends(get_db)):
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    user_id = 1
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.purchased_apps.append(app)
    db.commit()
    return {"message": "App purchased successfully"}

# Endpoint for User to view all their purchased apps
@app.get("/user/apps/purchased/")
def list_purchased_apps(db: Session = Depends(get_db)):
    user_id = 1
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    purchased_apps = user.purchased_apps
    return purchased_apps

# Create database tables
def create_tables():
    Base.metadata.create_all(bind=engine)

create_tables()
