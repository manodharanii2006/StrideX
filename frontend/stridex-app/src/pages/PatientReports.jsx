import React, { useEffect, useState } from 'react';
import { getPatientAssessments, downloadPdf } from '../api';
import { Download, FileText } from 'lucide-react';

export default function PatientReports() {
  const [assessments, setAssessments] = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    getPatientAssessments()
      .then(r => setAssessments((r.data.assessments || []).filter(a => a.status === 'completed')))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = async (id) => {
    setDownloading(id);
    try {
      const res = await downloadPdf(id);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url; a.download = `StrideX_Report_${id}.pdf`; a.click();
    } catch { alert('Download failed'); }
    finally { setDownloading(null); }
  };

  if (loading) return <div className="page-wrapper"><div className="spinner" style={{ margin:'60px auto' }} /></div>;

  return (
    <div className="page-wrapper animate-in">
      <div className="page-header">
        <h1 className="page-title">Reports</h1>
        <p className="page-subtitle">Download clinical PDF reports for your completed assessments</p>
      </div>
      {assessments.length === 0 ? (
        <div className="card" style={{ textAlign:'center', padding:'60px' }}>
          <FileText size={48} style={{ color:'var(--clr-border)', margin:'0 auto 16px' }} />
          <h3 style={{ color:'var(--clr-navy)', marginBottom:8 }}>No reports available</h3>
          <p style={{ color:'var(--clr-text-muted)' }}>Complete a gait assessment to generate your first report.</p>
        </div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          {assessments.map(a => (
            <div className="card" key={a.id} style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <div>
                <div style={{ fontWeight:700, color:'var(--clr-navy)', marginBottom:4 }}>
                  Gait Assessment Report — {a.date ? new Date(a.date).toLocaleDateString('en-GB', { day:'numeric', month:'long', year:'numeric' }) : a.id}
                </div>
                <div style={{ fontSize:'0.8rem', color:'var(--clr-text-muted)', display:'flex', gap:16 }}>
                  <span>ID: {a.id}</span>
                  <span>Score: <strong>{a.gait_score ?? '—'}</strong>/100</span>
                  <span>Risk: <strong>{a.risk_level || '—'}</strong></span>
                </div>
              </div>
              <button className="btn btn-primary btn-sm" onClick={() => handleDownload(a.id)} disabled={downloading === a.id}>
                <Download size={14} /> {downloading === a.id ? 'Generating…' : 'Download PDF'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
