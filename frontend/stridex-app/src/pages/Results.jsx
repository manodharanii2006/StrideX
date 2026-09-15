import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAssessment, getTimeseries, downloadPdf } from '../api';
import { Download, ChevronLeft, Calendar, User, Activity, AlertTriangle, Play, Pause, AlertCircle } from 'lucide-react';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function RiskPill({ level }) {
  const c = level === 'HIGH' ? 'var(--clr-danger)' : level === 'MODERATE' ? 'var(--clr-warning)' : 'var(--clr-success)';
  const bg = level === 'HIGH' ? 'var(--clr-danger-light)' : level === 'MODERATE' ? 'var(--clr-warning-light)' : 'var(--clr-success-light)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 14px', borderRadius: 20, background: bg, color: c, fontWeight: 700, fontSize: '0.8125rem', letterSpacing: '0.05em' }}>
      <span style={{ display: 'block', width: 8, height: 8, borderRadius: '50%', background: c }} />
      {level || 'UNKNOWN'}
    </div>
  );
}

export default function Results() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [ts, setTs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [activeTab, setActiveTab] = useState('Overview');

  useEffect(() => {
    Promise.all([
      getAssessment(id).catch(e => { throw e; }),
      getTimeseries(id).catch(() => ({ data: null })) // ts is optional initially
    ]).then(([resAsm, resTs]) => {
      setData(resAsm.data.assessment);
      setTs(resTs.data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setError('Failed to load assessment data.');
      setLoading(false);
    });
  }, [id]);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const res = await downloadPdf(id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `StrideX_Report_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (e) {
      alert('Failed to generate PDF');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) return <div className="page-wrapper"><div className="spinner mx-auto mt-20" /></div>;
  if (error || !data) return <div className="page-wrapper"><div className="alert alert-danger">{error}</div></div>;

  const features = data.features || {};
  const risk = data.risk || {};

  // Chart setup
  const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'top', labels: { font: { family: 'Inter', size: 12 }, usePointStyle: true, boxWidth: 8 } } },
    scales: {
      x: { grid: { display: false }, title: { display: true, text: 'Time (s)', font: { size: 11 } } },
      y: { grid: { color: 'var(--clr-border)' }, title: { display: true, font: { size: 11 } } }
    },
    elements: { point: { radius: 0, hitRadius: 10, hoverRadius: 4 }, line: { tension: 0.3, borderWidth: 2 } },
    interaction: { mode: 'index', intersect: false }
  };

  const timeAxis = ts ? ts.time : [];
  
  const kneeChartData = {
    labels: timeAxis,
    datasets: [
      { label: 'Left Knee', data: ts?.left_knee_angle || [], borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)' },
      { label: 'Right Knee', data: ts?.right_knee_angle || [], borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)' }
    ]
  };

  const comChartData = {
    labels: timeAxis,
    datasets: [
      { label: 'COM Lateral (X)', data: ts?.com_x || [], borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.1)' },
      { label: 'COM Vertical (Y)', data: ts?.com_y || [], borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,0.1)' }
    ]
  };

  const TABS = ['Overview', 'Kinematics', 'Symmetry & Balance', 'Risk Factors'];

  return (
    <div className="page-wrapper animate-in">
      {/* Top Navigation */}
      <div className="mb-6 flex items-center justify-between">
        <button className="btn btn-ghost" style={{ paddingLeft: 0 }} onClick={() => navigate(-1)}>
          <ChevronLeft size={18} /> Back
        </button>
        <button className="btn btn-primary" onClick={handleDownload} disabled={downloading}>
          {downloading ? <div className="spinner" style={{width:16,height:16,borderWidth:2}}/> : <Download size={16} />}
          Download PDF Report
        </button>
      </div>

      {/* Header Profile Card */}
      <div className="card mb-6" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="flex gap-6 items-center">
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--clr-surface-2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <User size={32} color="var(--clr-navy-light)" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.4rem', color: 'var(--clr-navy)', marginBottom: 4 }}>{data.patient_name}</h1>
            <div className="flex gap-4 text-sm text-muted">
              <span className="flex items-center gap-1"><Calendar size={14}/> {new Date(data.date).toLocaleDateString()}</span>
              <span className="flex items-center gap-1"><Activity size={14}/> {data.id}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-xs text-muted font-bold tracking-wider uppercase mb-1">Gait Score</div>
            <div style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', fontWeight: 700, color: 'var(--clr-navy)', lineHeight: 1 }}>
              {data.gait_score || '—'} <span style={{ fontSize: '1rem', color: 'var(--clr-text-muted)', fontWeight: 500 }}>/100</span>
            </div>
          </div>
          <div style={{ width: 1, height: 48, background: 'var(--clr-border)' }} />
          <div>
            <div className="text-xs text-muted font-bold tracking-wider uppercase mb-2">Screening Status</div>
            <RiskPill level={data.risk_level} />
          </div>
        </div>
      </div>

      {/* Warning Banner if HIGH risk */}
      {data.risk_level === 'HIGH' && (
        <div className="alert alert-danger mb-6">
          <AlertCircle size={20} style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong>Clinical Review Recommended:</strong> {risk.clinical_narrative || 'Notable gait irregularities detected. Further assessment is advised.'}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs mb-6">
        {TABS.map(t => (
          <div key={t} className={`tab ${activeTab === t ? 'active' : ''}`} onClick={() => setActiveTab(t)}>
            {t}
          </div>
        ))}
      </div>

      {/* Tab Content */}
      <div className="animate-in">
        
        {/* OVERVIEW TAB */}
        {activeTab === 'Overview' && (
          <div className="grid gap-6" style={{ gridTemplateColumns: '1fr 340px' }}>
            <div className="flex flex-col gap-6">
              
              {/* Key Metrics Grid */}
              <div className="card">
                <div className="card-header"><div className="card-title">Key Spatiotemporal Metrics</div></div>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'Cadence', value: features.cadence, unit: 'steps/min', norm: '100 - 115' },
                    { label: 'Walking Speed', value: features.walking_speed, unit: 'm/s', norm: '1.2 - 1.4' },
                    { label: 'Step Length', value: features.step_length, unit: 'm', norm: '0.6 - 0.8' },
                    { label: 'Stride Length', value: features.stride_length, unit: 'm', norm: '1.2 - 1.6' },
                    { label: 'Step Time', value: features.step_time, unit: 's', norm: '0.4 - 0.6' },
                    { label: 'Overall Symmetry', value: features.symmetry_score, unit: '%', norm: '> 90%' },
                  ].map(m => (
                    <div key={m.label} style={{ padding: '16px', background: 'var(--clr-surface-2)', borderRadius: 10, border: '1px solid var(--clr-border)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>{m.label}</div>
                      <div className="flex items-baseline gap-1">
                        <span style={{ fontFamily: 'Space Grotesk', fontSize: '1.5rem', fontWeight: 700, color: 'var(--clr-navy)' }}>
                          {m.value != null ? Number(m.value).toFixed(2) : '—'}
                        </span>
                        <span style={{ fontSize: '0.8rem', color: 'var(--clr-text-secondary)' }}>{m.unit}</span>
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--clr-text-muted)', marginTop: 4 }}>Ref: {m.norm}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Mini Kinematics Chart */}
              {ts && (
                <div className="card">
                  <div className="card-header"><div className="card-title">Knee Flexion/Extension Overview</div></div>
                  <div style={{ height: 260 }}>
                    <Line data={kneeChartData} options={{...chartOptions, scales: { y: { title: { text: 'Angle (°)' }}}}} />
                  </div>
                </div>
              )}
            </div>

            {/* Right Column */}
            <div className="flex flex-col gap-6">
              <div className="card">
                <div className="card-header"><div className="card-title">Assessment Info</div></div>
                <div className="flex flex-col gap-3 text-sm">
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted">Analyst</span>
                    <span className="font-medium">{data.doctor_name}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted">Condition</span>
                    <span className="font-medium text-right max-w-[150px] truncate" title={data.walking_condition}>{data.walking_condition}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted">Camera</span>
                    <span className="font-medium text-right">{data.camera_view}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted">Duration</span>
                    <span className="font-medium">{data.duration}s ({features.fps} fps)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Video File</span>
                    <span className="font-medium text-right max-w-[150px] truncate" title={data.video_filename}>{data.video_filename}</span>
                  </div>
                </div>
              </div>

              {/* Quick Risk factors */}
              <div className="card bg-slate-50 border-none shadow-none">
                <h4 className="text-sm font-bold text-navy mb-3 uppercase tracking-wider">Detected Risk Factors</h4>
                <div className="flex flex-col gap-3">
                  {(risk.factors || []).filter(f => f.status !== 'normal').map((f, i) => (
                    <div key={i} className="flex gap-3 items-start">
                      <AlertTriangle size={16} color={f.status === 'danger' ? 'var(--clr-danger)' : 'var(--clr-warning)'} style={{ marginTop: 2, flexShrink: 0 }} />
                      <div className="text-sm">
                        <div className="font-semibold">{f.name}</div>
                        <div className="text-xs text-muted">{f.label}</div>
                      </div>
                    </div>
                  ))}
                  {(risk.factors || []).filter(f => f.status !== 'normal').length === 0 && (
                    <div className="text-sm text-muted">No significant risk factors detected outside of normal ranges.</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* KINEMATICS TAB */}
        {activeTab === 'Kinematics' && (
          <div className="flex flex-col gap-6">
            <div className="card">
              <div className="card-header"><div className="card-title">Knee Flexion/Extension Angles</div></div>
              <div className="mb-4 grid grid-cols-4 gap-4">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <div className="text-xs text-blue-600 font-bold">L Knee ROM</div>
                  <div className="text-lg font-bold text-blue-900">{Number(features.left_knee_rom || 0).toFixed(1)}°</div>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <div className="text-xs text-green-600 font-bold">R Knee ROM</div>
                  <div className="text-lg font-bold text-green-900">{Number(features.right_knee_rom || 0).toFixed(1)}°</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500 font-bold">ROM Asymmetry</div>
                  <div className="text-lg font-bold text-navy">{Number(features.knee_rom_asymmetry || 0).toFixed(1)}°</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500 font-bold">Peak Flexion (Max)</div>
                  <div className="text-lg font-bold text-navy">{Math.max(features.left_knee_max||0, features.right_knee_max||0).toFixed(1)}°</div>
                </div>
              </div>
              <div style={{ height: 350 }}>
                {ts ? <Line data={kneeChartData} options={{...chartOptions, scales: { y: { title: { text: 'Angle (°)' }}}}} /> : <div className="flex items-center justify-center h-full text-muted">Timeseries data not available</div>}
              </div>
            </div>
          </div>
        )}

        {/* SYMMETRY & BALANCE TAB */}
        {activeTab === 'Symmetry & Balance' && (
          <div className="grid gap-6" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <div className="card flex flex-col">
              <div className="card-header"><div className="card-title">Center of Mass Trajectory</div></div>
              <p className="text-sm text-muted mb-4">Tracking dynamic stability and postural sway during locomotion.</p>
              <div style={{ height: 300 }}>
                {ts ? <Line data={comChartData} options={{...chartOptions, scales: { y: { title: { text: 'Normalized Displacement' }}}}} /> : <div className="flex items-center justify-center h-full text-muted">Timeseries data not available</div>}
              </div>
              <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-sm font-bold text-navy mb-1">Postural Sway Index</div>
                <div className="text-2xl font-black text-navy">{Number(features.postural_sway || 0).toFixed(4)}</div>
                <div className="text-xs text-muted mt-1">Lower indicates better dynamic stability.</div>
              </div>
            </div>

            <div className="card flex flex-col">
              <div className="card-header"><div className="card-title">Inter-limb Symmetry</div></div>
              
              <div className="flex flex-col gap-4 mt-2">
                <div className="metric-row">
                  <div className="metric-name">Overall Symmetry Score</div>
                  <div className="metric-bar-container"><div className="metric-bar" style={{ width: `${features.symmetry_score || 0}%`, background: features.symmetry_score > 90 ? 'var(--clr-success)' : 'var(--clr-warning)' }} /></div>
                  <div className="metric-value">{Number(features.symmetry_score || 0).toFixed(1)}%</div>
                </div>
                
                <div className="metric-row">
                  <div className="metric-name">Knee ROM Asymmetry</div>
                  <div className="metric-value">{Number(features.knee_rom_asymmetry || 0).toFixed(1)}°</div>
                </div>

                <div className="metric-row">
                  <div className="metric-name">Step Time Asymmetry</div>
                  <div className="metric-value">{Number(features.step_asymmetry || 0).toFixed(2)}s</div>
                </div>
              </div>

              <div className="mt-auto pt-6">
                <div className="alert alert-info">
                  <strong>Clinical Note:</strong> A symmetry score above 90% is generally considered within typical community ambulator ranges. Noticeable discrepancies in joint ROM may warrant targeted unilateral strengthening.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* RISK FACTORS TAB */}
        {activeTab === 'Risk Factors' && (
          <div className="card">
            <div className="card-header"><div className="card-title">Detailed Risk Screening</div></div>
            <p className="text-sm text-navy mb-6 font-medium leading-relaxed max-w-3xl">
              {risk.clinical_narrative}
            </p>
            
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 40 }}></th>
                  <th>Factor</th>
                  <th>Observation</th>
                  <th>Impact Score</th>
                </tr>
              </thead>
              <tbody>
                {(risk.factors || []).map((f, i) => (
                  <tr key={i}>
                    <td>
                      {f.status === 'normal' ? <div style={{width: 12, height: 12, borderRadius: '50%', background: 'var(--clr-success)'}} /> : 
                       f.status === 'warning' ? <div style={{width: 12, height: 12, borderRadius: '50%', background: 'var(--clr-warning)'}} /> :
                       <div style={{width: 12, height: 12, borderRadius: '50%', background: 'var(--clr-danger)'}} />}
                    </td>
                    <td className="font-medium text-navy">{f.name}</td>
                    <td className="text-muted text-sm">{f.label}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div style={{ flex: 1, height: 4, background: 'var(--clr-border)', borderRadius: 2 }}>
                          <div style={{ height: '100%', borderRadius: 2, background: 'var(--clr-navy-light)', width: `${f.score}%` }} />
                        </div>
                        <span className="text-xs font-bold w-6 text-right">{f.score}</span>
                      </div>
                    </td>
                  </tr>
                ))}
                {!(risk.factors?.length) && <tr><td colSpan={4} className="text-center p-8 text-muted">No risk breakdown available.</td></tr>}
              </tbody>
            </table>
          </div>
        )}

      </div>
    </div>
  );
}
