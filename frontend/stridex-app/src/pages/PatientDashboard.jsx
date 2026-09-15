import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { getPatientDashboard, getPatientTrends, downloadPdf } from '../api';
import { Activity, TrendingUp, AlertTriangle, Calendar, Plus, ChevronRight, Target } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Title, Tooltip, Legend
} from 'chart.js';
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

function RiskBadge({ level }) {
  const map = {
    HIGH:     { bg:'#fef2f2', color:'#dc2626', label:'High' },
    MODERATE: { bg:'#fffbeb', color:'#d97706', label:'Moderate' },
    LOW:      { bg:'#f0fdf4', color:'#16a34a', label:'Low' },
  };
  const s = map[level] || { bg:'#f1f5f9', color:'#64748b', label: level || 'Unknown' };
  return (
    <span style={{ padding:'3px 12px', borderRadius:20, background:s.bg, color:s.color, fontWeight:700, fontSize:'0.8rem' }}>
      {s.label}
    </span>
  );
}

function MetricCard({ label, value, unit, icon: Icon, color='var(--clr-primary)' }) {
  return (
    <div className="card" style={{ flex:1, minWidth:160 }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12 }}>
        <span style={{ fontSize:'0.75rem', fontWeight:700, color:'var(--clr-text-muted)', textTransform:'uppercase', letterSpacing:'0.06em' }}>{label}</span>
        {Icon && <div style={{ width:32, height:32, borderRadius:8, background:`${color}15`, display:'flex', alignItems:'center', justifyContent:'center' }}><Icon size={16} color={color} /></div>}
      </div>
      <div style={{ fontFamily:'Space Grotesk', fontSize:'2rem', fontWeight:700, color:'var(--clr-navy)', lineHeight:1 }}>
        {value ?? '—'}
        {unit && <span style={{ fontSize:'0.9rem', fontWeight:500, color:'var(--clr-text-muted)', marginLeft:4 }}>{unit}</span>}
      </div>
    </div>
  );
}

export default function PatientDashboard() {
  const { user } = useAuth();
  const navigate  = useNavigate();
  const [dash,    setDash]    = useState(null);
  const [trends,  setTrends]  = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getPatientDashboard(), getPatientTrends()])
      .then(([d, t]) => {
        setDash(d.data);
        setTrends(t.data.data || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const hour = new Date().getHours();
  const greet = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  const latest = dash?.latest_assessment;
  const latestFeatures = latest?.features || {};

  // Build chart data from trends
  const chartLabels = trends.map(t => new Date(t.date).toLocaleDateString('en-GB', { day:'numeric', month:'short' }));
  const scoreData   = trends.map(t => t.gait_score);
  const cadenceData = trends.map(t => t.cadence);

  const chartOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display:false } },
      y: { grid: { color:'var(--clr-border)' } }
    },
    elements: { point: { radius:4, hoverRadius:6 }, line: { tension:0.3, borderWidth:2 } },
  };

  if (loading) return <div className="page-wrapper"><div className="spinner" style={{ margin:'60px auto' }} /></div>;

  return (
    <div className="page-wrapper animate-in">
      {/* Header */}
      <div style={{ marginBottom:32 }}>
        <h1 style={{ fontFamily:'Space Grotesk', fontSize:'1.75rem', fontWeight:700, color:'var(--clr-navy)', marginBottom:4 }}>
          {greet}, {user?.name?.split(' ')[0] || 'there'} 👋
        </h1>
        <div style={{ display:'flex', gap:20, fontSize:'0.8125rem', color:'var(--clr-text-muted)' }}>
          <span>Patient ID: <strong style={{ color:'var(--clr-navy)' }}>{user?.id}</strong></span>
          {latest && <span>Last assessment: <strong style={{ color:'var(--clr-navy)' }}>{new Date(latest.date).toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric'})}</strong></span>}
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:28 }}>
        <MetricCard
          label="Latest Gait Score"
          value={latest ? `${latest.gait_score}` : '—'}
          unit={latest ? '/100' : ''}
          icon={Activity}
          color="var(--clr-primary)"
        />
        <div className="card" style={{ flex:1, minWidth:160 }}>
          <div style={{ fontSize:'0.75rem', fontWeight:700, color:'var(--clr-text-muted)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:12 }}>Current Risk</div>
          {latest ? <RiskBadge level={latest.risk_level} /> : <span style={{ color:'var(--clr-text-muted)' }}>No assessment yet</span>}
        </div>
        <MetricCard
          label="Assessments"
          value={dash?.total_assessments ?? 0}
          icon={Calendar}
          color="#8b5cf6"
        />
        <div className="card" style={{ flex:1, minWidth:160 }}>
          <div style={{ fontSize:'0.75rem', fontWeight:700, color:'var(--clr-text-muted)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:12 }}>Baseline</div>
          {dash?.has_baseline
            ? <span style={{ padding:'3px 12px', borderRadius:20, background:'#f0fdf4', color:'#16a34a', fontWeight:700, fontSize:'0.8rem' }}>Established ✓</span>
            : <span style={{ padding:'3px 12px', borderRadius:20, background:'#fffbeb', color:'#d97706', fontWeight:700, fontSize:'0.8rem' }}>Not yet</span>}
        </div>
      </div>

      {/* New Assessment CTA */}
      {!latest && (
        <div className="card" style={{ background:'linear-gradient(135deg,#eff6ff,#f0f9ff)', border:'1px solid #bfdbfe', marginBottom:24, display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <div>
            <h3 style={{ color:'var(--clr-navy)', marginBottom:6 }}>Start your first gait assessment</h3>
            <p style={{ color:'var(--clr-text-muted)', fontSize:'0.875rem' }}>Upload a short walking video to establish your personal gait baseline.</p>
          </div>
          <button className="btn btn-primary" onClick={() => navigate('/app/patient/assessment/new')} style={{ whiteSpace:'nowrap' }}>
            <Plus size={16} /> New Assessment
          </button>
        </div>
      )}

      {/* Trend charts (only if 2+ assessments) */}
      {trends.length >= 2 ? (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20, marginBottom:24 }}>
          <div className="card">
            <div className="card-header"><div className="card-title">Gait Score Over Time</div></div>
            <div style={{ height:220 }}>
              <Line data={{ labels:chartLabels, datasets:[{ label:'Gait Score', data:scoreData, borderColor:'#1a56db', backgroundColor:'rgba(26,86,219,0.1)', fill:true }] }} options={chartOpts} />
            </div>
          </div>
          <div className="card">
            <div className="card-header"><div className="card-title">Cadence (steps/min)</div></div>
            <div style={{ height:220 }}>
              <Line data={{ labels:chartLabels, datasets:[{ label:'Cadence', data:cadenceData, borderColor:'#10b981', backgroundColor:'rgba(16,185,129,0.1)', fill:true }] }} options={chartOpts} />
            </div>
          </div>
        </div>
      ) : trends.length === 1 ? (
        <div className="card" style={{ background:'#f8fafc', border:'1px dashed var(--clr-border)', textAlign:'center', padding:'40px 24px', marginBottom:24 }}>
          <Target size={40} style={{ color:'var(--clr-primary)', margin:'0 auto 16px' }} />
          <h3 style={{ color:'var(--clr-navy)', marginBottom:8 }}>Baseline established ✓</h3>
          <p style={{ color:'var(--clr-text-muted)', fontSize:'0.875rem', maxWidth:400, margin:'0 auto' }}>
            Complete another assessment to compare against your baseline and view progress trends.
          </p>
          <button className="btn btn-primary" style={{ marginTop:20 }} onClick={() => navigate('/app/patient/assessment/new')}>
            <Plus size={16} /> New Assessment
          </button>
        </div>
      ) : null}

      {/* Latest metrics summary */}
      {latest && (
        <div className="card">
          <div className="card-header" style={{ justifyContent:'space-between' }}>
            <div className="card-title">Latest Assessment — {new Date(latest.date).toLocaleDateString('en-GB', { day:'numeric', month:'long', year:'numeric' })}</div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/app/assess/${latest.id}/results`)}>
              View Full Report <ChevronRight size={14} />
            </button>
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16 }}>
            {[
              { label:'Cadence',       value:latestFeatures.cadence?.toFixed(1),         unit:'steps/min' },
              { label:'Walking Speed', value:latestFeatures.walking_speed?.toFixed(2),    unit:'m/s' },
              { label:'Symmetry',      value:latestFeatures.symmetry_score?.toFixed(1),   unit:'%' },
              { label:'L Knee ROM',    value:latestFeatures.left_knee_rom?.toFixed(1),    unit:'°' },
              { label:'R Knee ROM',    value:latestFeatures.right_knee_rom?.toFixed(1),   unit:'°' },
              { label:'Postural Sway', value:latestFeatures.postural_sway?.toFixed(4),    unit:'' },
            ].map(m => (
              <div key={m.label} style={{ padding:'12px 16px', background:'var(--clr-surface-2)', borderRadius:8 }}>
                <div style={{ fontSize:'0.7rem', color:'var(--clr-text-muted)', fontWeight:600, textTransform:'uppercase', marginBottom:4 }}>{m.label}</div>
                <div style={{ fontFamily:'Space Grotesk', fontSize:'1.25rem', fontWeight:700, color:'var(--clr-navy)' }}>
                  {m.value ?? '—'} <span style={{ fontSize:'0.75rem', color:'var(--clr-text-muted)', fontWeight:400 }}>{m.unit}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
