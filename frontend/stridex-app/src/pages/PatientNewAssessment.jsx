import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { createAssessment, uploadVideo, startAnalysis, getAnalysisStatus } from '../api';
import { Upload, FileVideo, CheckCircle, AlertCircle, Loader2, Info } from 'lucide-react';

const STEPS = ['Assessment Setup', 'Upload Video', 'Processing'];

const PIPELINE_STAGES = [
  'Uploading video',
  'Extracting pose landmarks',
  'Computing joint angles',
  'Calculating biomechanics',
  'Comparing to your baseline',
  'Risk screening',
  'Finalising report',
];

export default function PatientNewAssessment() {
  const { user } = useAuth();
  const navigate  = useNavigate();
  const [step,       setStep]      = useState(0);
  const [loading,    setLoading]   = useState(false);
  const [file,       setFile]      = useState(null);
  const [asmId,      setAsmId]     = useState(null);
  const [status,     setStatus]    = useState(null);
  const [dragOver,   setDragOver]  = useState(false);

  const [meta, setMeta] = useState({
    walking_condition: 'Level Ground — Comfortable Speed',
    camera_view: 'Sagittal Lateral (Right Side)',
    notes: '',
  });

  const pollRef = useRef(null);

  // ── Step 1 → create assessment record ───────────────────────────────────
  const handleCreateAssessment = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await createAssessment({
        patient_id:   user.id,
        patient_name: user.name,
        doctor_id:    null,
        doctor_name:  null,
        date:         new Date().toISOString().split('T')[0],
        ...meta,
      });
      setAsmId(res.data.assessment.id);
      setStep(1);
    } catch (err) {
      alert('Failed to create assessment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // ── Step 2 → upload + start pipeline ────────────────────────────────────
  const handleRunAnalysis = async () => {
    if (!file) return;
    setStep(2);
    setStatus({ stage:'Uploading video…', percent:0, status:'running' });
    try {
      await uploadVideo(asmId, file, (pct) => {
        setStatus({ stage:`Uploading… ${pct}%`, percent: pct * 0.3, status:'running' });
      });
      setStatus({ stage:'Starting pipeline…', percent:30, status:'running' });
      await startAnalysis(asmId);
      pollRef.current = setInterval(async () => {
        try {
          const res = await getAnalysisStatus(asmId);
          setStatus(res.data);
          if (res.data.status === 'completed') {
            clearInterval(pollRef.current);
            setTimeout(() => navigate(`/app/assess/${asmId}/results`), 1000);
          } else if (res.data.status === 'failed') {
            clearInterval(pollRef.current);
          }
        } catch (_) {}
      }, 2000);
    } catch (err) {
      setStatus({ stage:'Upload failed', percent:0, status:'failed', error: err.message });
    }
  };

  useEffect(() => () => clearInterval(pollRef.current), []);

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f && f.type.startsWith('video/')) setFile(f);
    else alert('Please select a valid video file (MP4, MOV, AVI).');
  };

  const pipelinePercent = status?.percent || 0;

  return (
    <div className="page-wrapper animate-in" style={{ maxWidth:780 }}>
      <div className="page-header">
        <h1 className="page-title">New Gait Assessment</h1>
        <p className="page-subtitle">Upload a walking video. The StrideX AI engine will extract your biomechanical data automatically.</p>
      </div>

      {/* Step indicator */}
      <div style={{ display:'flex', alignItems:'center', marginBottom:36, position:'relative' }}>
        <div style={{ position:'absolute', top:16, left:24, right:24, height:2, background:'var(--clr-border)', zIndex:0 }} />
        <div style={{ position:'absolute', top:16, left:24, height:2, width:`${(step/(STEPS.length-1))*100}%`, background:'var(--clr-primary)', zIndex:1, transition:'width 0.4s ease', maxWidth:'calc(100% - 48px)' }} />
        {STEPS.map((label, idx) => (
          <div key={label} style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', position:'relative', zIndex:2 }}>
            <div style={{
              width:32, height:32, borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center',
              background: step > idx ? 'var(--clr-primary)' : step===idx ? '#fff' : 'var(--clr-surface-2)',
              border:`2px solid ${step >= idx ? 'var(--clr-primary)' : 'var(--clr-border)'}`,
              color: step > idx ? '#fff' : step===idx ? 'var(--clr-primary)' : 'var(--clr-text-disabled)',
              fontWeight:700, fontSize:'0.875rem', transition:'all 0.3s ease',
            }}>
              {step > idx ? <CheckCircle size={16} /> : idx + 1}
            </div>
            <div style={{ fontSize:'0.75rem', marginTop:6, fontWeight: step>=idx?600:400, color: step>=idx?'var(--clr-navy)':'var(--clr-text-disabled)' }}>
              {label}
            </div>
          </div>
        ))}
      </div>

      <div className="card" style={{ padding:32 }}>

        {/* ── STEP 0: Setup ─────────────────────────────────────────────── */}
        {step === 0 && (
          <form onSubmit={handleCreateAssessment} style={{ display:'flex', flexDirection:'column', gap:20 }}>
            <h3 style={{ color:'var(--clr-navy)', marginBottom:4 }}>Recording Setup</h3>
            <div className="alert alert-info" style={{ fontSize:'0.875rem', gap:10 }}>
              <Info size={18} style={{ flexShrink:0 }} />
              <div>
                <strong>Recommended recording setup:</strong>
                <ul style={{ margin:'6px 0 0', paddingLeft:18, lineHeight:1.8 }}>
                  <li>Camera at hip height, stable on a tripod or surface</li>
                  <li>Side view (sagittal) preferred for best analysis</li>
                  <li>Entire body visible — head to toe — throughout the walk</li>
                  <li>Good lighting, no excessive shadows</li>
                  <li>Walk naturally for at least one full stride cycle</li>
                </ul>
              </div>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
              <div className="form-group">
                <label className="form-label">Walking Condition</label>
                <select className="form-control" value={meta.walking_condition} onChange={e => setMeta(m => ({ ...m, walking_condition:e.target.value }))}>
                  <option>Level Ground — Comfortable Speed</option>
                  <option>Level Ground — Fast Pace</option>
                  <option>Treadmill</option>
                  <option>Uneven Surface</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Camera View</label>
                <select className="form-control" value={meta.camera_view} onChange={e => setMeta(m => ({ ...m, camera_view:e.target.value }))}>
                  <option>Sagittal Lateral (Right Side)</option>
                  <option>Sagittal Lateral (Left Side)</option>
                  <option>Frontal (Anterior)</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Clinical Notes (Optional)</label>
              <textarea className="form-control" rows={2} placeholder="Any symptoms, recent changes, or context…"
                value={meta.notes} onChange={e => setMeta(m => ({ ...m, notes:e.target.value }))} />
            </div>
            <div style={{ display:'flex', justifyContent:'flex-end', borderTop:'1px solid var(--clr-border)', paddingTop:20, marginTop:8 }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Creating…' : 'Continue to Upload →'}
              </button>
            </div>
          </form>
        )}

        {/* ── STEP 1: Upload ────────────────────────────────────────────── */}
        {step === 1 && (
          <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:20 }}>
            <h3 style={{ color:'var(--clr-navy)', alignSelf:'flex-start' }}>Upload Walking Video</h3>

            <label
              style={{
                width:'100%', minHeight:280, border:`2px dashed ${dragOver ? 'var(--clr-primary)' : 'var(--clr-border)'}`,
                borderRadius:12, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
                cursor:'pointer', background: dragOver ? '#eff6ff' : 'var(--clr-surface-2)', transition:'all 0.2s',
                padding:24,
              }}
              onDragOver={e => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
            >
              <input type="file" accept="video/*" style={{ display:'none' }} onChange={e => setFile(e.target.files[0])} />
              {!file ? (
                <>
                  <div style={{ width:72, height:72, borderRadius:'50%', background:'#eff6ff', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:16 }}>
                    <Upload size={32} color="var(--clr-primary)" />
                  </div>
                  <div style={{ fontWeight:600, color:'var(--clr-navy)', marginBottom:6 }}>Click to upload or drag and drop</div>
                  <div style={{ fontSize:'0.8125rem', color:'var(--clr-text-muted)' }}>MP4, MOV, AVI, MKV — up to 100 MB</div>
                </>
              ) : (
                <>
                  <FileVideo size={52} color="var(--clr-primary)" style={{ marginBottom:16 }} />
                  <div style={{ fontWeight:700, color:'var(--clr-navy)', marginBottom:4 }}>{file.name}</div>
                  <div style={{ fontSize:'0.8125rem', color:'var(--clr-text-muted)' }}>{(file.size/1024/1024).toFixed(2)} MB</div>
                  <button type="button" className="btn btn-ghost btn-sm" style={{ marginTop:12 }}
                    onClick={e => { e.preventDefault(); setFile(null); }}>
                    Choose different file
                  </button>
                </>
              )}
            </label>

            <div style={{ width:'100%', display:'flex', justifyContent:'space-between', borderTop:'1px solid var(--clr-border)', paddingTop:20 }}>
              <button className="btn btn-secondary" onClick={() => setStep(0)}>← Back</button>
              <button className="btn btn-primary" onClick={handleRunAnalysis} disabled={!file}>
                Run Gait Analysis →
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 2: Processing ────────────────────────────────────────── */}
        {step === 2 && (
          <div style={{ display:'flex', flexDirection:'column', alignItems:'center', textAlign:'center', padding:'16px 0 8px' }}>
            {status?.status === 'failed' ? (
              <>
                <AlertCircle size={56} color="var(--clr-danger)" style={{ marginBottom:16 }} />
                <h3 style={{ color:'var(--clr-danger)', marginBottom:8 }}>Analysis Failed</h3>
                <div className="alert alert-danger" style={{ maxWidth:480, textAlign:'left' }}>
                  {status.stage || 'An unexpected error occurred.'}
                </div>
                <button className="btn btn-primary" style={{ marginTop:16 }} onClick={() => { setStep(1); setStatus(null); }}>
                  Try again with a different video
                </button>
              </>
            ) : status?.status === 'completed' ? (
              <>
                <CheckCircle size={64} color="var(--clr-success)" style={{ marginBottom:16 }} />
                <h3 style={{ color:'var(--clr-navy)', marginBottom:8 }}>Analysis Complete!</h3>
                <p style={{ color:'var(--clr-text-muted)' }}>Redirecting to your results…</p>
              </>
            ) : (
              <>
                {/* Circular progress */}
                <div style={{ position:'relative', width:128, height:128, marginBottom:28 }}>
                  <svg width="128" height="128" style={{ transform:'rotate(-90deg)' }}>
                    <circle cx="64" cy="64" r="56" fill="none" stroke="var(--clr-border)" strokeWidth="7" />
                    <circle cx="64" cy="64" r="56" fill="none" stroke="var(--clr-primary)" strokeWidth="7"
                      strokeDasharray={56*2*Math.PI}
                      strokeDashoffset={56*2*Math.PI*(1-pipelinePercent/100)}
                      style={{ transition:'stroke-dashoffset 0.5s ease' }} />
                  </svg>
                  <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center' }}>
                    <span style={{ fontFamily:'Space Grotesk', fontSize:'1.5rem', fontWeight:700, color:'var(--clr-navy)' }}>
                      {Math.round(pipelinePercent)}%
                    </span>
                  </div>
                </div>

                <h3 style={{ color:'var(--clr-navy)', marginBottom:8 }}>{status?.stage || 'Starting…'}</h3>
                <p style={{ color:'var(--clr-text-muted)', fontSize:'0.875rem', maxWidth:400, marginBottom:28 }}>
                  The StrideX physics engine is processing your video. This may take 1–3 minutes depending on the video length.
                </p>

                {/* Pipeline step list */}
                <div style={{ width:'100%', maxWidth:400, textAlign:'left' }}>
                  {PIPELINE_STAGES.map((s, i) => {
                    const pctThreshold = (i / (PIPELINE_STAGES.length - 1)) * 100;
                    const done   = pipelinePercent > pctThreshold + 5;
                    const active = !done && pipelinePercent >= pctThreshold;
                    return (
                      <div key={s} style={{ display:'flex', alignItems:'center', gap:12, padding:'6px 0' }}>
                        {done
                          ? <CheckCircle size={16} color="var(--clr-success)" />
                          : active
                            ? <Loader2 size={16} color="var(--clr-primary)" style={{ animation:'spin 1s linear infinite' }} />
                            : <div style={{ width:16, height:16, borderRadius:'50%', border:'2px solid var(--clr-border)' }} />}
                        <span style={{ fontSize:'0.875rem', color: active||done ? 'var(--clr-navy)' : 'var(--clr-text-disabled)', fontWeight: active?600:400 }}>{s}</span>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
