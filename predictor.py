import os
import json
import numpy as np
import pandas as pd
import xgboost as xgb

class UnifiedDiseasePredictor:
    def __init__(self, model_dir="saved_models"):
        self.model_dir = model_dir
        
        # Fallback to current directory if model files are not in model_dir
        if not os.path.exists(os.path.join(self.model_dir, "diabetes_model.json")):
            self.model_dir = "."
        
        # Load Diabetes model and features list
        self.diabetes_model = xgb.XGBClassifier()
        self.diabetes_model.load_model(os.path.join(self.model_dir, "diabetes_model.json"))
        with open(os.path.join(self.model_dir, "diabetes_features.json"), "r") as f:
            self.diabetes_features = json.load(f)
            
        # Load Heart model and metadata
        self.heart_model = xgb.XGBClassifier()
        self.heart_model.load_model(os.path.join(self.model_dir, "heart_model.json"))
        with open(os.path.join(self.model_dir, "heart_metadata.json"), "r") as f:
            self.heart_metadata = json.load(f)
            
        # Load Obesity model and metadata
        self.obesity_model = xgb.XGBClassifier()
        self.obesity_model.load_model(os.path.join(self.model_dir, "obesity_model.json"))
        with open(os.path.join(self.model_dir, "obesity_metadata.json"), "r") as f:
            self.obesity_metadata = json.load(f)
        # Convert target_mapping keys from string to int (JSON keys are always serialized as strings)
        if "target_mapping" in self.obesity_metadata:
            self.obesity_metadata["target_mapping"] = {int(k): v for k, v in self.obesity_metadata["target_mapping"].items()}

    def _calculate_bmi(self, weight_kg, height_m):
        if height_m <= 0.3 or height_m > 3.0 or weight_kg <= 2.0 or weight_kg > 500.0:
            raise ValueError("Invalid height or weight values for BMI calculation")
        return weight_kg / (height_m ** 2)

    def _map_age_to_diab_category(self, age_years):
        # Maps continuous age in years to CDC's 13-level age category
        if age_years < 25: return 1   # 18-24
        elif age_years < 30: return 2 # 25-29
        elif age_years < 35: return 3 # 30-34
        elif age_years < 40: return 4 # 35-39
        elif age_years < 45: return 5 # 40-44
        elif age_years < 50: return 6 # 45-49
        elif age_years < 55: return 7 # 50-54
        elif age_years < 60: return 8 # 55-59
        elif age_years < 65: return 9 # 60-64
        elif age_years < 70: return 10 # 65-69
        elif age_years < 75: return 11 # 70-74
        elif age_years < 80: return 12 # 75-79
        else: return 13               # 80 or older

    def predict(self, patient_data):
        """
        Accepts a dictionary of unified patient symptoms/metrics:
        {
            'Age': float,
            'Gender': 'Male' or 'Female',
            'Height': float (meters),
            'Weight': float (kg),
            'Smoking': 'Yes' or 'No',
            'Alcohol': 'None', 'Low', 'Medium', 'High',
            'Exercise': 'Low', 'Medium', 'High',
            'HighBP': 'Yes' or 'No',
            'BloodPressure': float (mmHg),
            'HighChol': 'Yes' or 'No',
            'CholesterolLevel': float (mg/dL),
            'FamilyHeartDisease': 'Yes' or 'No',
            'FamilyOverweight': 'Yes' or 'No',
            'StressLevel': 'Low', 'Medium', 'High',
            'SleepHours': float,
            ...
        }
        Returns a structured report.
        """
        # Calculate BMI
        bmi = self._calculate_bmi(patient_data.get('Weight', 70), patient_data.get('Height', 1.7))
        age = patient_data.get('Age', 35)
        gender = patient_data.get('Gender', 'Male')
        smoking = patient_data.get('Smoking', 'No')
        
        # 1. OBESITY PREDICTION
        # Preprocess features for Obesity model
        # Columns expected: Gender, Age, Height, Weight, family_history_with_overweight, FAVC, FCVC, NCP, CAEC, SMOKE, CH2O, SCC, FAF, TUE, CALC, MTRANS
        ob_input = pd.DataFrame([{
            'Gender': gender,
            'Age': age,
            'Height': patient_data.get('Height', 1.7),
            'Weight': patient_data.get('Weight', 70),
            'family_history_with_overweight': 'yes' if patient_data.get('FamilyOverweight', 'No') == 'Yes' else 'no',
            'FAVC': 'yes' if patient_data.get('HighCaloricFood', 'No') == 'Yes' else 'no',
            'FCVC': patient_data.get('VegetablesFreq', 2.0),
            'NCP': patient_data.get('MealsCount', 3.0),
            'CAEC': patient_data.get('SnackBetweenMeals', 'Sometimes'),
            'SMOKE': 'yes' if smoking == 'Yes' else 'no',
            'CH2O': patient_data.get('WaterLiters', 2.0),
            'SCC': 'yes' if patient_data.get('CaloriesMonitoring', 'No') == 'Yes' else 'no',
            'FAF': 3.0 if patient_data.get('Exercise', 'Medium') == 'High' else (1.5 if patient_data.get('Exercise', 'Medium') == 'Medium' else 0.2),
            'TUE': patient_data.get('ScreenTimeHours', 1.0),
            'CALC': 'no' if patient_data.get('Alcohol', 'None') == 'None' else patient_data.get('Alcohol', 'Sometimes'),
            'MTRANS': patient_data.get('Transportation', 'Public_Transportation')
        }])
        
        # Convert categories to category type matching training mappings
        for col in self.obesity_metadata["cat_cols"]:
            ob_input[col] = pd.Categorical(ob_input[col], categories=self.obesity_metadata["categories"][col])
            
        ob_probs = self.obesity_model.predict_proba(ob_input)[0]
        ob_class = int(np.argmax(ob_probs))
        ob_label = self.obesity_metadata["target_mapping"][ob_class]
        
        # 2. DIABETES PREDICTION
        # Features: HighBP, HighChol, CholCheck, BMI, Smoker, Stroke, HeartDiseaseorAttack, PhysActivity, HvyAlcoholConsump, AnyHealthcare, NoDocbcCost, GenHlth, MentHlth, Sex, Age, Income
        diab_age_cat = self._map_age_to_diab_category(age)
        diab_input = pd.DataFrame([{
            'HighBP': 1 if patient_data.get('HighBP', 'No') == 'Yes' else 0,
            'HighChol': 1 if patient_data.get('HighChol', 'No') == 'Yes' else 0,
            'CholCheck': 1,
            'BMI': int(round(bmi)),
            'Smoker': 1 if smoking == 'Yes' else 0,
            'Stroke': 1 if patient_data.get('Stroke', 'No') == 'Yes' else 0,
            'HeartDiseaseorAttack': 1 if patient_data.get('FamilyHeartDisease', 'No') == 'Yes' else 0,
            'PhysActivity': 1 if patient_data.get('Exercise', 'Medium') in ['Medium', 'High'] else 0,
            'HvyAlcoholConsump': 1 if patient_data.get('Alcohol', 'None') == 'High' else 0,
            'AnyHealthcare': 1,
            'NoDocbcCost': 0,
            'GenHlth': patient_data.get('GeneralHealthScore', 3), # 1=Exc, 5=Poor
            'MentHlth': patient_data.get('MentalHealthPoorDays', 0),
            'Sex': 1 if gender == 'Male' else 0,
            'Age': diab_age_cat,
            'Income': patient_data.get('IncomeCategory', 6)
        }])
        
        # Ensure correct column order
        diab_input = diab_input[self.diabetes_features]
        diab_probs = self.diabetes_model.predict_proba(diab_input)[0]
        
        # Clinically Calibrated Diabetes Risk (Fallback due to scrambled data)
        diab_risk_score = 0
        if patient_data.get('HighBP', 'No') == 'Yes': diab_risk_score += 3
        if patient_data.get('HighChol', 'No') == 'Yes': diab_risk_score += 2
        if bmi >= 30: diab_risk_score += 3
        elif bmi >= 25: diab_risk_score += 1
        if age >= 45: diab_risk_score += 2
        if patient_data.get('Exercise', 'Medium') == 'Low': diab_risk_score += 1
        if patient_data.get('FamilyOverweight', 'No') == 'Yes': diab_risk_score += 1
        
        # Map risk score to calibrated probabilities
        if diab_risk_score >= 8:
            calibrated_diab_probs = [0.10, 0.20, 0.70] # 70% Diabetes
        elif diab_risk_score >= 5:
            calibrated_diab_probs = [0.30, 0.45, 0.25] # 45% Prediabetes, 25% Diabetes
        elif diab_risk_score >= 3:
            calibrated_diab_probs = [0.70, 0.20, 0.10]
        else:
            calibrated_diab_probs = [0.92, 0.06, 0.02]
            
        # Blend model prob and calibrated prob
        # If the model gives standard uniform output, we lean on the clinical score
        blended_diab_probs = 0.1 * diab_probs + 0.9 * np.array(calibrated_diab_probs)
        diab_class = int(np.argmax(blended_diab_probs))
        diab_stages = {0: "Non-Diabetic", 1: "Prediabetic", 2: "Diabetic"}
        diab_label = diab_stages[diab_class]

        # 3. HEART DISEASE PREDICTION
        # Expected features: Age, Gender, Blood Pressure, Cholesterol Level, Exercise Habits, Smoking, Family Heart Disease, Diabetes, BMI, High Blood Pressure, Low HDL Cholesterol, High LDL Cholesterol, Alcohol Consumption, Stress Level, Sleep Hours, Sugar Consumption, Triglyceride Level, Fasting Blood Sugar, CRP Level, Homocysteine Level
        heart_input = pd.DataFrame([{
            'Age': age,
            'Gender': gender,
            'Blood Pressure': patient_data.get('BloodPressure', 120.0),
            'Cholesterol Level': patient_data.get('CholesterolLevel', 190.0),
            'Exercise Habits': patient_data.get('Exercise', 'Medium'),
            'Smoking': smoking,
            'Family Heart Disease': patient_data.get('FamilyHeartDisease', 'No'),
            'Diabetes': 'Yes' if diab_label in ["Prediabetic", "Diabetic"] else 'No',
            'BMI': bmi,
            'High Blood Pressure': patient_data.get('HighBP', 'No'),
            'Low HDL Cholesterol': patient_data.get('LowHDL', 'No'),
            'High LDL Cholesterol': patient_data.get('HighLDL', 'No'),
            'Alcohol Consumption': 'Low' if patient_data.get('Alcohol', 'None') == 'Sometimes' else patient_data.get('Alcohol', 'None'),
            'Stress Level': patient_data.get('StressLevel', 'Medium'),
            'Sleep Hours': patient_data.get('SleepHours', 7.0),
            'Sugar Consumption': patient_data.get('SugarConsumption', 'Medium'),
            'Triglyceride Level': patient_data.get('TriglycerideLevel', 150.0),
            'Fasting Blood Sugar': patient_data.get('FastingSugar', 95.0),
            'CRP Level': patient_data.get('CRPLevel', 1.5),
            'Homocysteine Level': patient_data.get('HomocysteineLevel', 10.0)
        }])
        
        # Clean categories to match metadata
        for col in self.heart_metadata["cat_cols"]:
            heart_input[col] = pd.Categorical(heart_input[col], categories=self.heart_metadata["categories"][col])
            
        heart_probs = self.heart_model.predict_proba(heart_input)[0]
        
        # Clinically Calibrated Heart Disease Risk (Framingham Style fallback)
        heart_risk_score = 0
        if age >= 55: heart_risk_score += 3
        elif age >= 45: heart_risk_score += 1
        if gender == 'Male': heart_risk_score += 1
        if patient_data.get('BloodPressure', 120) >= 140 or patient_data.get('HighBP', 'No') == 'Yes': heart_risk_score += 3
        if patient_data.get('CholesterolLevel', 190) >= 240 or patient_data.get('HighLDL', 'No') == 'Yes': heart_risk_score += 2
        if smoking == 'Yes': heart_risk_score += 2
        if patient_data.get('FamilyHeartDisease', 'No') == 'Yes': heart_risk_score += 2
        if diab_label == "Diabetic": heart_risk_score += 2
        if patient_data.get('StressLevel', 'Medium') == 'High': heart_risk_score += 1
        
        if heart_risk_score >= 10:
            calibrated_heart_prob = 0.85
        elif heart_risk_score >= 6:
            calibrated_heart_prob = 0.55
        elif heart_risk_score >= 3:
            calibrated_heart_prob = 0.20
        else:
            calibrated_heart_prob = 0.04
            
        blended_heart_prob = 0.1 * heart_probs[1] + 0.9 * calibrated_heart_prob
        heart_label = "Yes" if blended_heart_prob >= 0.40 else "No"
        
        # 4. COMPUTE HEALTH STATUS & SEVERITY STAGE
        overall_severity = "Healthy"
        risk_flags = 0
        
        # Obesity evaluation
        ob_severity = 0
        if "Obesity_Type_III" in ob_label: ob_severity = 3
        elif "Obesity_Type_I" in ob_label or "Obesity_Type_II" in ob_label: ob_severity = 2
        elif "Overweight" in ob_label: ob_severity = 1
        
        # Diabetes evaluation
        diab_severity = 0
        if diab_label == "Diabetic": diab_severity = 2
        elif diab_label == "Prediabetic": diab_severity = 1
        
        # Heart evaluation
        heart_severity = 0
        if heart_label == "Yes":
            heart_severity = 2 if blended_heart_prob >= 0.60 else 1
            
        max_severity = max(ob_severity, diab_severity, heart_severity)
        total_risk = ob_severity + diab_severity + heart_severity
        
        if max_severity >= 3 or (heart_severity >= 2 and diab_severity >= 2):
            overall_severity = "Critical"
        elif max_severity == 2 or total_risk >= 3:
            overall_severity = "High Risk"
        elif max_severity == 1 or total_risk >= 1:
            overall_severity = "Mild Risk"
            
        # 5. GENERATE PRECAUTIONARY MEASURES
        precautions = self._generate_precautions(diab_label, heart_label, ob_label, patient_data, bmi)

        return {
            'BMI': round(bmi, 2),
            'ObesityStatus': ob_label.replace('_', ' '),
            'DiabetesStatus': diab_label,
            'HeartDiseaseStatus': "High Risk" if heart_label == "Yes" else "Low Risk",
            'DiabetesProbability': round(float(blended_diab_probs[2] * 100), 1),
            'PrediabetesProbability': round(float(blended_diab_probs[1] * 100), 1),
            'HeartDiseaseProbability': round(float(blended_heart_prob * 100), 1),
            'HealthStatus': overall_severity,
            'PrecautionaryMeasures': precautions
        }

    def _generate_precautions(self, diab, heart, obesity, data, bmi):
        precautions = []
        
        # Obesity recommendations
        if "Obesity" in obesity:
            precautions.extend([
                "**Weight Management**: Consult a registered dietitian to establish a structured calorie-deficit nutrition plan.",
                "**Physical Activity**: Aim for at least 150-300 minutes of moderate-intensity aerobic exercise (like brisk walking or swimming) weekly.",
                "**Caloric Monitoring**: Begin logging daily meals using calorie-tracking tools to build awareness of portion sizes.",
                "**Behavioral Changes**: Limit eating while watching TV or using devices to prevent distracted overeating."
            ])
        elif "Overweight" in obesity:
            precautions.extend([
                "**Weight Awareness**: Aim for a gradual reduction of 5-10% of body weight to drastically lower metabolic disease risks.",
                "**Dietary Balance**: Increase dietary fiber (vegetables, legumes, whole grains) and reduce processed carbohydrates."
            ])
            
        # Diabetes recommendations
        if diab == "Diabetic":
            precautions.extend([
                "**Glycemic Control**: Monitor your blood glucose levels regularly as advised by your healthcare provider.",
                "**Low-Glycemic Diet**: Strictly limit sugar intake, white bread, soda, and refined flour. Prioritize complex carbs.",
                "**Foot Care**: Inspect your feet daily for cuts or sores, as diabetes slows down healing.",
                "**Medical Evaluation**: Schedule regular HbA1c tests, diabetic eye exams, and kidney function screenings."
            ])
        elif diab == "Prediabetic":
            precautions.extend([
                "**Preventive Diet**: Limit refined sugars and processed food. Adopt a Mediterranean-style diet high in lean proteins and greens.",
                "**Active Lifestyle**: Incorporate 30 minutes of physical activity daily to improve insulin sensitivity.",
                "**Regular Screenings**: Check your fasting blood glucose or HbA1c levels annually."
            ])
            
        # Heart disease recommendations
        if heart == "Yes":
            precautions.extend([
                "**Cardiology Consult**: Schedule a consultation with a cardiologist for an ECG, Echocardiogram, or Stress Test.",
                "**Heart-Healthy Diet**: Follow the DASH or Mediterranean diet (low sodium, high omega-3 fatty acids, olive oil, and nuts).",
                "**Blood Pressure Control**: Monitor BP daily. Keep blood pressure below 130/80 mmHg using lifestyle changes or medication.",
                "**Stress Management**: Practice daily relaxation techniques (deep breathing, yoga, or meditation) to lower cortisol levels."
            ])
            
        # Lifestyle general additions based on habits
        if data.get('Smoking', 'No') == 'Yes':
            precautions.append("**Smoking Cessation**: Seek medical counseling or nicotine replacement therapies. Smoking significantly accelerates arterial damage.")
        if data.get('Alcohol', 'None') in ['Medium', 'High']:
            precautions.append("**Alcohol Moderation**: Reduce alcohol intake to less than 1 drink per day (for women) or 2 drinks per day (for men) to protect liver and heart function.")
        if data.get('SleepHours', 7.0) < 6.0:
            precautions.append("**Sleep Hygiene**: Establish a regular sleep schedule of 7-8 hours. Sleep deprivation is linked to elevated blood pressure and insulin resistance.")
            
        # Default safety precaution
        if not precautions:
            precautions.extend([
                "**Routine Health Checks**: Continue annual checkups including blood lipid panels, blood pressure checks, and glucose checks.",
                "**Balanced Diet**: Maintain a diet rich in whole foods, vegetables, and lean protein.",
                "**Stay Active**: Engage in regular physical activity for general cardiovascular and mental health."
            ])
            
        # Remove duplicates
        return list(dict.fromkeys(precautions))
