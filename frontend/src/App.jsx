import React, { useState, useEffect } from 'react';
import { 
  Shield, Heart, Activity, User, LogOut, CheckCircle, Search, 
  RefreshCw, AlertTriangle, ChevronRight, FileText, Plus, Eye,
  Sun, Moon, Type, Scale, Sparkles
} from 'lucide-react';

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'https://shazeen-amjad45-metaboshield-api.hf.space';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [role, setRole] = useState(localStorage.getItem('role') || '');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Theme and Font Resizing States
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [fontScale, setFontScale] = useState(parseInt(localStorage.getItem('fontScale')) || 16);

  // Navigation & Data States
  const [view, setView] = useState(token ? 'dashboard' : 'login');
  const [patients, setPatients] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [syncEhrId, setSyncEhrId] = useState('');
  const [syncLoading, setSyncLoading] = useState(false);
  const [predictLoading, setPredictLoading] = useState(false);
  const [results, setResults] = useState(null);

  // New Patient Registration ID Form
  const [newEhrId, setNewEhrId] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newDob, setNewDob] = useState('');
  const [newGender, setNewGender] = useState('Male');
  const [autoId, setAutoId] = useState(true);
  const [showAddPatient, setShowAddPatient] = useState(false);

  // Unit Systems selection
  const [heightUnit, setHeightUnit] = useState('Meters'); // 'Meters' or 'Feet/Inches'
  const [heightM, setHeightM] = useState(1.70);
  const [heightFt, setHeightFt] = useState(5);
  const [heightIn, setHeightIn] = useState(7);

  const [weightUnit, setWeightUnit] = useState('Kilograms'); // 'Kilograms' or 'Pounds'
  const [weightKg, setWeightKg] = useState(70);
  const [weightLbs, setWeightLbs] = useState(154);

  // Intake Form Vitals/Lifestyle
  const [activeTab, setActiveTab] = useState('demographics');
  const [formData, setFormData] = useState({
    age: 35,
    blood_pressure: 120,
    cholesterol_level: 190,
    smoking: 'No',
    exercise: 'Medium',
    alcohol: 'None',
    stress_level: 'Medium',
    sleep_hours: 7.0,
    family_heart_disease: 'No',
    family_overweight: 'No',
    water_liters: 2.0,
    veg_freq: 2.0,
    meals_count: 3.0,
    snack_freq: 'Sometimes'
  });

  // Load theme and font scale on startup
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.style.setProperty('--font-scale', `${fontScale}px`);
    localStorage.setItem('fontScale', fontScale);
  }, [fontScale]);

  // Auto-generate EHR ID for new patients if selected
  useEffect(() => {
    if (autoId && showAddPatient) {
      setNewEhrId(`EHR-${Math.floor(1000 + Math.random() * 9000)}`);
    }
  }, [autoId, showAddPatient]);

  // Fetch My Profile
  const fetchMyProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/profile/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedPatient({
          id: data.id,
          ehr_id: `USR-${data.user_id}`,
          full_name: data.full_name,
          dob: data.dob,
          gender: data.gender || 'Male'
        });
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
    }
  };

  useEffect(() => {
    if (token) {
      fetchMyProfile();
    }
  }, [token]);

  // Google Translate dynamic initialization
  useEffect(() => {
    if (document.getElementById('google-translate-script')) return;
    
    window.googleTranslateElementInit = () => {
      const el = document.getElementById('google_translate_element');
      if (el) el.innerHTML = ''; // Prevent double rendering in React StrictMode
      new window.google.translate.TranslateElement(
        { pageLanguage: 'en' },
        'google_translate_element'
      );
    };
    const script = document.createElement('script');
    script.id = 'google-translate-script';
    script.src = "https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
    script.async = true;
    document.body.appendChild(script);
  }, []);

  // Handle Auth
  const handleAuth = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    const endpoint = isRegister ? '/api/v1/auth/register' : '/api/v1/auth/login';
    const payload = isRegister 
      ? { email, password, full_name: fullName, role: 'Patient' }
      : { email, password };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      if (isRegister) {
        setSuccess('Registration successful! Please login.');
        setIsRegister(false);
        setPassword('');
      } else {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('role', data.role);
        setToken(data.access_token);
        setRole(data.role);
        setView('dashboard');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    setToken('');
    setRole('');
    setView('login');
    setResults(null);
    setSelectedPatient(null);
  };

  // Add Patient Manual/Automatic ID
  const handleAddPatient = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/patients`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ehr_id: newEhrId,
          full_name: newFullName,
          dob: newDob || null,
          gender: newGender
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create patient');
      
      setSuccess(`Patient ${newFullName} registered successfully under ID ${newEhrId}!`);
      fetchPatients();
      setNewFullName('');
      setNewDob('');
      setShowAddPatient(false);
    } catch (err) {
      setError(err.message);
    }
  };

  // Sync EHR Data
  const handleEhrSync = async (ehrId) => {
    setError('');
    setSyncLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/patients/${ehrId}/sync`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'EMR record not found');
      
      setSelectedPatient({
        id: data.patient_id,
        ehr_id: data.ehr_id,
        full_name: data.full_name,
        dob: data.dob,
        gender: data.gender
      });

      if (data.vitals) {
        setFormData({
          age: data.vitals.age,
          blood_pressure: data.vitals.blood_pressure,
          cholesterol_level: data.vitals.cholesterol_level,
          smoking: data.vitals.smoking,
          exercise: data.vitals.exercise,
          alcohol: data.vitals.alcohol,
          stress_level: data.vitals.stress_level,
          sleep_hours: data.vitals.sleep_hours,
          family_heart_disease: 'No',
          family_overweight: 'No'
        });

        // Set local unit values and run conversions
        const m = data.vitals.height;
        setHeightM(m);
        const totalInches = m / 0.0254;
        setHeightFt(Math.floor(totalInches / 12));
        setHeightIn(Math.round(totalInches % 12));

        const kg = data.vitals.weight;
        setWeightKg(kg);
        setWeightLbs(Math.round(kg * 2.20462));

        setSuccess(`EMR Vitals synced for ${data.full_name}`);
      } else {
        setSuccess(`EMR Patient record loaded. Please complete diagnostics metrics.`);
      }
      setView('intake');
    } catch (err) {
      setError(err.message);
    } finally {
      setSyncLoading(false);
    }
  };

  // Submit assessment payload
  const runDiagnostics = async () => {
    setError('');
    setPredictLoading(true);
    
    // Convert units to metric standard before posting
    let finalHeight = heightM;
    if (heightUnit === 'Feet/Inches') {
      finalHeight = (heightFt * 12 + heightIn) * 0.0254;
    }

    let finalWeight = weightKg;
    if (weightUnit === 'Pounds') {
      finalWeight = weightLbs / 2.20462;
    }

    try {
      const payload = {
        patient_id: selectedPatient.id,
        age: parseFloat(formData.age),
        gender: selectedPatient.gender,
        height: parseFloat(finalHeight.toFixed(2)),
        weight: parseFloat(finalWeight.toFixed(2)),
        blood_pressure: parseFloat(formData.blood_pressure),
        cholesterol_level: parseFloat(formData.cholesterol_level),
        smoking: formData.smoking,
        exercise: formData.exercise,
        alcohol: formData.alcohol,
        stress_level: formData.stress_level,
        sleep_hours: parseFloat(formData.sleep_hours),
        family_heart_disease: formData.family_heart_disease,
        family_overweight: formData.family_overweight,
        water_liters: parseFloat(formData.water_liters),
        veg_freq: parseFloat(formData.veg_freq),
        meals_count: parseFloat(formData.meals_count),
        snack_freq: formData.snack_freq
      };

      const res = await fetch(`${API_BASE}/api/v1/predictions/assess`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Prediction failed');
      
      setResults(data);
      setView('report');
    } catch (err) {
      setError(err.message);
    } finally {
      setPredictLoading(false);
    }
  };

  const filteredPatients = patients.filter(p => 
    p.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.ehr_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="app-container">
      {/* Navbar */}
      <nav className="navbar">
        <div className="logo-container">
          <Shield className="logo-icon text-teal-400" size={28} style={{color: '#2dd4bf'}} />
          <span className="logo-text">Metabo<span style={{color: '#38bdf8'}}>Shield</span></span>
        </div>
        
        <div className="nav-links">
          <div id="google_translate_element" style={{ marginRight: '1rem' }}></div>
          {token && (
            <>
              <span style={{color: 'var(--text-muted)', fontSize: '0.875rem'}} className="hidden-mobile">
                Welcome, <strong style={{color: '#38bdf8'}}>{role}</strong>
              </span>
              <button className="btn btn-secondary" onClick={handleLogout}>
                <LogOut size={16} /> Logout
              </button>
            </>
          )}
        </div>
      </nav>

      {/* Main Container */}
      <main style={{ flex: 1, padding: '2rem 1.5rem', maxWidth: '1200px', width: '100%', margin: '0 auto' }}>
        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#f87171', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <CheckCircle size={18} />
            <span>{success}</span>
          </div>
        )}

        {/* --- VIEW 1: AUTH LOGIN/REGISTER --- */}
        {view === 'login' && (
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '4rem' }}>
            <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
              <h2 style={{ textAlign: 'center', marginBottom: '0.5rem' }}>
                {isRegister ? 'Register Account' : 'Patient Login'}
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', textAlign: 'center', marginBottom: '2rem' }}>
                Personal Health Tracking & Risk Prediction
              </p>
              
              <form onSubmit={handleAuth}>
                {isRegister && (
                  <div className="form-group">
                    <label className="form-label">Full Name</label>
                    <input 
                      type="text" className="form-control" placeholder="Dr. John Doe"
                      value={fullName} onChange={e => setFullName(e.target.value)} required 
                    />
                  </div>
                )}
                
                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <input 
                    type="email" className="form-control" placeholder="doctor@clinic.org"
                    value={email} onChange={e => setEmail(e.target.value)} required 
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Security Password</label>
                  <input 
                    type="password" className="form-control" placeholder="••••••••"
                    value={password} onChange={e => setPassword(e.target.value)} required 
                  />
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
                  {isRegister ? 'Create Account' : 'Access Dashboard'}
                </button>
              </form>

              <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>
                  {isRegister ? 'Already have an account? ' : 'First time deploying MetaboShield? '}
                </span>
                <button 
                  style={{ background: 'transparent', border: 'none', color: '#38bdf8', cursor: 'pointer', fontWeight: 600, padding: 0 }}
                  onClick={() => { setError(''); setIsRegister(!isRegister); }}
                >
                  {isRegister ? 'Login' : 'Register here'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* --- VIEW 2: PATIENT DASHBOARD --- */}
        {view === 'dashboard' && selectedPatient && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <div>
                <h1 className="gradient-text" style={{ fontSize: '2rem' }}>My Health Dashboard</h1>
                <p style={{ color: 'var(--text-muted)' }}>Welcome back, {selectedPatient.full_name}.</p>
              </div>
            </div>

            <div className="card" style={{ marginBottom: '2rem', textAlign: 'center', padding: '4rem 2rem' }}>
              <Heart size={48} style={{ color: '#f43f5e', marginBottom: '1rem', display: 'inline-block' }} />
              <h2 style={{ marginBottom: '1rem' }}>Ready for your Health Assessment?</h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', maxWidth: '500px', margin: '0 auto 2rem auto' }}>
                Take our comprehensive assessment to evaluate your risk for Diabetes, Heart Disease, and Obesity simultaneously.
              </p>
              <button className="btn btn-primary" onClick={() => setView('intake')} style={{ fontSize: '1.1rem', padding: '1rem 2rem' }}>
                Start New Assessment <ChevronRight size={20} />
              </button>
            </div>
          </div>
        )}

        {/* --- VIEW 3: INTAKE & DIAGNOSTICS FORM --- */}
        {view === 'intake' && selectedPatient && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <div>
                <h1 className="gradient-text" style={{ fontSize: '2rem' }}>Clinical Intake Form</h1>
                {/* EHR ID Locked for old patients */}
                <p style={{ color: 'var(--text-muted)' }}>
                  Patient Name: <strong>{selectedPatient.full_name}</strong> | EHR ID: <strong style={{ color: '#0ea5e9' }}>{selectedPatient.ehr_id}</strong>
                </p>
              </div>
              <button className="btn btn-secondary" onClick={() => { setView('dashboard'); setSuccess(''); }}>
                Back to Registry
              </button>
            </div>

            <div className="card">
              <div className="tabs-header">
                <button className={`tab-btn ${activeTab === 'demographics' ? 'active' : ''}`} onClick={() => setActiveTab('demographics')}>Demographics & Vitals</button>
                <button className={`tab-btn ${activeTab === 'lifestyle' ? 'active' : ''}`} onClick={() => setActiveTab('lifestyle')}>Lifestyle Habits</button>
                <button className={`tab-btn ${activeTab === 'diet' ? 'active' : ''}`} onClick={() => setActiveTab('diet')}>Dietary History (Missing Data Imputed)</button>
              </div>

              <div style={{ marginBottom: '2rem' }}>
                {activeTab === 'demographics' && (
                  <div className="grid-2">
                    <div>
                      <div className="form-group">
                        <label className="form-label">Age (Years)</label>
                        <div className="slider-container">
                          <input 
                            type="range" min="18" max="100" className="slider-input"
                            value={formData.age} onChange={e => setFormData({...formData, age: parseInt(e.target.value)})}
                          />
                          <span className="slider-val">{formData.age}</span>
                        </div>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Biological Sex</label>
                        <div className="radio-cards">
                          <div className={`radio-card ${selectedPatient.gender === 'Male' ? 'active' : ''}`} onClick={() => setSelectedPatient({...selectedPatient, gender: 'Male'})}>Male</div>
                          <div className={`radio-card ${selectedPatient.gender === 'Female' ? 'active' : ''}`} onClick={() => setSelectedPatient({...selectedPatient, gender: 'Female'})}>Female</div>
                          <div className={`radio-card ${selectedPatient.gender === 'Other' ? 'active' : ''}`} onClick={() => setSelectedPatient({...selectedPatient, gender: 'Other'})}>Other</div>
                        </div>
                      </div>

                      {/* Multimodal Height Unit Selector */}
                      <div className="form-group">
                        <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span>Height</span>
                          <select 
                            style={{ width: '130px', padding: '0.25rem 0.5rem', background: 'rgba(255,255,255,0.05)', fontSize: '0.8rem', height: 'auto' }}
                            className="form-control" value={heightUnit} onChange={e => setHeightUnit(e.target.value)}
                          >
                            <option value="Meters">Meters (m)</option>
                            <option value="Feet/Inches">Feet & Inches</option>
                          </select>
                        </label>
                        
                        {heightUnit === 'Meters' ? (
                          <input 
                            type="number" step="0.01" className="form-control"
                            value={heightM} onChange={e => setHeightM(parseFloat(e.target.value) || 0)}
                          />
                        ) : (
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <input 
                                type="number" className="form-control" placeholder="Ft"
                                value={heightFt} onChange={e => setHeightFt(parseInt(e.target.value) || 0)}
                              />
                              <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>ft</span>
                            </div>
                            <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <input 
                                type="number" className="form-control" placeholder="In"
                                value={heightIn} onChange={e => setHeightIn(parseFloat(e.target.value) || 0)}
                              />
                              <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>in</span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      {/* Multimodal Weight Unit Selector */}
                      <div className="form-group">
                        <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span>Weight</span>
                          <select 
                            style={{ width: '130px', padding: '0.25rem 0.5rem', background: 'rgba(255,255,255,0.05)', fontSize: '0.8rem', height: 'auto' }}
                            className="form-control" value={weightUnit} onChange={e => setWeightUnit(e.target.value)}
                          >
                            <option value="Kilograms">Kilograms (kg)</option>
                            <option value="Pounds">Pounds (lbs)</option>
                          </select>
                        </label>

                        {weightUnit === 'Kilograms' ? (
                          <input 
                            type="number" className="form-control"
                            value={weightKg} onChange={e => setWeightKg(parseFloat(e.target.value) || 0)}
                          />
                        ) : (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <input 
                              type="number" className="form-control" placeholder="Lbs"
                              value={weightLbs} onChange={e => setWeightLbs(parseFloat(e.target.value) || 0)}
                            />
                            <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>lbs</span>
                          </div>
                        )}
                      </div>

                      <div className="form-group">
                        <label className="form-label">Systolic Blood Pressure (mmHg)</label>
                        <div className="slider-container">
                          <input 
                            type="range" min="80" max="220" className="slider-input"
                            value={formData.blood_pressure} onChange={e => setFormData({...formData, blood_pressure: parseInt(e.target.value)})}
                          />
                          <span className="slider-val">{formData.blood_pressure}</span>
                        </div>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Cholesterol Level (mg/dL)</label>
                        <div className="slider-container">
                          <input 
                            type="range" min="100" max="400" className="slider-input"
                            value={formData.cholesterol_level} onChange={e => setFormData({...formData, cholesterol_level: parseInt(e.target.value)})}
                          />
                          <span className="slider-val">{formData.cholesterol_level}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'lifestyle' && (
                  <div className="grid-2">
                    <div>
                      <div className="form-group">
                        <label className="form-label">Smoking Status</label>
                        <div className="radio-cards">
                          <div className={`radio-card ${formData.smoking === 'Yes' ? 'active' : ''}`} onClick={() => setFormData({...formData, smoking: 'Yes'})}>Smoker</div>
                          <div className={`radio-card ${formData.smoking === 'No' ? 'active' : ''}`} onClick={() => setFormData({...formData, smoking: 'No'})}>Non-Smoker</div>
                        </div>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Physical Activity / Exercise Habits</label>
                        <select className="form-control" value={formData.exercise} onChange={e => setFormData({...formData, exercise: e.target.value})}>
                          <option value="Low">Low (Sedentary)</option>
                          <option value="Medium">Medium (Moderate walking/gym)</option>
                          <option value="High">High (Athletic/heavy active)</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Alcohol Consumption</label>
                        <select className="form-control" value={formData.alcohol} onChange={e => setFormData({...formData, alcohol: e.target.value})}>
                          <option value="None">None</option>
                          <option value="Sometimes">Sometimes</option>
                          <option value="Medium">Medium</option>
                          <option value="High">High (Heavy Drinker)</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <div className="form-group">
                        <label className="form-label">Perceived Stress Level</label>
                        <select className="form-control" value={formData.stress_level} onChange={e => setFormData({...formData, stress_level: e.target.value})}>
                          <option value="Low">Low</option>
                          <option value="Medium">Medium</option>
                          <option value="High">High</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Sleep Hours per Night</label>
                        <div className="slider-container">
                          <input 
                            type="range" min="3" max="12" step="0.5" className="slider-input"
                            value={formData.sleep_hours} onChange={e => setFormData({...formData, sleep_hours: parseFloat(e.target.value)})}
                          />
                          <span className="slider-val">{formData.sleep_hours}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'diet' && (
                  <div>
                    <div className="grid-2">
                      <div className="form-group">
                        <label className="form-label">Water Intake (Liters per day)</label>
                        <div className="slider-container">
                          <input 
                            type="range" min="0" max="6" step="0.5" className="slider-input"
                            value={formData.water_liters} onChange={e => setFormData({...formData, water_liters: parseFloat(e.target.value)})}
                          />
                          <span className="slider-val">{formData.water_liters} L</span>
                        </div>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Vegetables & Fruits Consumption</label>
                        <select className="form-control" value={formData.veg_freq} onChange={e => setFormData({...formData, veg_freq: parseFloat(e.target.value)})}>
                          <option value={1.0}>Never</option>
                          <option value={2.0}>Sometimes</option>
                          <option value={3.0}>Always</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Number of Meals a day</label>
                        <select className="form-control" value={formData.meals_count} onChange={e => setFormData({...formData, meals_count: parseFloat(e.target.value)})}>
                          <option value={1.0}>1 Meal</option>
                          <option value={2.0}>2 Meals</option>
                          <option value={3.0}>3 Meals</option>
                          <option value={4.0}>4+ Meals</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Snacking between meals</label>
                        <select className="form-control" value={formData.snack_freq} onChange={e => setFormData({...formData, snack_freq: e.target.value})}>
                          <option value="no">No Snacks</option>
                          <option value="Sometimes">Sometimes</option>
                          <option value="Frequently">Frequently</option>
                          <option value="Always">Always</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Family History of Heart Disease?</label>
                        <div className="radio-cards">
                          <div className={`radio-card ${formData.family_heart_disease === 'Yes' ? 'active' : ''}`} onClick={() => setFormData({...formData, family_heart_disease: 'Yes'})}>Yes</div>
                          <div className={`radio-card ${formData.family_heart_disease === 'No' ? 'active' : ''}`} onClick={() => setFormData({...formData, family_heart_disease: 'No'})}>No</div>
                        </div>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Family History of Overweight/Obesity?</label>
                        <div className="radio-cards">
                          <div className={`radio-card ${formData.family_overweight === 'Yes' ? 'active' : ''}`} onClick={() => setFormData({...formData, family_overweight: 'Yes'})}>Yes</div>
                          <div className={`radio-card ${formData.family_overweight === 'No' ? 'active' : ''}`} onClick={() => setFormData({...formData, family_overweight: 'No'})}>No</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '2rem', display: 'flex', justifyContent: 'space-between' }}>
                <button 
                  className="btn btn-secondary"
                  onClick={() => setActiveTab(activeTab === 'diet' ? 'lifestyle' : 'demographics')}
                  disabled={activeTab === 'demographics'}
                >
                  Previous Section
                </button>

                {activeTab !== 'diet' ? (
                  <button 
                    className="btn btn-primary"
                    onClick={() => setActiveTab(activeTab === 'demographics' ? 'lifestyle' : 'diet')}
                  >
                    Next Section
                  </button>
                ) : (
                  <button className="btn btn-primary" onClick={runDiagnostics} disabled={predictLoading} style={{ padding: '0.75rem 2.5rem' }}>
                    {predictLoading ? <RefreshCw className="spinner" size={16} /> : 'Process Multi-Disease Check'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* --- VIEW 4: DIAGNOSTICS REPORT --- */}
        {view === 'report' && results && selectedPatient && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <div>
                <h1 className="gradient-text" style={{ fontSize: '2rem' }}>Clinical Assessment Report</h1>
                <p style={{ color: 'var(--text-muted)' }}>ID: <strong>{selectedPatient.ehr_id}</strong> | Name: <strong>{selectedPatient.full_name}</strong></p>
              </div>
              <div className="no-print" style={{ display: 'flex', gap: '1rem' }}>
                <button className="btn btn-secondary" onClick={() => { setView('intake'); setResults(null); }}>
                  Adjust Metrics
                </button>
                <button className="btn btn-primary" onClick={() => window.print()}>
                  <FileText size={16} /> Print/Save PDF
                </button>
                <button className="btn btn-secondary" onClick={() => { setView('dashboard'); setResults(null); setSuccess(''); }}>
                  Dashboard Home
                </button>
              </div>
            </div>

            {/* Overall Severity Card */}
            <div className="card" style={{ marginBottom: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>Calculated Patient Health Risk</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Composite diagnostic score derived from combined diabetes, heart, and weight pipelines.</p>
                </div>
                <span className={`badge ${
                  results.overall_health_severity === 'Healthy' ? 'badge-healthy' :
                  results.overall_health_severity === 'Mild Risk' ? 'badge-mild' :
                  results.overall_health_severity === 'High Risk' ? 'badge-high' : 'badge-critical'
                }`} style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}>
                  {results.overall_health_severity}
                </span>
              </div>
            </div>

            {/* 3 Individual Disease Cards */}
            <div className="preset-grid" style={{ marginBottom: '2rem', alignItems: 'stretch' }}>
              {/* Obesity Card */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', height: '100%' }}>
                <h3 style={{ color: '#14b8a6', borderBottom: '1px solid rgba(20, 184, 166, 0.15)', paddingBottom: '0.5rem' }}>Obesity Staging</h3>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Classification</label>
                  <p style={{ fontSize: '1.1rem', fontWeight: '700' }}>{results.obesity_status}</p>
                </div>
                <div style={{ marginTop: 'auto' }}>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Calculated BMI</label>
                  <p style={{ fontSize: '1.1rem', fontWeight: '700' }}>{results.bmi} kg/m²</p>
                </div>
              </div>

              {/* Diabetes Card */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', height: '100%' }}>
                <h3 style={{ color: '#0ea5e9', borderBottom: '1px solid rgba(14, 165, 233, 0.15)', paddingBottom: '0.5rem' }}>Diabetes Staging</h3>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Classification</label>
                  <p style={{ fontSize: '1.1rem', fontWeight: '700' }}>{results.diabetes_status}</p>
                </div>
                <div style={{ marginTop: 'auto' }}>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Primary Indicator</label>
                  <p style={{ fontSize: '1.1rem', fontWeight: '700' }}>Glucose Baseline</p>
                </div>
              </div>

              {/* Cardiovascular Card */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', height: '100%' }}>
                <h3 style={{ color: '#f43f5e', borderBottom: '1px solid rgba(244, 63, 94, 0.15)', paddingBottom: '0.5rem' }}>Cardiovascular Staging</h3>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Risk Category</label>
                  <p style={{ fontSize: '1.1rem', fontWeight: '700' }}>{results.heart_disease_status}</p>
                </div>
                <div style={{ marginTop: 'auto' }}>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Primary Indicator</label>
                  <p style={{ fontSize: '1.1rem', fontWeight: '700' }}>BP & Cholesterol</p>
                </div>
              </div>
            </div>

            {/* Action Plans */}
            <div className="card">
              <h3 style={{ marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <FileText style={{ color: '#14b8a6' }} /> Personalized Health Action Plan
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {results.precautionary_measures.map((measure, idx) => {
                  const parts = measure.split('**');
                  return (
                    <div key={idx} style={{ display: 'flex', gap: '1rem', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-glass)', padding: '1rem', borderRadius: '8px', alignItems: 'center' }}>
                      <CheckCircle style={{ color: '#2dd4bf', flexShrink: 0 }} size={20} />
                      <p style={{ fontSize: '0.95rem' }}>
                        {parts.map((part, pidx) => pidx % 2 === 1 ? <strong key={pidx} style={{ color: '#38bdf8' }}>{part}</strong> : part)}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', borderTop: '1px solid var(--border-glass)' }}>
        © {new Date().getFullYear()} MetaboShield Diagnostic Pipeline. Confidential Clinical Research Portal.
      </footer>

      {/* Sidebar Settings Panel */}
      <div className="settings-sidebar">
        <button className="btn btn-secondary" onClick={() => setFontScale(Math.max(12, fontScale - 2))} title="Decrease Font">A-</button>
        <button className="btn btn-secondary" onClick={() => setFontScale(16)} title="Reset Font">A</button>
        <button className="btn btn-secondary" onClick={() => setFontScale(Math.min(22, fontScale + 2))} title="Increase Font">A+</button>
        
        <div style={{ width: '100%', height: '1px', background: 'var(--border-glass)' }}></div>

        <button 
          className="btn btn-secondary" 
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          title="Toggle Theme"
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </div>
    </div>
  );
}

export default App;
