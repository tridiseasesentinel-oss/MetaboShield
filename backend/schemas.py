from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    role: Optional[str] = "Patient"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    class Config:
        orm_mode = True
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

# --- PATIENT SCHEMAS ---
class PatientCreate(BaseModel):
    full_name: str
    dob: Optional[str] = None
    gender: Optional[str] = None

class PatientResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    dob: Optional[str]
    gender: Optional[str]

    class Config:
        orm_mode = True
        from_attributes = True

# --- INTAKE & DIAGNOSTIC SCHEMAS ---
class MedicalIntakeCreate(BaseModel):
    patient_id: int
    age: float = Field(..., ge=18, le=120)
    gender: str  # 'Male' or 'Female'
    height: float = Field(..., ge=0.5, le=2.5)  # in meters
    weight: float = Field(..., ge=10, le=300)   # in kg
    blood_pressure: float = Field(..., ge=50, le=250) # systolic mmHg
    cholesterol_level: float = Field(..., ge=80, le=500) # mg/dL
    smoking: str  # 'Yes' or 'No'
    exercise: str # 'Low', 'Medium', 'High'
    alcohol: str  # 'None', 'Low', 'Medium', 'High' or 'Sometimes'
    stress_level: str # 'Low', 'Medium', 'High'
    sleep_hours: float = Field(..., ge=1, le=16)
    family_heart_disease: str # 'Yes' or 'No'
    family_overweight: str # 'Yes' or 'No'

    # Optional columns that can be imputed from training metadata if missing
    high_bp: Optional[str] = None
    high_chol: Optional[str] = None
    high_caloric_food: Optional[str] = None
    veg_freq: Optional[float] = None
    meals_count: Optional[float] = None
    snack_freq: Optional[str] = None
    water_liters: Optional[float] = None
    cal_mon: Optional[str] = None
    screen_time: Optional[float] = None
    gen_health: Optional[int] = None

class PredictionResponse(BaseModel):
    id: int
    intake_id: int
    bmi: float
    obesity_status: str
    diabetes_status: str
    diabetes_probability: float
    prediabetes_probability: float
    heart_disease_status: str
    heart_disease_probability: float
    overall_health_severity: str
    precautionary_measures: List[str]
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
