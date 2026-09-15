import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Activity, CheckCircle } from 'lucide-react';
import { useAuth } from '../AuthContext';
import { register } from '../api';

const STEPS = ['Basic Info', 'Activity Profile'];

export default function RegisterPage() {
  const navigate = useNavigate();
  const { signIn } = useAuth();
  const [step,    setStep]    = useState(0);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');
  const [form,    setForm]    = useState({
    name:'', email:'', password:'', confirmPassword:'',
    dob:'', gender:'Female',
    mobility_level:'Independent',
    activity_frequency:'Occasionally',
    walking_change:'No',
    assessment_goal:'Track my gait over time',
  });

  const set = (k, v) => setForm(f => ({ ...f, [k]:v }));

  const handleNext = (e) => {
    e.preventDefault();
    if (form.password !== form.confirmPassword) { setError('Passwords do not match'); return; }
    if (form.password.length < 6) { setError('Password must be at least 6 characters'); return; }
    setError(''); setStep(1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const res = await register(form);
      signIn(res.data.user, res.data.token);
      navigate('/app/patient/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight:'100vh', background:'#f8fafc', display:'flex', alignItems:'center', justifyContent:'center', padding:24 }}>
      <div style={{ width:'100%', maxWidth:520 }}>
        {/* Header */}
        <div style={{ textAlign:'center', marginBottom:32 }}>
          <div style={{ display:'inline-flex', alignItems:'center', gap:10, marginBottom:16 }}>
            <div style={{ width:44,height:44,borderRadius:12,background:'linear-gradient(135deg,#1a56db,#3b82f6)',display:'flex',alignItems:'center',justifyContent:'center' }}>
              <Activity size={24} color="#fff" />
            </div>
            <span style={{ fontFamily:'Space Grotesk',fontSize:'1.5rem',fontWeight:700,color:'var(--clr-navy)' }}>StrideX</span>
          </div>
          <h1 style={{ fontSize:'1.4rem',fontWeight:700,color:'var(--clr-navy)',marginBottom:4 }}>Create your patient account</h1>
          <p style={{ color:'var(--clr-text-muted)',fontSize:'0.875rem' }}>Step {step + 1} of 2 — {STEPS[step]}</p>
        </div>

        {/* Progress bar */}
        <div style={{ height:4,background:'var(--clr-border)',borderRadius:2,marginBottom:32,overflow:'hidden' }}>
          <div style={{ height:'100%',width:step===0?'50%':'100%',background:'var(--clr-primary)',transition:'width 0.4s ease' }} />
        </div>

        <div className="card" style={{ padding:32 }}>
          {error && <div className="alert alert-danger" style={{ marginBottom:20 }}>{error}</div>}

          {/* ── STEP 1 ── */}
          {step === 0 && (
            <form onSubmit={handleNext} style={{ display:'flex',flexDirection:'column',gap:20 }}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input required className="form-control" placeholder="e.g. Eleanor Vance"
                  value={form.name} onChange={e => set('name', e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input required type="email" className="form-control" placeholder="you@example.com"
                  value={form.email} onChange={e => set('email', e.target.value)} />
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
                <div className="form-group">
                  <label className="form-label">Date of Birth</label>
                  <input required type="date" className="form-control"
                    value={form.dob} onChange={e => set('dob', e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Gender</label>
                  <select className="form-control" value={form.gender} onChange={e => set('gender', e.target.value)}>
                    <option>Female</option><option>Male</option><option>Other</option>
                  </select>
                </div>
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
                <div className="form-group">
                  <label className="form-label">Password</label>
                  <input required type="password" className="form-control" placeholder="Min 6 chars"
                    value={form.password} onChange={e => set('password', e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Confirm Password</label>
                  <input required type="password" className="form-control" placeholder="Repeat"
                    value={form.confirmPassword} onChange={e => set('confirmPassword', e.target.value)} />
                </div>
              </div>
              <button type="submit" className="btn btn-primary" style={{ marginTop:8 }}>Continue →</button>
            </form>
          )}

          {/* ── STEP 2 ── */}
          {step === 1 && (
            <form onSubmit={handleSubmit} style={{ display:'flex',flexDirection:'column',gap:20 }}>
              <p style={{ fontSize:'0.875rem',color:'var(--clr-text-secondary)',marginBottom:4 }}>
                These details help establish your gait baseline and personalise your monitoring programme.
              </p>

              <div className="form-group">
                <label className="form-label">How would you describe your usual mobility?</label>
                <select className="form-control" value={form.mobility_level} onChange={e => set('mobility_level', e.target.value)}>
                  <option>Independent</option>
                  <option>Sometimes assisted</option>
                  <option>Usually assisted</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">How often do you walk or exercise?</label>
                <select className="form-control" value={form.activity_frequency} onChange={e => set('activity_frequency', e.target.value)}>
                  <option>Rarely</option><option>Occasionally</option><option>Regularly</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Have you noticed recent changes in your walking pattern?</label>
                <select className="form-control" value={form.walking_change} onChange={e => set('walking_change', e.target.value)}>
                  <option>No</option><option>Slight change</option><option>Significant change</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Main reason for using StrideX?</label>
                <select className="form-control" value={form.assessment_goal} onChange={e => set('assessment_goal', e.target.value)}>
                  <option>Track my gait over time</option>
                  <option>Monitor movement changes</option>
                  <option>Rehabilitation monitoring</option>
                  <option>General mobility assessment</option>
                </select>
              </div>

              <div style={{ display:'flex', gap:12, marginTop:8 }}>
                <button type="button" className="btn btn-secondary" style={{ flex:1 }} onClick={() => setStep(0)}>← Back</button>
                <button type="submit" className="btn btn-primary" style={{ flex:2 }} disabled={loading}>
                  {loading ? 'Creating account…' : <><CheckCircle size={16} /> Create Account</>}
                </button>
              </div>
            </form>
          )}
        </div>

        <p style={{ textAlign:'center',marginTop:20,fontSize:'0.8125rem',color:'var(--clr-text-muted)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color:'var(--clr-primary)',fontWeight:600,textDecoration:'none' }}>Sign In</Link>
        </p>
      </div>
    </div>
  );
}
