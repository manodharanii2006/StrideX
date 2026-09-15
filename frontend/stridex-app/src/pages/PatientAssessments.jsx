import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPatientAssessments, downloadPdf } from '../api';
import { FileText, Download, ChevronRight, Activity } from 'lucide-react';

function RiskBadge({ level }) {
  const c = level==='HIGH' ? '#dc2626' : level==='MODERATE' ? '#d97706' : '#16a34a';
  const bg = level==='HIGH' ? '#fef2f2' : level==='MODERATE' ? '#fffbeb' : '#f0fdf4';
  return <span style={{ padding:'2px 10px',borderRadius:20,background:bg,color:c,fontWeight:700,fontSize:'0.75rem' }}>{level||'—'}</span>;
}

export default function PatientAssessments() {
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    getPatientAssessments()
      .then(r => setAssessments(r.data.assessments || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = async (id, e) => {
    e.stopPropagation();
    setDownloading(id);
    try {
      const res = await downloadPdf(id);
      const url = URL.createObjectURL(new Blob([res.data]));
      Object.assign(document.createElement('a'), { href:url, download:`StrideX_Report_${id}.pdf` }).click();
    } catch { alert('PDF generation failed'); }
    finally { setDownloading(null); }
  };

  return (
    <div className="page-wrapper animate-in">
      <div className="page-header">
        <h1 className="page-title">My Assessments</h1>
        <p className="page-subtitle">All your completed and pending gait assessments.</p>
      </div>

      {loading ? (
        <div className="spinner" style={{ margin:'60px auto' }} />
      ) : assessments.length === 0 ? (
        <div className="card" style={{ textAlign:'center', padding:'60px 24px' }}>
          <Activity size={48} style={{ color:'var(--clr-border)', margin:'0 auto 16px' }} />
          <h3 style={{ color:'var(--clr-navy)', marginBottom:8 }}>No assessments yet</h3>
          <p style={{ color:'var(--clr-text-muted)', marginBottom:20 }}>Upload your first walking video to establish your personal gait baseline.</p>
          <button className="btn btn-primary" onClick={() => navigate('/app/patient/assessment/new')}>Start First Assessment</button>
        </div>
      ) : (
        <div className="card" style={{ padding:0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Assessment ID</th>
                <th>Date</th>
                <th>Gait Score</th>
                <th>Risk Level</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {assessments.map(a => (
                <tr key={a.id} style={{ cursor:'pointer' }} onClick={() => a.status==='completed' && navigate(`/app/assess/${a.id}/results`)}>
                  <td style={{ fontFamily:'Space Grotesk', fontSize:'0.8rem', color:'var(--clr-text-muted)' }}>{a.id}</td>
                  <td>{a.date ? new Date(a.date).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}) : '—'}</td>
                  <td>
                    {a.gait_score != null
                      ? <span style={{ fontFamily:'Space Grotesk', fontWeight:700, color:'var(--clr-navy)' }}>{a.gait_score}<span style={{ fontSize:'0.75rem', color:'var(--clr-text-muted)' }}>/100</span></span>
                      : '—'}
                  </td>
                  <td>{a.risk_level ? <RiskBadge level={a.risk_level} /> : '—'}</td>
                  <td>
                    <span style={{
                      padding:'2px 10px', borderRadius:20, fontSize:'0.75rem', fontWeight:600,
                      background: a.status==='completed'?'#f0fdf4':a.status==='processing'?'#eff6ff':'#f1f5f9',
                      color:      a.status==='completed'?'#16a34a':a.status==='processing'?'#1a56db':'#64748b',
                    }}>{a.status}</span>
                  </td>
                  <td>
                    <div style={{ display:'flex', gap:8 }}>
                      {a.status === 'completed' && (
                        <>
                          <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/app/assess/${a.id}/results`)}>
                            <ChevronRight size={14} /> View
                          </button>
                          <button className="btn btn-ghost btn-sm" onClick={e => handleDownload(a.id, e)} disabled={downloading===a.id}>
                            <Download size={14} /> PDF
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
