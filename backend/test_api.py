import sys
import os
import unittest
import json

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from predictor import UnifiedDiseasePredictor

class TestMetaboShieldCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Locate saved_models directory relative to test script
        cls.model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saved_models")
        cls.predictor = UnifiedDiseasePredictor(model_dir=cls.model_dir)

    def test_metadata_json_integrity(self):
        """Verify models are loaded from JSON and not unsafe pickles"""
        self.assertTrue(os.path.exists(os.path.join(self.model_dir, "diabetes_features.json")))
        self.assertTrue(os.path.exists(os.path.join(self.model_dir, "heart_metadata.json")))
        self.assertTrue(os.path.exists(os.path.join(self.model_dir, "obesity_metadata.json")))
        
        # Verify they are serializable lists/dicts
        self.assertIsInstance(self.predictor.diabetes_features, list)
        self.assertIsInstance(self.predictor.heart_metadata, dict)
        self.assertIsInstance(self.predictor.obesity_metadata, dict)

    def test_bmi_calculator_bounds(self):
        """Check that invalid height/weight values are correctly caught and rejected"""
        # Test negative height
        with self.assertRaises(ValueError):
            self.predictor._calculate_bmi(70, -1.70)
            
        # Test zero height
        with self.assertRaises(ValueError):
            self.predictor._calculate_bmi(70, 0.0)
            
        # Test extreme unreal values
        with self.assertRaises(ValueError):
            self.predictor._calculate_bmi(0.5, 1.70)
            
        # Test valid calculations
        bmi = self.predictor._calculate_bmi(70, 1.70)
        self.assertAlmostEqual(bmi, 70 / (1.70 ** 2), places=2)

    def test_predictor_imputation_keys(self):
        """Ensure all required feature columns are present in metadata for imputation"""
        # Obesity features
        ob_imputations = self.predictor.obesity_metadata.get("imputation", {})
        self.assertIn("FAVC", ob_imputations)
        self.assertIn("FCVC", ob_imputations)
        self.assertIn("NCP", ob_imputations)
        self.assertIn("CAEC", ob_imputations)
        
        # Heart features
        heart_imputations = self.predictor.heart_metadata.get("imputation", {})
        self.assertIn("Age", heart_imputations)
        self.assertIn("Gender", heart_imputations)
        self.assertIn("Smoking", heart_imputations)

    def test_prediction_output_structure(self):
        """Execute a prediction check with mock data and verify structure"""
        mock_patient = {
            'Age': 45,
            'Gender': 'Male',
            'Height': 1.75,
            'Weight': 85,
            'Smoking': 'No',
            'Alcohol': 'Sometimes',
            'Exercise': 'Medium',
            'HighBP': 'Yes',
            'BloodPressure': 142.0,
            'HighChol': 'No',
            'CholesterolLevel': 195.0,
            'FamilyHeartDisease': 'No',
            'FamilyOverweight': 'Yes',
            'StressLevel': 'Medium',
            'SleepHours': 7.0,
            'HighCaloricFood': 'Yes',
            'VegetablesFreq': 2.0,
            'MealsCount': 3.0,
            'SnackBetweenMeals': 'Sometimes',
            'WaterLiters': 2.0,
            'CaloriesMonitoring': 'No',
            'ScreenTimeHours': 1.0,
            'GeneralHealthScore': 3
        }
        
        res = self.predictor.predict(mock_patient)
        
        self.assertIn("BMI", res)
        self.assertIn("ObesityStatus", res)
        self.assertIn("DiabetesStatus", res)
        self.assertIn("HeartDiseaseStatus", res)
        self.assertIn("HealthStatus", res)
        self.assertIn("PrecautionaryMeasures", res)
        
        self.assertIsInstance(res["PrecautionaryMeasures"], list)
        self.assertGreater(len(res["PrecautionaryMeasures"]), 0)

if __name__ == "__main__":
    unittest.main()
