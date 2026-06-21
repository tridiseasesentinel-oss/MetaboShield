import sys
import os
import json
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

# Add parent directory to path so python can find predictor.py and database models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.database import get_db, engine, Base
    from backend.auth import get_password_hash, verify_password, create_access_token, verify_token
    import backend.models as models
    import backend.schemas as schemas
except ModuleNotFoundError:
    from database import get_db, engine, Base
    from auth import get_password_hash, verify_password, create_access_token, verify_token
    import models as models
    import schemas as schemas
from predictor import UnifiedDiseasePredictor

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MetaboShield REST API",
    description="Secure diagnostic and patient sync backend for MetaboShield.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache loaded ML model
predictor = UnifiedDiseasePredictor(model_dir=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saved_models"))

# --- ROOT API ---
@app.get("/")
def read_root():
    return {"status": "running", "system": "MetaboShield REST API", "timestamp": datetime.utcnow()}

# --- AUTH ROUTES ---
@app.post("/api/v1/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email is already registered")
    
    hashed_pw = get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        password_hash=hashed_pw,
        full_name=user.full_name,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Auto-create Patient Profile to solve the Patient ID issue
    new_profile = models.Patient(
        user_id=new_user.id,
        full_name=user.full_name
    )
    db.add(new_profile)
    db.commit()
    
    return new_user

@app.post("/api/v1/auth/login", response_model=schemas.Token)
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }

# --- PATIENT PROFILE ROUTES ---
@app.get("/api/v1/profile/me", response_model=schemas.PatientResponse)
def get_my_profile(db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    user = db.query(models.User).filter(models.User.email == current_user["sub"]).first()
    profile = db.query(models.Patient).filter(models.Patient.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.put("/api/v1/profile/me", response_model=schemas.PatientResponse)
def update_my_profile(profile_data: schemas.PatientCreate, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    user = db.query(models.User).filter(models.User.email == current_user["sub"]).first()
    profile = db.query(models.Patient).filter(models.Patient.user_id == user.id).first()
    
    profile.full_name = profile_data.full_name
    if profile_data.dob:
        profile.dob = profile_data.dob
    if profile_data.gender:
        profile.gender = profile_data.gender
        
    db.commit()
    db.refresh(profile)
    return profile

# --- DIAGNOSTICS & PREDICTION ROUTES ---
@app.post("/api/v1/predictions/assess", response_model=schemas.PredictionResponse)
def assess_patient_health(data: schemas.MedicalIntakeCreate, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    # 1. Enforce Privacy: Get patient profile associated with logged-in user
    user = db.query(models.User).filter(models.User.email == current_user["sub"]).first()
    patient = db.query(models.Patient).filter(models.Patient.user_id == user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
        
    data.patient_id = patient.id # Force the intake to belong to the logged-in user
        
    # 2. Smart Statistical Imputation (Missing Data Management)
    # Extract imputation dictionaries loaded from models metadata
    ob_imp = predictor.obesity_metadata.get("imputation", {})
    heart_imp = predictor.heart_metadata.get("imputation", {})
    
    # Impute missing parameters
    high_bp = data.high_bp or ("Yes" if data.blood_pressure >= 140 else "No")
    high_chol = data.high_chol or ("Yes" if data.cholesterol_level >= 240 else "No")
    high_cal = data.high_caloric_food or ob_imp.get("FAVC", "no").capitalize()
    veg_freq = data.veg_freq if data.veg_freq is not None else float(ob_imp.get("FCVC", 2.0))
    meals_count = data.meals_count if data.meals_count is not None else float(ob_imp.get("NCP", 3.0))
    snack_freq = data.snack_freq or ob_imp.get("CAEC", "Sometimes").capitalize()
    water_liters = data.water_liters if data.water_liters is not None else float(ob_imp.get("CH2O", 2.0))
    cal_mon = data.cal_mon or ob_imp.get("SCC", "no").capitalize()
    screen_time = data.screen_time if data.screen_time is not None else float(ob_imp.get("TUE", 1.0))
    gen_health = data.gen_health if data.gen_health is not None else 3
    
    # Save Intake record to database
    db_intake = models.MedicalIntake(
        patient_id=data.patient_id,
        age=data.age,
        gender=data.gender,
        height=data.height,
        weight=data.weight,
        blood_pressure=data.blood_pressure,
        cholesterol_level=data.cholesterol_level,
        smoking=data.smoking,
        exercise=data.exercise,
        alcohol=data.alcohol,
        stress_level=data.stress_level,
        sleep_hours=data.sleep_hours,
        family_heart_disease=data.family_heart_disease,
        family_overweight=data.family_overweight,
        high_bp=high_bp,
        high_chol=high_chol,
        high_caloric_food=high_cal,
        veg_freq=veg_freq,
        meals_count=meals_count,
        snack_freq=snack_freq,
        water_liters=water_liters,
        cal_mon=cal_mon,
        screen_time=screen_time,
        gen_health=gen_health
    )
    db.add(db_intake)
    db.commit()
    db.refresh(db_intake)
    
    # 3. Format payload matching prediction pipeline expectations
    patient_payload = {
        'Age': data.age,
        'Gender': data.gender,
        'Height': data.height,
        'Weight': data.weight,
        'Smoking': data.smoking,
        'Alcohol': data.alcohol,
        'Exercise': data.exercise,
        'HighBP': high_bp,
        'BloodPressure': data.blood_pressure,
        'HighChol': high_chol,
        'CholesterolLevel': data.cholesterol_level,
        'FamilyHeartDisease': data.family_heart_disease,
        'FamilyOverweight': data.family_overweight,
        'StressLevel': data.stress_level,
        'SleepHours': data.sleep_hours,
        'HighCaloricFood': high_cal,
        'VegetablesFreq': veg_freq,
        'MealsCount': meals_count,
        'SnackBetweenMeals': snack_freq,
        'WaterLiters': water_liters,
        'CaloriesMonitoring': cal_mon,
        'ScreenTimeHours': screen_time,
        'GeneralHealthScore': gen_health,
        'LowHDL': "Yes" if data.cholesterol_level > 240 and data.blood_pressure > 140 else "No",
        'HighLDL': "Yes" if data.cholesterol_level > 200 else "No",
        'TriglycerideLevel': 150.0,
        'FastingSugar': 95.0,
        'CRPLevel': 1.5,
        'HomocysteineLevel': 10.0
    }
    
    # Run ML Inferences
    try:
        results = predictor.predict(patient_payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Save Prediction Result to database
    db_result = models.PredictionResult(
        intake_id=db_intake.id,
        bmi=results["BMI"],
        obesity_status=results["ObesityStatus"],
        diabetes_status=results["DiabetesStatus"],
        diabetes_probability=results["DiabetesProbability"],
        prediabetes_probability=results["PrediabetesProbability"],
        heart_disease_status=results["HeartDiseaseStatus"],
        heart_disease_probability=results["HeartDiseaseProbability"],
        overall_health_severity=results["HealthStatus"],
        precautionary_measures=json.dumps(results["PrecautionaryMeasures"])
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    # Save Action Plan to database
    db_plan = models.ActionPlan(
        prediction_id=db_result.id,
        precautionary_tasks=json.dumps(results["PrecautionaryMeasures"])
    )
    db.add(db_plan)
    db.commit()
    
    # 4. Construct API Response
    return {
        "id": db_result.id,
        "intake_id": db_result.intake_id,
        "bmi": db_result.bmi,
        "obesity_status": db_result.obesity_status,
        "diabetes_status": db_result.diabetes_status,
        "diabetes_probability": db_result.diabetes_probability,
        "prediabetes_probability": db_result.prediabetes_probability,
        "heart_disease_status": db_result.heart_disease_status,
        "heart_disease_probability": db_result.heart_disease_probability,
        "overall_health_severity": db_result.overall_health_severity,
        "precautionary_measures": results["PrecautionaryMeasures"],
        "created_at": db_intake.created_at
    }

@app.get("/api/v1/predictions/me", response_model=List[schemas.PredictionResponse])
def get_my_predictions(db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    user = db.query(models.User).filter(models.User.email == current_user["sub"]).first()
    patient = db.query(models.Patient).filter(models.Patient.user_id == user.id).first()
    
    intakes = db.query(models.MedicalIntake).filter(models.MedicalIntake.patient_id == patient.id).all()
    intake_ids = [intake.id for intake in intakes]
    results = db.query(models.PredictionResult).filter(models.PredictionResult.intake_id.in_(intake_ids)).all()
    
    response_data = []
    for r in results:
        # Load the matching intake to get its created_at timestamp
        intake = next((i for i in intakes if i.id == r.intake_id), None)
        response_data.append({
            "id": r.id,
            "intake_id": r.intake_id,
            "bmi": r.bmi,
            "obesity_status": r.obesity_status,
            "diabetes_status": r.diabetes_status,
            "diabetes_probability": r.diabetes_probability,
            "prediabetes_probability": r.prediabetes_probability,
            "heart_disease_status": r.heart_disease_status,
            "heart_disease_probability": r.heart_disease_probability,
            "overall_health_severity": r.overall_health_severity,
            "precautionary_measures": json.loads(r.precautionary_measures),
            "created_at": intake.created_at if intake else datetime.utcnow()
        })
    return response_data
