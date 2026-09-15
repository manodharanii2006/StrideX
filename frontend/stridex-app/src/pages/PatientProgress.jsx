import React, { useEffect, useState } from 'react';
import { getPatientTrends, getPatientBaseline } from '../api';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const CHARTS = [
  { key:'gait_score',     label:'Gait Score',           color:'#1a56db', unit:'/100' },
  { key:'cadence',        label:'Cadence',              color:'#10b981', unit:'steps/min' },
  { key:'symmetry_score', label:'Symmetry Score',       color:'#8b5cf6', unit:'%' },
  { key:'left_knee_rom',  label:'Left Knee ROM',        color:'#f59e0b', unit:'°' },
  { key:'right_knee_rom', label:'Right Knee ROM',       color:'#ec4899', unit:'°' },
  { key:'postural_sway',  label:'Postural Sway',        color:'#ef4444', unit:'' },
];

export default function PatientProgress() {
  const [trends,   setTrends]   = useState([]);
  const [baseline, setBaseline] = useState({});
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    Promise.all([getPatientTrends(), getPatientBaseline()])
      .then(([t, b]) => { setTrends(t.data.data || []); setBaseline(b.data.baseline || {}); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const labels = trends.map(t => new Date(t.date).toLocaleDateString('en-GB', { day:'numeric', month:'short' }));

  const chartOpts = {
    responsive:true, maintainAspectRatio:false,
    plugins:{ legend:{ position:'top', labels:{ usePointStyle:true, boxWidth:8, font:{ size:11 } } } },
    scales:{ x:{ grid:{ display:false } }, y:{ grid:{ color:'#f1f5f9' } } },
    elements:{ point:{ radius:4, hoverRadius:6 }, line:{ tension:0.35, borderWidth:2 } },
  };

  if (loading) return <div className="page-wrapper"><div className="spinner" style={{ margin:'60px auto' }} /></div>;

  if (trends.length < 2) return (
    <div className="page-wrapper animate-in">
      <div className="page-header"><h1 className="page-title">Progress</h1></div>
      <div className="card" style={{ textAlign:'center', padding:'60px' }}>
        <h3 style={{ color:'var(--clr-navy)', marginBottom:8 }}>Not enough data yet</h3>
        <p style={{ color:'var(--clr-text-muted)' }}>Complete at least two assessments to view progress trends.</p>
      </div>
    </div>
  );

  return (
    <div className="page-wrapper animate-in">
      <div className="page-header">
        <h1 className="page-title">Progress</h1>
        <p className="page-subtitle">Longitudinal trend analysis across {trends.length} assessments</p>
      </div>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
        {CHARTS.map(ch => {
          const bVal = baseline[ch.key];
          return (
            <div className="card" key={ch.key}>
              <div className="card-header"><div className="card-title">{ch.label} <span style={{ fontSize:'0.75rem', color:'var(--clr-text-muted)', fontWeight:400 }}>({ch.unit})</span></div></div>
              <div style={{ height:220 }}>
                <Line data={{
                  labels,
                  datasets: [
                    { label:ch.label, data:trends.map(t => t[ch.key]), borderColor:ch.color, backgroundColor:`${ch.color}12`, fill:true },
                    ...(bVal != null ? [{ label:'Baseline', data:trends.map(() => bVal), borderColor:'#94a3b8', borderDash:[6,4], pointRadius:0, borderWidth:1.5 }] : []),
                  ],
                }} options={chartOpts} />
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ marginTop:24, padding:'12px 16px', background:'#fffbeb', borderRadius:8, border:'1px solid #fef3c7', fontSize:'0.8rem', color:'#92400e' }}>
        ⚠️ StrideX is a biomechanical screening research platform. Measurements are video-derived estimates and are not a medical diagnosis.
      </div>
    </div>
  );
}
