import React, { useEffect, useState } from 'react';
import { getPatientBaseline, getPatientTrends } from '../api';
import { Target, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Tooltip, Legend
} from 'chart.js';
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const METRICS = [
  { key:'cadence',        label:'Cadence',        unit:'steps/min', higherBetter:true,  refRange:'100–115' },
  { key:'walking_speed',  label:'Walking Speed',   unit:'m/s',       higherBetter:true,  refRange:'1.2–1.4' },
  { key:'symmetry_score', label:'Symmetry Score',  unit:'%',         higherBetter:true,  refRange:'> 90%' },
  { key:'left_knee_rom',  label:'Left Knee ROM',   unit:'°',         higherBetter:true,  refRange:'55–70°' },
  { key:'right_knee_rom', label:'Right Knee ROM',  unit:'°',         higherBetter:true,  refRange:'55–70°' },
  { key:'postural_sway',  label:'Postural Sway',   unit:'',          higherBetter:false, refRange:'< 0.05' },
];

function ChangeIndicator({ pct, higherBetter }) {
  if (pct === null || pct === undefined) return null;
  const improved = (pct > 0 && higherBetter) || (pct < 0 && !higherBetter);
  const stable   = Math.abs(pct) < 3;
  const color    = stable ? '#64748b' : improved ? '#16a34a' : '#dc2626';
  const Icon     = stable ? Minus : improved ? TrendingUp : TrendingDown;
  return (
    <div style={{ display:'flex', alignItems:'center', gap:4, color, fontSize:'0.8rem', fontWeight:600 }}>
      <Icon size={14} />
      {pct > 0 ? '+' : ''}{pct.toFixed(1)}%
    </div>
  );
}

export default function PatientBaseline() {
  const [baseline, setBaseline] = useState({});
  const [trends,   setTrends]   = useState([]);
  const [estDate,  setEstDate]  = useState(null);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    Promise.all([getPatientBaseline(), getPatientTrends()])
      .then(([b, t]) => {
        setBaseline(b.data.baseline || {});
        setEstDate(b.data.established_at);
        setTrends(t.data.data || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const latest = trends[trends.length - 1] || null;

  const chartLabels = trends.map(t => new Date(t.date).toLocaleDateString('en-GB', { day:'numeric', month:'short' }));
  const chartOpts   = {
    responsive:true, maintainAspectRatio:false,
    plugins:{ legend:{ position:'top', labels:{ usePointStyle:true, boxWidth:8, font:{ size:11 } } } },
    scales:{ x:{ grid:{ display:false } }, y:{ grid:{ color:'var(--clr-border)' } } },
    elements:{ point:{ radius:4 }, line:{ tension:0.3, borderWidth:2 } },
  };

  if (loading) return <div className="page-wrapper"><div className="spinner" style={{ margin:'60px auto' }} /></div>;

  const hasBaseline = Object.keys(baseline).length > 0;

  return (
    <div className="page-wrapper animate-in">
      <div className="page-header">
        <h1 className="page-title">My Personal Baseline</h1>
        <p className="page-subtitle">
          Your personal baseline was established from your first valid assessment and is used to track changes over time.
        </p>
      </div>

      {!hasBaseline ? (
        <div className="card" style={{ textAlign:'center', padding:'60px' }}>
          <Target size={48} style={{ color:'var(--clr-border)', margin:'0 auto 16px' }} />
          <h3 style={{ color:'var(--clr-navy)', marginBottom:8 }}>No baseline established yet</h3>
          <p style={{ color:'var(--clr-text-muted)' }}>Complete your first gait assessment to establish your personal baseline.</p>
        </div>
      ) : (
        <>
          {estDate && (
            <div style={{ marginBottom:20, padding:'12px 16px', background:'#f0fdf4', border:'1px solid #bbf7d0', borderRadius:10, display:'inline-flex', gap:8, alignItems:'center', fontSize:'0.875rem', color:'#15803d', fontWeight:600 }}>
              <Target size={16} />
              Baseline established: {new Date(estDate).toLocaleDateString('en-GB', { day:'numeric', month:'long', year:'numeric' })}
            </div>
          )}

          {/* Comparison table */}
          <div className="card" style={{ marginBottom:24 }}>
            <div className="card-header"><div className="card-title">Baseline vs. Current Values</div></div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Your Baseline</th>
                  <th>Latest Value</th>
                  <th>Change</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {METRICS.map(m => {
                  const bVal    = baseline[m.key];
                  const cVal    = latest?.[m.key] ?? latest?.features?.[m.key];
                  const pct     = (bVal != null && cVal != null) ? ((cVal - bVal) / bVal) * 100 : null;
                  const stable  = pct !== null && Math.abs(pct) < 5;
                  const improved= pct !== null && ((pct > 0 && m.higherBetter) || (pct < 0 && !m.higherBetter));
                  const statusLabel = pct === null ? '—' : stable ? 'Within baseline' : improved ? 'Improved' : 'Monitor';
                  const statusColor = pct === null ? '#64748b' : stable ? '#16a34a' : improved ? '#1a56db' : '#d97706';
                  return (
                    <tr key={m.key}>
                      <td className="font-medium">{m.label}</td>
                      <td style={{ fontFamily:'Space Grotesk', fontWeight:700 }}>
                        {bVal != null ? `${Number(bVal).toFixed(2)} ${m.unit}` : '—'}
                      </td>
                      <td style={{ fontFamily:'Space Grotesk', fontWeight:700 }}>
                        {cVal != null ? `${Number(cVal).toFixed(2)} ${m.unit}` : '—'}
                      </td>
                      <td><ChangeIndicator pct={pct} higherBetter={m.higherBetter} /></td>
                      <td><span style={{ fontSize:'0.8rem', fontWeight:600, color:statusColor }}>{statusLabel}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Longitudinal charts */}
          {trends.length >= 2 && (
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
              {[
                { key:'cadence',        label:'Cadence (steps/min)',   color:'#1a56db' },
                { key:'symmetry_score', label:'Symmetry Score (%)',    color:'#10b981' },
                { key:'left_knee_rom',  label:'Left Knee ROM (°)',     color:'#8b5cf6' },
                { key:'postural_sway',  label:'Postural Sway',         color:'#f59e0b' },
              ].map(ch => {
                const bVal = baseline[ch.key];
                return (
                  <div className="card" key={ch.key}>
                    <div className="card-header"><div className="card-title">{ch.label}</div></div>
                    <div style={{ height:200 }}>
                      <Line
                        data={{
                          labels: chartLabels,
                          datasets: [
                            {
                              label: 'Measurement',
                              data: trends.map(t => t[ch.key] ?? t.features?.[ch.key]),
                              borderColor: ch.color,
                              backgroundColor: `${ch.color}15`,
                              fill: true,
                            },
                            ...(bVal != null ? [{
                              label: 'Your Baseline',
                              data: trends.map(() => bVal),
                              borderColor: '#94a3b8',
                              borderDash: [6, 4],
                              pointRadius: 0,
                              borderWidth: 1.5,
                            }] : []),
                          ],
                        }}
                        options={chartOpts}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      <div style={{ marginTop:24, padding:'12px 16px', background:'#fffbeb', borderRadius:8, border:'1px solid #fef3c7', fontSize:'0.8rem', color:'#92400e' }}>
        ⚠️ StrideX is a biomechanical screening and monitoring research platform. Measurements are video-derived estimates and are not a medical diagnosis.
      </div>
    </div>
  );
}
