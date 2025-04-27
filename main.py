import logging
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from starlette.middleware.wsgi import WSGIMiddleware
from dashboard.app import app as dash_app

# Add these lines at the top of your main.py file
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import date, datetime, timedelta
import os
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Import database helper
from db_helper import get_db, get_user, create_user, get_all_inspections
from db_helper import get_inspection, create_inspection, update_inspection, delete_inspection

# =========================
# Configuration and Helpers
# =========================

SECRET_KEY = os.getenv("SECRET_KEY", "my-very-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# =====================
# User Auth Management
# =====================

def verify_password(plain_password, password_hash):
    return pwd_context.verify(plain_password, password_hash)

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.password_hash):
        return False
    return True

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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


# =========================
# Inspection Record Model
# =========================

class InspectionRecord(BaseModel):
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

    hvac_type: List[Literal["Window", "Split", "Cassette", "Duct Concealed", "Free Standing", "Other"]]
    sprinkler: Literal["Yes", "No"]
    fire_alarm: Literal["Yes", "No"]
    power_source: List[Literal["110V", "220V", "380V", "480V"]]
    vcp_status: Literal["Completed", "Inprogress", "Not Applicable", "Planned"]
    vcp_planned_date: Optional[date] = None
    smart_power_meter_status: Literal["Yes", "No"]
    eifs: Literal["Yes", "No"]
    eifs_installed_year: Optional[int] = None

    exterior_cladding_condition: Literal["Poor", "Average", "Good", "Excellent"]
    interior_architectural_condition: Literal["Poor", "Average", "Good", "Excellent"]
    fire_protection_system_obsolete: Literal["Obsolete", "Not Obsolete"]
    hvac_condition: Optional[int] = None
    electrical_condition: Optional[int] = None
    roofing_condition: Literal["Poor", "Average", "Good", "Excellent"]

    water_proofing_warranty: Literal["Yes", "No"]
    water_proofing_warranty_date: Optional[date] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    full_inspection_completed: Literal["Yes", "No"]

# =========================
# FastAPI App and Endpoints
# =========================

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# ----------- AUTH ENDPOINTS -----------

@app.post("/register")
def register(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = get_user(db, form_data.username)
        if user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        password_hash = pwd_context.hash(form_data.password)
        create_user(db, form_data.username, password_hash)
        return {"msg": "User registered successfully."}
    except Exception as e:
        print("REGISTER ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        if not authenticate_user(db, form_data.username, form_data.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print("LOGIN ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

# ----------- INSPECTION CRUD -----------

@app.post("/inspection")
def create_inspection_endpoint(
    record: InspectionRecord,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Convert the record to a dict
        inspection_data = record.dict()
        
        # Convert list values to comma-separated strings
        inspection_data["hvac_type"] = ", ".join(inspection_data["hvac_type"])
        inspection_data["power_source"] = ", ".join(inspection_data["power_source"])
        
        # Create the inspection
        db_inspection = create_inspection(db, inspection_data)
        
        return {"status": "added", "id": db_inspection.id, "record": record}
    except Exception as e:
        print("DATABASE ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/inspections/{inspection_id}")
def get_inspection_by_id_endpoint(
    inspection_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        inspection = get_inspection(db, inspection_id)
        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")
        inspection_dict = {
            "row_number": inspection.id,
            "function_location_id": inspection.function_location_id,
            "sap_function_location": inspection.sap_function_location,
            "building_name": inspection.building_name,
            "building_number": inspection.building_number,
            "facility_type": inspection.facility_type,
            "function": inspection.function,
            "macro_area": inspection.macro_area,
            "micro_area": inspection.micro_area,
            "proponent": inspection.proponent,
            "zone": inspection.zone,
            "hvac_type": inspection.hvac_type,
            "sprinkler": inspection.sprinkler,
            "fire_alarm": inspection.fire_alarm,
            "power_source": inspection.power_source,
            "vcp_status": inspection.vcp_status,
            "vcp_planned_date": inspection.vcp_planned_date.isoformat() if inspection.vcp_planned_date else None,
            "smart_power_meter_status": inspection.smart_power_meter_status,
            "eifs": inspection.eifs,
            "eifs_installed_year": inspection.eifs_installed_year,
            "exterior_cladding_condition": inspection.exterior_cladding_condition,
            "interior_architectural_condition": inspection.interior_architectural_condition,
            "fire_protection_system_obsolete": inspection.fire_protection_system_obsolete,
            "hvac_condition": inspection.hvac_condition,
            "electrical_condition": inspection.electrical_condition,
            "roofing_condition": inspection.roofing_condition,
            "water_proofing_warranty": inspection.water_proofing_warranty,
            "water_proofing_warranty_date": inspection.water_proofing_warranty_date.isoformat() if inspection.water_proofing_warranty_date else None,
            "latitude": inspection.latitude,
            "longitude": inspection.longitude,
            "full_inspection_completed": inspection.full_inspection_completed
        }
        return inspection_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inspections")
def get_all_inspections_endpoint(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        db_inspections = get_all_inspections(db)
        
        # Convert to a list of dictionaries
        inspections = []
        for idx, inspection in enumerate(db_inspections):
            # Convert to dict
            inspection_dict = {
                "row_number": inspection.id,
                "function_location_id": inspection.function_location_id,
                "sap_function_location": inspection.sap_function_location,
                "building_name": inspection.building_name,
                "building_number": inspection.building_number,
                "facility_type": inspection.facility_type,
                "function": inspection.function,
                "macro_area": inspection.macro_area,
                "micro_area": inspection.micro_area,
                "proponent": inspection.proponent,
                "zone": inspection.zone,
                "hvac_type": inspection.hvac_type,
                "sprinkler": inspection.sprinkler,
                "fire_alarm": inspection.fire_alarm,
                "power_source": inspection.power_source,
                "vcp_status": inspection.vcp_status,
                "vcp_planned_date": inspection.vcp_planned_date.isoformat() if inspection.vcp_planned_date else None,
                "smart_power_meter_status": inspection.smart_power_meter_status,
                "eifs": inspection.eifs,
                "eifs_installed_year": inspection.eifs_installed_year,
                "exterior_cladding_condition": inspection.exterior_cladding_condition,
                "interior_architectural_condition": inspection.interior_architectural_condition,
                "fire_protection_system_obsolete": inspection.fire_protection_system_obsolete,
                "hvac_condition": inspection.hvac_condition,
                "electrical_condition": inspection.electrical_condition,
                "roofing_condition": inspection.roofing_condition,
                "water_proofing_warranty": inspection.water_proofing_warranty,
                "water_proofing_warranty_date": inspection.water_proofing_warranty_date.isoformat() if inspection.water_proofing_warranty_date else None,
                "latitude": inspection.latitude,
                "longitude": inspection.longitude,
                "full_inspection_completed": inspection.full_inspection_completed
            }
            inspections.append(inspection_dict)
        
        return {"inspections": inspections}
    except Exception as e:
        print("DATABASE ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/inspection/{inspection_id}")
def update_inspection_endpoint(
    inspection_id: int,
    record: InspectionRecord,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Check if inspection exists
        db_inspection = get_inspection(db, inspection_id)
        if not db_inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")
        
        # Convert the record to a dict
        inspection_data = record.dict()
        
        # Convert list values to comma-separated strings
        inspection_data["hvac_type"] = ", ".join(inspection_data["hvac_type"])
        inspection_data["power_source"] = ", ".join(inspection_data["power_source"])
        
        # Update the inspection
        db_inspection = update_inspection(db, inspection_id, inspection_data)
        
        return {"status": "updated", "id": db_inspection.id, "record": record}
    except Exception as e:
        print("DATABASE ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/inspection/{inspection_id}")
def delete_inspection_endpoint(
    inspection_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Check if inspection exists
        db_inspection = get_inspection(db, inspection_id)
        if not db_inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")
        
        # Delete the inspection
        success = delete_inspection(db, inspection_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete inspection")
        
        return {"status": "deleted", "id": inspection_id}
    except Exception as e:
        print("DATABASE ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

# Mount Dash at /dashboard
app.mount("/dashboard", WSGIMiddleware(dash_app.server))
