from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
try:
    from .database import Base
except ImportError:
    from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="Patient")
    
    patient_profile = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    dob = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    
    user = relationship("User", back_populates="patient_profile")

    intakes = relationship("MedicalIntake", back_populates="patient", cascade="all, delete-orphan")

class MedicalIntake(Base):
    __tablename__ = "medical_intakes"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    age = Column(Float, nullable=False)
    gender = Column(String, nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    blood_pressure = Column(Float, nullable=False)
    cholesterol_level = Column(Float, nullable=False)
    smoking = Column(String, nullable=False)
    exercise = Column(String, nullable=False)
    alcohol = Column(String, nullable=False)
    stress_level = Column(String, nullable=False)
    sleep_hours = Column(Float, nullable=False)
    family_heart_disease = Column(String, nullable=False)
    family_overweight = Column(String, nullable=False)
    
    high_bp = Column(String, default="No")
    high_chol = Column(String, default="No")
    high_caloric_food = Column(String, default="No")
    veg_freq = Column(Float, default=2.0)
    meals_count = Column(Float, default=3.0)
    snack_freq = Column(String, default="Sometimes")
    water_liters = Column(Float, default=2.0)
    cal_mon = Column(String, default="No")
    screen_time = Column(Float, default=1.0)
    gen_health = Column(Integer, default=3)

    patient = relationship("Patient", back_populates="intakes")
    prediction = relationship("PredictionResult", back_populates="intake", uselist=False, cascade="all, delete-orphan")

class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id = Column(Integer, primary_key=True, index=True)
    intake_id = Column(Integer, ForeignKey("medical_intakes.id"), nullable=False)
    
    bmi = Column(Float, nullable=False)
    obesity_status = Column(String, nullable=False)
    diabetes_status = Column(String, nullable=False)
    diabetes_probability = Column(Float, nullable=False)
    prediabetes_probability = Column(Float, nullable=False)
    heart_disease_status = Column(String, nullable=False)
    heart_disease_probability = Column(Float, nullable=False)
    overall_health_severity = Column(String, nullable=False)
    precautionary_measures = Column(Text, nullable=False) # Stored as JSON string
    
    intake = relationship("MedicalIntake", back_populates="prediction")
    action_plan = relationship("ActionPlan", back_populates="prediction", uselist=False, cascade="all, delete-orphan")

class ActionPlan(Base):
    __tablename__ = "action_plans"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("prediction_results.id"), nullable=False)
    precautionary_tasks = Column(Text, nullable=False) # Stored as JSON string
    generated_at = Column(DateTime, default=datetime.utcnow)

    prediction = relationship("PredictionResult", back_populates="action_plan")
