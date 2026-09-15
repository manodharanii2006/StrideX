import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import Sidebar from './Sidebar';

// Auth pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Clinician pages
import Dashboard from './pages/Dashboard';
import Patients from './pages/Patients';
import NewAssessment from './pages/NewAssessment';
import ClinicianPatientProfile from './pages/ClinicianPatientProfile';

// Patient pages
import PatientDashboard from './pages/PatientDashboard';
import PatientNewAssessment from './pages/PatientNewAssessment';
import PatientAssessments from './pages/PatientAssessments';
import PatientBaseline from './pages/PatientBaseline';
import PatientProgress from './pages/PatientProgress';
import PatientReports from './pages/PatientReports';
import PatientProfile from './pages/PatientProfile';

// Shared
import Results from './pages/Results';

/* ─── Protected route wrapper with sidebar layout ─── */
function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />;

  // Role-based access control
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    // Send user to their own dashboard instead
    return <Navigate to={user?.role === 'patient' ? '/app/patient/dashboard' : '/app/dashboard'} replace />;
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <header className="topbar">
          <div className="topbar-breadcrumb">
            <strong>StrideX</strong> / <span>{user?.role === 'doctor' ? 'Clinical Portal' : 'Patient Portal'}</span>
          </div>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--clr-success)' }} title="System Online" />
            <span style={{ fontSize: '0.8rem', color: 'var(--clr-text-muted)' }}>Secure Environment</span>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}

/* ─── Landing Page ─── */
function LandingPage() {
  const navigate = useNavigate();
  return (
    <div>
      <nav className="public-nav">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 700, fontSize: '1.25rem', fontFamily: 'Space Grotesk' }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--clr-primary)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>S</div>
          StrideX
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <button className="btn btn-ghost" onClick={() => navigate('/login')}>Sign In</button>
          <button className="btn btn-primary" onClick={() => navigate('/register')}>Create Patient Account</button>
        </div>
      </nav>
      <div className="landing-hero">
        <div className="hero-grid-overlay" />
        <div style={{ position: 'relative', zIndex: 10, maxWidth: 800 }}>
          <h1 style={{ color: '#fff', fontSize: '3.5rem', lineHeight: 1.1, marginBottom: 24, letterSpacing: '-0.02em' }}>
            Understand movement.<br/>Measure gait.
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '1.25rem', lineHeight: 1.6, marginBottom: 40, maxWidth: 600 }}>
            StrideX transforms ordinary walking videos into quantitative biomechanical measurements using computer vision and physics-based gait analysis.
          </p>
          <div style={{ display: 'flex', gap: 16 }}>
            <button className="btn btn-primary btn-lg" onClick={() => navigate('/register')} style={{ fontSize: '1.1rem' }}>Get Started</button>
            <button className="btn btn-lg" style={{ background: 'rgba(255,255,255,0.1)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)' }} onClick={() => navigate('/login')}>Clinical Portal</button>
          </div>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.75rem', marginTop: 32 }}>
            StrideX is a biomechanical screening platform. Measurements are video-derived estimates and are not a medical diagnosis.
          </p>
        </div>
      </div>
    </div>
  );
}

/* ─── Routes ─── */
function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* ── Clinician routes ── */}
      <Route path="/app/dashboard"   element={<ProtectedRoute allowedRoles={['doctor']}><Dashboard /></ProtectedRoute>} />
      <Route path="/app/patients"    element={<ProtectedRoute allowedRoles={['doctor']}><Patients /></ProtectedRoute>} />
      <Route path="/app/patients/:id" element={<ProtectedRoute allowedRoles={['doctor']}><ClinicianPatientProfile /></ProtectedRoute>} />
      <Route path="/app/assess/new"  element={<ProtectedRoute allowedRoles={['doctor']}><NewAssessment /></ProtectedRoute>} />
      <Route path="/app/assessments" element={<ProtectedRoute allowedRoles={['doctor']}><Dashboard /></ProtectedRoute>} />
      <Route path="/app/analytics"   element={<ProtectedRoute allowedRoles={['doctor']}><Dashboard /></ProtectedRoute>} />
      <Route path="/app/reports"     element={<ProtectedRoute allowedRoles={['doctor']}><Dashboard /></ProtectedRoute>} />

      {/* ── Patient routes ── */}
      <Route path="/app/patient/dashboard"       element={<ProtectedRoute allowedRoles={['patient']}><PatientDashboard /></ProtectedRoute>} />
      <Route path="/app/patient/assessment/new"   element={<ProtectedRoute allowedRoles={['patient']}><PatientNewAssessment /></ProtectedRoute>} />
      <Route path="/app/patient/assessments"      element={<ProtectedRoute allowedRoles={['patient']}><PatientAssessments /></ProtectedRoute>} />
      <Route path="/app/patient/baseline"         element={<ProtectedRoute allowedRoles={['patient']}><PatientBaseline /></ProtectedRoute>} />
      <Route path="/app/patient/progress"         element={<ProtectedRoute allowedRoles={['patient']}><PatientProgress /></ProtectedRoute>} />
      <Route path="/app/patient/reports"          element={<ProtectedRoute allowedRoles={['patient']}><PatientReports /></ProtectedRoute>} />
      <Route path="/app/patient/profile"          element={<ProtectedRoute allowedRoles={['patient']}><PatientProfile /></ProtectedRoute>} />

      {/* ── Shared routes ── */}
      <Route path="/app/assess/:id/results" element={<ProtectedRoute><Results /></ProtectedRoute>} />

      {/* Fallbacks */}
      <Route path="/app/*" element={<Navigate to="/login" />} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}
