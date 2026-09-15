import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { getDashboardStats } from '../api';
import { Users, ClipboardList, AlertTriangle, TrendingUp, Plus, ArrowRight, Activity } from 'lucide-react';

function RiskDot({ level }) {
  const c = level === 'HIGH' ? 'var(--clr-danger)' : level === 'MODERATE' ? 'var(--clr-warning)' : 'var(--clr-success)';
  return <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: c, flexShrink: 0 }} />;
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats().then(r => { setStats(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const today = new Date().toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

  return (
    <div className="page-wrapper animate-in">
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.8125rem', marginBottom: 4 }}>{today}</p>
          <h1 className="page-title" style={{ fontSize: '1.65rem' }}>Good morning, {user?.name?.split(' ')[0]} 👋</h1>
          <p className="page-subtitle">{user?.specialty || 'Clinical Workstation'} · {user?.institution || 'StrideX Platform'}</p>
        </div>
        <button id="new-assessment-btn" className="btn btn-primary" onClick={() => navigate('/app/assess/new')}>
          <Plus size={16} /> New Assessment
        </button>
      </div>

      {/* Stat Cards */}
      {loading ? (
        <div className="stat-grid" style={{ marginBottom: 32 }}>
          {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 110 }} />)}
        </div>
      ) : (
        <div className="stat-grid" style={{ marginBottom: 32 }}>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#eff6ff' }}>
              <Users size={22} color="var(--clr-primary)" />
            </div>
            <div>
              <div className="stat-label">Total Patients</div>
              <div className="stat-value">{stats?.total_patients ?? '—'}</div>
              <div className="stat-delta">Active in registry</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#f0fdf9' }}>
              <ClipboardList size={22} color="var(--clr-success)" />
            </div>
            <div>
              <div className="stat-label">Assessments This Month</div>
              <div className="stat-value">{stats?.assessments_this_month ?? '—'}</div>
              <div className="stat-delta up">↑ Active month</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#fef3c7' }}>
              <AlertTriangle size={22} color="var(--clr-warning)" />
            </div>
            <div>
              <div className="stat-label">Require Review</div>
              <div className="stat-value">{stats?.patients_requiring_review ?? '—'}</div>
              <div className="stat-delta" style={{ color: 'var(--clr-warning)' }}>Moderate or High risk</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#fdf4ff' }}>
              <TrendingUp size={22} color="#9333ea" />
            </div>
            <div>
              <div className="stat-label">Total Assessments</div>
              <div className="stat-value">{stats?.total_assessments ?? '—'}</div>
              <div className="stat-delta">All time</div>
            </div>
          </div>
        </div>
      )}

      {/* Two-column: Recent Assessments + Quick Actions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24 }}>

        {/* Recent Assessments */}
        <div className="card" style={{ padding: 0 }}>
          <div className="card-header" style={{ padding: '20px 24px' }}>
            <div>
              <div className="card-title">Recent Assessments</div>
              <div className="card-subtitle">Latest gait analysis results</div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/app/assessments')}>
              View all <ArrowRight size={14} />
            </button>
          </div>
          <div style={{ overflowX: 'auto' }}>
            {loading ? (
              <div style={{ padding: 24 }}>
                {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 52, marginBottom: 8 }} />)}
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Patient</th><th>Date</th><th>Gait Score</th><th>Risk Level</th><th>Status</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  {(stats?.recent_assessments || []).map(a => (
                    <tr key={a.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/app/assess/${a.id}/results`)}>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--clr-navy)', fontSize: '0.875rem' }}>{a.patient_name}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--clr-text-muted)' }}>{a.patient_id}</div>
                      </td>
                      <td style={{ color: 'var(--clr-text-secondary)', fontSize: '0.8125rem' }}>
                        {new Date(a.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </td>
                      <td>
                        {a.gait_score != null ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontFamily: 'Space Grotesk', fontWeight: 700, fontSize: '1.05rem', color: 'var(--clr-navy)' }}>
                              {a.gait_score}
                            </span>
                            <span style={{ fontSize: '0.7rem', color: 'var(--clr-text-muted)' }}>/100</span>
                          </div>
                        ) : <span style={{ color: 'var(--clr-text-muted)' }}>—</span>}
                      </td>
                      <td>
                        {a.risk_level ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <RiskDot level={a.risk_level} />
                            <span className={`risk-pill risk-${a.risk_level}`}>{a.risk_level}</span>
                          </div>
                        ) : <span style={{ color: 'var(--clr-text-muted)' }}>—</span>}
                      </td>
                      <td>
                        <span className={`badge ${a.status === 'completed' ? 'badge-success' : a.status === 'failed' ? 'badge-danger' : 'badge-info'}`}>
                          {a.status}
                        </span>
                      </td>
                      <td>
                        <button className="btn btn-ghost btn-sm" style={{ padding: '6px 10px' }}>
                          <ArrowRight size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {!loading && !(stats?.recent_assessments?.length) && (
                    <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--clr-text-muted)', padding: '40px' }}>
                      No assessments yet. Start a new gait analysis.
                    </td></tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <div className="card-header" style={{ paddingBottom: 12, marginBottom: 12 }}>
              <div className="card-title">Quick Actions</div>
            </div>
            {[
              { label: 'New Gait Assessment', desc: 'Upload and analyse a walking video', icon: Activity, color: '#eff6ff', iconColor: 'var(--clr-primary)', path: '/app/assess/new', id: 'qa-new-assess' },
              { label: 'Register Patient', desc: 'Add new patient to registry', icon: Users, color: '#f0fdf9', iconColor: 'var(--clr-success)', path: '/app/patients', id: 'qa-add-patient' },
              { label: 'View All Patients', desc: 'Browse patient registry', icon: ClipboardList, color: '#fdf4ff', iconColor: '#9333ea', path: '/app/patients', id: 'qa-all-patients' },
            ].map(action => {
              const Icon = action.icon;
              return (
                <div key={action.label} id={action.id} style={{
                  display: 'flex', alignItems: 'center', gap: 14, padding: '12px 4px',
                  cursor: 'pointer', borderRadius: 8, transition: 'background 0.15s'
                }}
                  onClick={() => navigate(action.path)}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--clr-surface-2)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ width: 40, height: 40, borderRadius: 10, background: action.color, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Icon size={18} color={action.iconColor} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--clr-navy)' }}>{action.label}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>{action.desc}</div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="card" style={{ background: 'linear-gradient(135deg, #0f2342 0%, #1a3a6b 100%)', border: 'none' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: 'rgba(59,130,246,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Activity size={16} color="#93c5fd" />
              </div>
              <span style={{ fontFamily: 'Space Grotesk', fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>Analysis Engine</span>
            </div>
            <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.78rem', lineHeight: 1.6, marginBottom: 16 }}>
              StrideX uses MediaPipe Pose Landmarker + physics-based biomechanical extraction to deliver clinical-grade gait metrics in real-time.
            </p>
            <button id="run-analysis-btn" className="btn btn-sm" onClick={() => navigate('/app/assess/new')} style={{
              background: 'rgba(26,86,219,0.7)', color: '#fff', border: '1px solid rgba(59,130,246,0.3)', fontSize: '0.75rem'
            }}>
              Run New Analysis →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
