import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPatient, getPatientHistory, getPatientBaselineFor, getPatientTrendsFor, downloadPdf } from '../api';
import { User, Calendar, Activity, ChevronRight, Download, ArrowLeft } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler } from 'chart.js';
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

function RiskBadge({ level }) {
  const c = level==='HIGH'?'#dc2626':level==='MODERATE'?'#d97706':'#16a34a';
  const bg = level==='HIGH'?'#fef2f2':level==='MODERATE'?'#fffbeb':'#f0fdf4';
  return <span style={{ padding:'2px 10px',borderRadius:20,background:bg,color:c,fontWeight:700,fontSize:'0.75rem' }}>{level||'—'}</span>;
}

export default function ClinicianPatientProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [patient,     setPatient]     = useState(null);
  const [assessments, setAssessments] = useState([]);
  const [baseline,    setBaseline]    = useState({});
  const [trends,      setTrends]      = useState([]);
  const [latest,      setLatest]      = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [tab,         setTab]         = useState('overview');

  useEffect(() => {
    Promise.all([
      getPatient(id),
      getPatientHistory(id),
      getPatientBaselineFor(id),
      getPatientTrendsFor(id),
    ]).then(([p, a, b, t]) => {
      setPatient(p.data.patient);
      setLatest(p.data.latest_assessment);
      setAssessments(a.data.assessments || []);
      setBaseline(b.data.baseline || {});
      setTrends(t.data.data || []);
    }).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  const chartLabels = trends.map(t => new Date(t.date).toLocaleDateString('en-GB',{day:'numeric',month:'short'}));
  const chartOpts = {
    responsive:true, maintainAspectRatio:false,
    plugins:{ legend:{ position:'top', labels:{ usePointStyle:true, boxWidth:8, font:{size:11} } } },
    scales:{ x:{grid:{display:false}}, y:{grid:{color:'#f1f5f9'}} },
    elements:{ point:{radius:4}, line:{tension:0.35,borderWidth:2} },
  };

  if (loading) return <div className="page-wrapper"><div className="spinner" style={{margin:'60px auto'}} /></div>;
  if (!patient) return <div className="page-wrapper"><div className="alert alert-danger">Patient not found</div></div>;

  const latestFeatures = latest?.features || {};
  const risk = latest?.risk || {};

  const TABS = [
    { key:'overview',    label:'Overview' },
    { key:'assessments', label:'Assessment History' },
    { key:'analytics',   label:'Analytics' },
    { key:'risk',        label:'Risk Screening' },
  ];

  return (
    <div className="page-wrapper animate-in">
      {/* Back + Header */}
      <button className="btn btn-ghost btn-sm" onClick={() => navigate('/app/patients')} style={{ marginBottom:16 }}>
        <ArrowLeft size={14} /> Back to Patients
      </button>
      <div style={{ display:'flex', gap:20, marginBottom:28, alignItems:'center' }}>
        <div style={{ width:64,height:64,borderRadius:16,background:'linear-gradient(135deg,#1a56db,#3b82f6)',display:'flex',alignItems:'center',justifyContent:'center',color:'#fff',fontSize:'1.5rem',fontWeight:700,fontFamily:'Space Grotesk' }}>
          {patient.name?.split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase()}
        </div>
        <div>
          <h1 style={{ fontFamily:'Space Grotesk',fontSize:'1.5rem',fontWeight:700,color:'var(--clr-navy)',marginBottom:2 }}>{patient.name}</h1>
          <div style={{ fontSize:'0.8125rem',color:'var(--clr-text-muted)',display:'flex',gap:16 }}>
            <span>ID: <strong>{patient.id}</strong></span>
            <span>Age: <strong>{patient.age ?? '—'}</strong></span>
            <span>Gender: <strong>{patient.gender || '—'}</strong></span>
          </div>
        </div>
        <div style={{ marginLeft:'auto', display:'flex', gap:12 }}>
          {latest && <RiskBadge level={latest.risk_level} />}
          {latest && <span style={{ fontFamily:'Space Grotesk',fontWeight:700,fontSize:'1.25rem',color:'var(--clr-navy)' }}>{latest.gait_score}/100</span>}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display:'flex', gap:4, borderBottom:'2px solid var(--clr-border)', marginBottom:24 }}>
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            padding:'10px 20px', border:'none', cursor:'pointer',
            background:'none', fontWeight: tab===t.key?700:400,
            color: tab===t.key?'var(--clr-primary)':'var(--clr-text-muted)',
            borderBottom: tab===t.key?'2px solid var(--clr-primary)':'2px solid transparent',
            marginBottom:-2, fontSize:'0.875rem',
          }}>{t.label}</button>
        ))}
      </div>

      {/* ── OVERVIEW ─────────────────────────────────────────────── */}
      {tab === 'overview' && (
        <>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16, marginBottom:24 }}>
            {[
              { label:'Cadence',       value:latestFeatures.cadence?.toFixed(1),       unit:'steps/min' },
              { label:'Walking Speed', value:latestFeatures.walking_speed?.toFixed(2),  unit:'m/s' },
              { label:'Symmetry',      value:latestFeatures.symmetry_score?.toFixed(1), unit:'%' },
              { label:'L Knee ROM',    value:latestFeatures.left_knee_rom?.toFixed(1),  unit:'°' },
              { label:'R Knee ROM',    value:latestFeatures.right_knee_rom?.toFixed(1), unit:'°' },
              { label:'Postural Sway', value:latestFeatures.postural_sway?.toFixed(4),  unit:'' },
            ].map(m => (
              <div key={m.label} style={{ padding:'16px', background:'var(--clr-surface-2)', borderRadius:10 }}>
                <div style={{ fontSize:'0.7rem',fontWeight:600,color:'var(--clr-text-muted)',textTransform:'uppercase',marginBottom:6 }}>{m.label}</div>
                <div style={{ fontFamily:'Space Grotesk',fontSize:'1.5rem',fontWeight:700,color:'var(--clr-navy)' }}>
                  {m.value ?? '—'} <span style={{ fontSize:'0.75rem',color:'var(--clr-text-muted)',fontWeight:400 }}>{m.unit}</span>
                </div>
              </div>
            ))}
          </div>
          {/* Baseline table */}
          {Object.keys(baseline).length > 0 && (
            <div className="card">
              <div className="card-header"><div className="card-title">Personal Baseline Comparison</div></div>
              <table className="data-table">
                <thead><tr><th>Metric</th><th>Baseline</th><th>Current</th><th>Change</th></tr></thead>
                <tbody>
                  {Object.entries(baseline).map(([k,bv]) => {
                    const cv = latestFeatures[k];
                    const pct = cv!=null ? ((cv-bv)/bv*100) : null;
                    return (
                      <tr key={k}>
                        <td style={{fontWeight:600}}>{k.replace(/_/g,' ').replace(/\b\w/g,l=>l.toUpperCase())}</td>
                        <td style={{fontFamily:'Space Grotesk'}}>{Number(bv).toFixed(2)}</td>
                        <td style={{fontFamily:'Space Grotesk'}}>{cv!=null?Number(cv).toFixed(2):'—'}</td>
                        <td style={{fontFamily:'Space Grotesk',color:pct!=null&&Math.abs(pct)<5?'#16a34a':pct>0?'#1a56db':'#d97706',fontWeight:600}}>
                          {pct!=null?`${pct>0?'+':''}${pct.toFixed(1)}%`:'—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* ── ASSESSMENTS ──────────────────────────────────────────── */}
      {tab === 'assessments' && (
        <div className="card" style={{ padding:0 }}>
          <table className="data-table">
            <thead><tr><th>ID</th><th>Date</th><th>Score</th><th>Risk</th><th>Status</th><th>Report</th></tr></thead>
            <tbody>
              {assessments.map(a => (
                <tr key={a.id}>
                  <td style={{fontFamily:'Space Grotesk',fontSize:'0.8rem'}}>{a.id}</td>
                  <td>{a.date?new Date(a.date).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}):'—'}</td>
                  <td style={{fontFamily:'Space Grotesk',fontWeight:700}}>{a.gait_score??'—'}</td>
                  <td><RiskBadge level={a.risk_level} /></td>
                  <td><span style={{fontSize:'0.75rem',fontWeight:600,color:a.status==='completed'?'#16a34a':'#64748b'}}>{a.status}</span></td>
                  <td>
                    {a.status==='completed' && (
                      <div style={{display:'flex',gap:8}}>
                        <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/app/assess/${a.id}/results`)}><ChevronRight size={14}/>View</button>
                        <button className="btn btn-ghost btn-sm" onClick={async()=>{
                          const r=await downloadPdf(a.id);const u=URL.createObjectURL(new Blob([r.data]));
                          Object.assign(document.createElement('a'),{href:u,download:`StrideX_${a.id}.pdf`}).click();
                        }}><Download size={14}/>PDF</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── ANALYTICS ────────────────────────────────────────────── */}
      {tab === 'analytics' && (
        trends.length >= 2 ? (
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
            {[
              {key:'gait_score',label:'Gait Score',color:'#1a56db'},
              {key:'cadence',label:'Cadence',color:'#10b981'},
              {key:'symmetry_score',label:'Symmetry',color:'#8b5cf6'},
              {key:'left_knee_rom',label:'Left Knee ROM',color:'#f59e0b'},
              {key:'postural_sway',label:'Postural Sway',color:'#ef4444'},
            ].map(ch => {
              const bv = baseline[ch.key];
              return (
                <div className="card" key={ch.key}>
                  <div className="card-header"><div className="card-title">{ch.label}</div></div>
                  <div style={{height:200}}>
                    <Line data={{labels:chartLabels,datasets:[
                      {label:ch.label,data:trends.map(t=>t[ch.key]),borderColor:ch.color,backgroundColor:`${ch.color}12`,fill:true},
                      ...(bv!=null?[{label:'Baseline',data:trends.map(()=>bv),borderColor:'#94a3b8',borderDash:[6,4],pointRadius:0,borderWidth:1.5}]:[]),
                    ]}} options={chartOpts}/>
                  </div>
                </div>
              );
            })}
          </div>
        ) : <div className="card" style={{textAlign:'center',padding:40}}><p style={{color:'var(--clr-text-muted)'}}>Need 2+ assessments for analytics</p></div>
      )}

      {/* ── RISK ─────────────────────────────────────────────────── */}
      {tab === 'risk' && (
        <>
          <div className="card" style={{ marginBottom:20, display:'flex', alignItems:'center', gap:20 }}>
            <div>
              <div style={{ fontSize:'0.75rem', fontWeight:700, color:'var(--clr-text-muted)', textTransform:'uppercase', marginBottom:4 }}>Overall Screening Risk</div>
              <RiskBadge level={latest?.risk_level} />
            </div>
            <div style={{ flex:1, fontSize:'0.875rem', color:'var(--clr-text-secondary)' }}>
              {risk.clinical_narrative || 'No clinical narrative available.'}
            </div>
          </div>
          {(risk.factors || []).length > 0 && (
            <div className="card" style={{ padding:0 }}>
              <table className="data-table">
                <thead><tr><th>Factor</th><th>Score</th><th>Status</th><th>Explanation</th></tr></thead>
                <tbody>
                  {risk.factors.map((f,i) => (
                    <tr key={i}>
                      <td style={{fontWeight:600}}>{f.name}</td>
                      <td style={{fontFamily:'Space Grotesk',fontWeight:700}}>{f.score}</td>
                      <td><span style={{
                        padding:'2px 10px',borderRadius:20,fontSize:'0.75rem',fontWeight:700,
                        background:f.status==='danger'?'#fef2f2':f.status==='warning'?'#fffbeb':'#f0fdf4',
                        color:f.status==='danger'?'#dc2626':f.status==='warning'?'#d97706':'#16a34a',
                      }}>{f.status}</span></td>
                      <td style={{fontSize:'0.875rem',color:'var(--clr-text-secondary)'}}>{f.label}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
