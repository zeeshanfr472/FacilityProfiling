import os
from datetime import datetime, timedelta, date
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import (
    create_engine, Column, Integer, String, Date, Float, DateTime, ARRAY
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

# ENV vars
DATABASE_URL = os.getenv("DATABASE_URL", "your_neon_postgres_url")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# MODELS

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

class Inspection(Base):
    __tablename__ = "inspections"
    id = Column(Integer, primary_key=True, index=True)
    function_location_id = Column(String)
    sap_function_location = Column(String)
    building_name = Column(String)
    building_number = Column(String)
    facility_type = Column(String)
    function = Column(String)
    macro_area = Column(String)
    micro_area = Column(String)
    proponent = Column(String)
    zone = Column(String)
    hvac_type = Column(ARRAY(String))
    sprinkler = Column(String)
    fire_alarm = Column(String)
    power_source = Column(ARRAY(String))
    vcp_status = Column(String)
    vcp_planned_date = Column(Date)
    smart_power_meter_status = Column(String)
    eifs = Column(String)
    eifs_installed_year = Column(Integer)
    exterior_cladding_condition = Column(String)
    interior_architectural_condition = Column(String)
    fire_protection_system_obsolete = Column(String)
    hvac_condition = Column(Integer)
    electrical_condition = Column(Integer)
    roofing_condition = Column(String)
    water_proofing_warranty = Column(String)
    water_proofing_warranty_date = Column(Date)
    latitude = Column(Float)
    longitude = Column(Float)
    full_inspection_completed = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic schemas

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    class Config:
        orm_mode = True

class InspectionBase(BaseModel):
    function_location_id: str
    sap_function_location: str
    building_name: str
    building_number: str
    facility_type: str
    function: str
    macro_area: str
    micro_area: str
    proponent: str
    zone: str
    hvac_type: List[str]
    sprinkler: str
    fire_alarm: str
    power_source: List[str]
    vcp_status: str
    vcp_planned_date: Optional[date]
    smart_power_meter_status: str
    eifs: str
    eifs_installed_year: Optional[int]
    exterior_cladding_condition: str
    interior_architectural_condition: str
    fire_protection_system_obsolete: str
    hvac_condition: Optional[int]
    electrical_condition: Optional[int]
    roofing_condition: str
    water_proofing_warranty: str
    water_proofing_warranty_date: Optional[date]
    latitude: Optional[float]
    longitude: Optional[float]
    full_inspection_completed: str

class InspectionCreate(InspectionBase):
    pass

class InspectionResponse(InspectionBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

# UTILS

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# APP

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Make this stricter in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# CRUD for inspections

@app.post("/inspections/", response_model=InspectionResponse)
def create_inspection(inspection: InspectionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_inspection = Inspection(**inspection.dict())
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

@app.get("/inspections/", response_model=List[InspectionResponse])
def read_inspections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inspections = db.query(Inspection).offset(skip).limit(limit).all()
    return inspections

@app.get("/inspections/{inspection_id}", response_model=InspectionResponse)
def read_inspection(inspection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection

@app.put("/inspections/{inspection_id}", response_model=InspectionResponse)
def update_inspection(inspection_id: int, inspection: InspectionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if db_inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    for field, value in inspection.dict().items():
        setattr(db_inspection, field, value)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

@app.delete("/inspections/{inspection_id}")
def delete_inspection(inspection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if db_inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    db.delete(db_inspection)
    db.commit()
    return {"ok": True}
