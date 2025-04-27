import os
from typing import Optional, List
from datetime import datetime, date, timedelta

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# === DATABASE SETUP ===
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
# Add sslmode for Neon/Render
if DATABASE_URL and "sslmode" not in DATABASE_URL:
    if "?" in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
    else:
        DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# === MODELS ===
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="inspector")
    created_at = Column(Date, default=datetime.utcnow)

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
    hvac_type = Column(String)
    sprinkler = Column(String)
    fire_alarm = Column(String)
    power_source = Column(String)
    vcp_status = Column(String)
    vcp_planned_date = Column(Date, nullable=True)
    smart_power_meter_status = Column(String)
    eifs = Column(String)
    eifs_installed_year = Column(Integer, nullable=True)
    exterior_cladding_condition = Column(String)
    interior_architectural_condition = Column(String)
    fire_protection_system_obsolete = Column(String)
    hvac_condition = Column(Integer, nullable=True)
    electrical_condition = Column(Integer, nullable=True)
    roofing_condition = Column(String)
    water_proofing_warranty = Column(String)
    water_proofing_warranty_date = Column(Date, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    full_inspection_completed = Column(String)

# === APP & UTILS ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

SECRET_KEY = os.environ.get("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username)
    if user is None:
        raise credentials_exception
    return user

# === SCHEMAS (Pydantic) ===
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = ""
    role: Optional[str] = "inspector"

class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role: Optional[str]
    created_at: Optional[date]
    class Config:
        from_attributes = True

class InspectionCreate(BaseModel):
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
    hvac_type: str
    sprinkler: str
    fire_alarm: str
    power_source: str
    vcp_status: str
    vcp_planned_date: Optional[date] = None
    smart_power_meter_status: str
    eifs: str
    eifs_installed_year: Optional[int] = None
    exterior_cladding_condition: str
    interior_architectural_condition: str
    fire_protection_system_obsolete: str
    hvac_condition: Optional[int] = None
    electrical_condition: Optional[int] = None
    roofing_condition: str
    water_proofing_warranty: str
    water_proofing_warranty_date: Optional[date] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    full_inspection_completed: str

class InspectionOut(InspectionCreate):
    id: int
    class Config:
        from_attributes = True

# === ENDPOINTS ===

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/inspections", response_model=InspectionOut)
def create_inspection(inspection: InspectionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_inspection = Inspection(**inspection.dict())
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

@app.get("/inspections", response_model=List[InspectionOut])
def get_all_inspections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Inspection).all()

@app.get("/inspections/{inspection_id}", response_model=InspectionOut)
def get_inspection(inspection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection

@app.put("/inspections/{inspection_id}", response_model=InspectionOut)
def update_inspection(inspection_id: int, inspection: InspectionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not db_inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    for key, value in inspection.dict().items():
        setattr(db_inspection, key, value)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

@app.delete("/inspections/{inspection_id}")
def delete_inspection(inspection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not db_inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    db.delete(db_inspection)
    db.commit()
    return {"ok": True, "deleted_id": inspection_id}

# --- Optional: Create tables if not exists (useful for dev, comment for prod) ---
# Base.metadata.create_all(bind=engine)
