import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Activity, Eye, EyeOff, AlertCircle, ArrowRight, Lock } from 'lucide-react';
import { useAuth } from '../AuthContext';
import { login } from '../api';

export default function LoginPage() {
  const navigate = useNavigate();
  const { signIn } = useAuth();
  const [form,    setForm]    = useState({ email:'', password:'' });
  const [showPw,  setShowPw]  = useState(false);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  const fillDemo = (email) => setForm({ email, password:'demo1234' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const res = await login(form.email, form.password);
      signIn(res.data.user, res.data.token);
      const role = res.data.user?.role;
      navigate(role === 'patient' ? '/app/patient/dashboard' : '/app/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Sign in failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight:'100vh', display:'flex' }}>
      {/* Left branding panel */}
      <div style={{
        flex:'0 0 48%', display:'flex', flexDirection:'column',
        alignItems:'center', justifyContent:'center', padding:'64px',
        background:'linear-gradient(145deg,#0a1a2e 0%,#0f2342 55%,#1a3a6b 100%)',
        position:'relative', overflow:'hidden',
      }}>
        <div style={{
          position:'absolute', inset:0,
          backgroundImage:'linear-gradient(rgba(255,255,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.03) 1px,transparent 1px)',
          backgroundSize:'48px 48px',
        }} />
        <div style={{ position:'relative', zIndex:1, maxWidth:400, textAlign:'center' }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:12, marginBottom:40 }}>
            <div style={{ width:52,height:52,borderRadius:14,background:'linear-gradient(135deg,#1a56db,#3b82f6)',display:'flex',alignItems:'center',justifyContent:'center' }}>
              <Activity size={28} color="#fff" />
            </div>
            <span style={{ fontFamily:'Space Grotesk',fontSize:'2rem',fontWeight:700,color:'#fff' }}>StrideX</span>
          </div>
          <h1 style={{ fontSize:'1.75rem',fontWeight:700,color:'#fff',marginBottom:16,fontFamily:'Space Grotesk' }}>
            AI-Powered Gait Analysis
          </h1>
          <p style={{ color:'rgba(255,255,255,0.6)',lineHeight:1.7,marginBottom:40 }}>
            Clinical-grade biomechanical screening using computer vision, pose estimation and physics-based feature extraction.
          </p>
          {['MediaPipe pose estimation','Physics-based biomechanical extraction','Personal baseline comparison','Longitudinal risk screening'].map(f => (
            <div key={f} style={{ display:'flex',alignItems:'flex-start',gap:10,marginBottom:10,textAlign:'left' }}>
              <div style={{ width:6,height:6,borderRadius:'50%',background:'#3b82f6',flexShrink:0,marginTop:7 }} />
              <span style={{ color:'rgba(255,255,255,0.6)',fontSize:'0.875rem' }}>{f}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right login panel */}
      <div style={{ flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',padding:'48px',background:'#f8fafc' }}>
        <div style={{ width:'100%',maxWidth:400 }}>
          <Link to="/" style={{ display:'inline-flex',alignItems:'center',gap:6,color:'var(--clr-primary)',fontSize:'0.8125rem',marginBottom:28,textDecoration:'none' }}>
            ← Back to home
          </Link>
          <h2 style={{ fontFamily:'Space Grotesk',fontSize:'1.6rem',fontWeight:700,color:'var(--clr-navy)',marginBottom:4 }}>Welcome back</h2>
          <p style={{ color:'var(--clr-text-muted)',fontSize:'0.875rem',marginBottom:28 }}>
            Sign in to your StrideX account
          </p>

          {/* Demo shortcuts */}
          <div style={{ background:'#eff6ff',border:'1px solid #bfdbfe',borderRadius:10,padding:'14px 16px',marginBottom:24 }}>
            <p style={{ fontSize:'0.7rem',fontWeight:700,color:'#1d4ed8',marginBottom:8,textTransform:'uppercase',letterSpacing:'0.08em' }}>
              Demo Accounts
            </p>
            <div style={{ display:'flex',gap:8,alignItems:'center',flexWrap:'wrap' }}>
              <button onClick={() => fillDemo('doctor@stridex.health')} className="btn btn-secondary btn-sm" style={{ fontSize:'0.75rem' }}>
                🩺 Clinician
              </button>
              <button onClick={() => fillDemo('demo.patient@stridex.health')} className="btn btn-secondary btn-sm" style={{ fontSize:'0.75rem' }}>
                🧑 Patient
              </button>
              <span style={{ fontSize:'0.7rem',color:'#6b7280' }}>pw: demo1234</span>
            </div>
          </div>

          {error && (
            <div className="alert alert-danger" style={{ marginBottom:20 }}>
              <AlertCircle size={16} style={{ flexShrink:0 }} />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display:'flex',flexDirection:'column',gap:18 }}>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input className="form-control" type="email" autoComplete="email"
                placeholder="you@example.com"
                value={form.email} onChange={e => setForm(f => ({ ...f, email:e.target.value }))} required />
            </div>
            <div className="form-group">
              <label className="form-label" style={{ display:'flex',justifyContent:'space-between' }}>
                Password
                <span style={{ fontSize:'0.8rem',color:'var(--clr-primary)',cursor:'pointer' }}>Forgot password?</span>
              </label>
              <div style={{ position:'relative' }}>
                <input className="form-control" type={showPw ? 'text' : 'password'} autoComplete="current-password"
                  placeholder="••••••••"
                  value={form.password} onChange={e => setForm(f => ({ ...f, password:e.target.value }))}
                  required style={{ paddingRight:42 }} />
                <button type="button" onClick={() => setShowPw(p => !p)} style={{
                  position:'absolute',right:12,top:'50%',transform:'translateY(-50%)',
                  background:'none',border:'none',color:'var(--clr-text-muted)',cursor:'pointer',padding:0
                }}>
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button className="btn btn-primary btn-lg" type="submit" disabled={loading} style={{ marginTop:4 }}>
              {loading
                ? <><div className="spinner" style={{ width:18,height:18 }}/> Signing in…</>
                : <>Sign In <ArrowRight size={16} /></>}
            </button>
          </form>

          {/* Patient registration only — clinicians are pre-created */}
          <div style={{ marginTop:28,textAlign:'center',padding:'16px',background:'#f1f5f9',borderRadius:10 }}>
            <p style={{ fontSize:'0.8125rem',color:'var(--clr-text-muted)',marginBottom:8 }}>New to StrideX?</p>
            <Link to="/register">
              <button className="btn btn-secondary" style={{ width:'100%' }}>
                Create Patient Account
              </button>
            </Link>
          </div>

          <div style={{ marginTop:20,display:'flex',alignItems:'center',gap:6,justifyContent:'center' }}>
            <Lock size={12} style={{ color:'var(--clr-text-muted)' }} />
            <span style={{ fontSize:'0.7rem',color:'var(--clr-text-muted)' }}>
              Clinician accounts are provisioned by your administrator
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
