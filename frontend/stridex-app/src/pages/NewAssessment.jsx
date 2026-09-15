import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPatients, createAssessment, uploadVideo, startAnalysis, getAnalysisStatus } from '../api';
import { useAuth } from '../AuthContext';
import { Upload, FileVideo, Activity, CheckCircle, AlertCircle, PlayCircle, Loader2 } from 'lucide-react';

const STEPS = ['Patient Details', 'Video Upload', 'Analysis'];

export default function NewAssessment() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [patients, setPatients] = useState([]);
  
  // State for Step 1
  const [assessment, setAssessment] = useState({
    patient_id: '', patient_name: '',
    date: new Date().toISOString().split('T')[0],
    walking_condition: 'Level Ground — Comfortable Speed',
    camera_view: 'Sagittal Lateral (Right Side)',
    notes: ''
  });
  
  // State for Step 2
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [assessmentId, setAssessmentId] = useState(null);
  
  // State for Step 3
  const [status, setStatus] = useState(null); // polling status

  useEffect(() => {
    getPatients().then(res => setPatients(res.data.patients || []));
  }, []);

  const handleCreateAssessment = async () => {
    if (!assessment.patient_id) return alert('Select a patient');
    setLoading(true);
    try {
      const p = patients.find(x => x.id === assessment.patient_id) || {};
      const payload = {
        ...assessment,
        patient_name: p.name || 'Unknown Patient',
        doctor_id: user?.id,
        doctor_name: user?.name,
      };
      const res = await createAssessment(payload);
      setAssessmentId(res.data.assessment.id);
      setStep(1);
    } catch (e) {
      console.error(e);
      alert('Failed to create assessment');
    } finally {
      setLoading(false);
    }
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer ? e.dataTransfer.files[0] : e.target.files[0];
    if (f && f.type.startsWith('video/')) {
      setFile(f);
    } else {
      alert('Please upload a valid video file (MP4, MOV)');
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (!file) return alert('Select a video first');
    setStep(2);
    try {
      // 1. Upload
      setStatus({ stage: 'Uploading video...', percent: 0, status: 'uploading' });
      await uploadVideo(assessmentId, file, (pct) => {
        setStatus({ stage: `Uploading... ${pct}%`, percent: pct, status: 'uploading' });
      });

      // 2. Start Analysis
      setStatus({ stage: 'Initializing pipeline...', percent: 0, status: 'starting' });
      await startAnalysis(assessmentId);
      
      // 3. Poll Status
      pollStatus();
    } catch (e) {
      console.error(e);
      setStatus({ stage: 'Failed', percent: 0, status: 'failed', error: e.response?.data?.error || 'Analysis failed' });
    }
  };

  const pollStatus = () => {
    const timer = setInterval(async () => {
      try {
        const res = await getAnalysisStatus(assessmentId);
        setStatus(res.data);
        if (res.data.status === 'completed') {
          clearInterval(timer);
          setTimeout(() => navigate(`/app/assess/${assessmentId}/results`), 1000);
        } else if (res.data.status === 'failed') {
          clearInterval(timer);
        }
      } catch (e) {
        console.error('Polling error', e);
      }
    }, 2000);
  };

  return (
    <div className="page-wrapper animate-in" style={{ maxWidth: 800 }}>
      <div className="page-header">
        <h1 className="page-title">New Gait Assessment</h1>
        <p className="page-subtitle">Upload and analyze a walking video to extract clinical-grade biomechanical metrics.</p>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center justify-between mb-8 relative">
        <div style={{ position: 'absolute', top: 16, left: 20, right: 20, height: 2, background: 'var(--clr-border)', zIndex: 0 }} />
        <div style={{ position: 'absolute', top: 16, left: 20, width: `${(step / (STEPS.length - 1)) * 100}%`, height: 2, background: 'var(--clr-primary)', zIndex: 1, transition: 'width 0.4s ease' }} />
        
        {STEPS.map((label, idx) => (
          <div key={label} className="flex flex-col items-center gap-2 relative z-10" style={{ width: 100 }}>
            <div style={{ 
              width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: step > idx ? 'var(--clr-primary)' : step === idx ? 'var(--clr-surface)' : 'var(--clr-surface-2)',
              border: `2px solid ${step >= idx ? 'var(--clr-primary)' : 'var(--clr-border)'}`,
              color: step > idx ? '#fff' : step === idx ? 'var(--clr-primary)' : 'var(--clr-text-disabled)',
              fontWeight: 600, fontSize: '0.875rem', transition: 'all 0.3s ease'
            }}>
              {step > idx ? <CheckCircle size={16} /> : idx + 1}
            </div>
            <div style={{ fontSize: '0.75rem', fontWeight: step >= idx ? 600 : 500, color: step >= idx ? 'var(--clr-navy)' : 'var(--clr-text-disabled)' }}>{label}</div>
          </div>
        ))}
      </div>

      <div className="card" style={{ padding: '32px' }}>
        
        {/* STEP 1: PATIENT & METADATA */}
        {step === 0 && (
          <div className="animate-in">
            <h3 style={{ marginBottom: 24, fontSize: '1.1rem', color: 'var(--clr-navy)' }}>Assessment Details</h3>
            <div className="grid gap-5" style={{ gridTemplateColumns: '1fr 1fr' }}>
              <div className="form-group">
                <label className="form-label">Select Patient</label>
                <select className="form-control" value={assessment.patient_id} onChange={e => setAssessment({...assessment, patient_id: e.target.value})}>
                  <option value="" disabled>-- Select Patient --</option>
                  {patients.map(p => <option key={p.id} value={p.id}>{p.name} ({p.id})</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Assessment Date</label>
                <input type="date" className="form-control" value={assessment.date} onChange={e => setAssessment({...assessment, date: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Walking Condition</label>
                <select className="form-control" value={assessment.walking_condition} onChange={e => setAssessment({...assessment, walking_condition: e.target.value})}>
                  <option>Level Ground — Comfortable Speed</option>
                  <option>Level Ground — Fast Pace</option>
                  <option>Treadmill</option>
                  <option>Uneven Surface</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Camera View</label>
                <select className="form-control" value={assessment.camera_view} onChange={e => setAssessment({...assessment, camera_view: e.target.value})}>
                  <option>Sagittal Lateral (Right Side)</option>
                  <option>Sagittal Lateral (Left Side)</option>
                  <option>Frontal (Anterior)</option>
                  <option>Back (Posterior)</option>
                </select>
              </div>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label className="form-label">Clinical Notes (Optional)</label>
                <textarea className="form-control" rows={3} placeholder="Add any relevant observations..." value={assessment.notes} onChange={e => setAssessment({...assessment, notes: e.target.value})} />
              </div>
            </div>
            <div className="flex justify-end mt-8 pt-6" style={{ borderTop: '1px solid var(--clr-border)' }}>
              <button className="btn btn-primary" onClick={handleCreateAssessment} disabled={loading || !assessment.patient_id}>
                {loading ? 'Creating...' : 'Continue to Upload'}
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: VIDEO UPLOAD */}
        {step === 1 && (
          <div className="animate-in flex flex-col items-center">
            <h3 style={{ marginBottom: 8, fontSize: '1.1rem', color: 'var(--clr-navy)', alignSelf: 'flex-start' }}>Upload Walking Video</h3>
            <p className="text-muted text-sm mb-6" style={{ alignSelf: 'flex-start' }}>
              Ensure the entire body (head to toe) is visible in the frame during the walking cycle.
            </p>
            
            <label 
              className="upload-zone flex flex-col items-center justify-center w-full"
              onDragOver={e => { e.preventDefault(); e.currentTarget.classList.add('drag-over'); }}
              onDragLeave={e => { e.preventDefault(); e.currentTarget.classList.remove('drag-over'); }}
              onDrop={handleFileDrop}
              style={{ minHeight: 280 }}
            >
              <input type="file" accept="video/mp4,video/quicktime" style={{ display: 'none' }} onChange={handleFileDrop} />
              
              {!file ? (
                <>
                  <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--clr-primary-glow)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                    <Upload size={28} color="var(--clr-primary)" />
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--clr-navy)', marginBottom: 8 }}>
                    Click to upload or drag and drop
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--clr-text-muted)' }}>
                    MP4, MOV up to 50MB. (Sample video available for demo)
                  </div>
                </>
              ) : (
                <>
                  <FileVideo size={48} color="var(--clr-primary)" style={{ marginBottom: 16 }} />
                  <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--clr-navy)', marginBottom: 4 }}>
                    {file.name}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--clr-text-muted)' }}>
                    {(file.size / (1024*1024)).toFixed(2)} MB
                  </div>
                  <button type="button" className="btn btn-ghost btn-sm mt-4" onClick={(e) => { e.preventDefault(); setFile(null); }}>
                    Choose different file
                  </button>
                </>
              )}
            </label>
            
            <div className="w-full flex justify-between mt-8 pt-6" style={{ borderTop: '1px solid var(--clr-border)' }}>
              <button className="btn btn-secondary" onClick={() => setStep(0)}>Back</button>
              <button className="btn btn-primary" onClick={handleUploadAndAnalyze} disabled={!file}>
                Run Gait Analysis <PlayCircle size={16} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: ANALYSIS PROCESSING */}
        {step === 2 && (
          <div className="animate-in flex flex-col items-center py-8">
            {status?.status === 'failed' ? (
              <>
                <AlertCircle size={56} color="var(--clr-danger)" style={{ marginBottom: 20 }} />
                <h2 style={{ color: 'var(--clr-danger)', marginBottom: 12 }}>Analysis Failed</h2>
                <div style={{ background: 'var(--clr-danger-bg)', padding: '16px', borderRadius: 8, color: 'var(--clr-danger)', fontSize: '0.875rem', maxWidth: '100%', marginBottom: 24, textAlign: 'left' }}>
                  <strong>Error Details:</strong><br/>
                  {status.error || 'An unexpected error occurred during processing.'}
                </div>
                <button className="btn btn-primary" onClick={() => setStep(1)}>Try Another Video</button>
              </>
            ) : status?.status === 'completed' ? (
              <>
                <CheckCircle size={64} color="var(--clr-success)" style={{ marginBottom: 24 }} />
                <h2 style={{ color: 'var(--clr-navy)', marginBottom: 8 }}>Analysis Complete!</h2>
                <p className="text-muted mb-6">Redirecting to results dashboard...</p>
                <div className="spinner" />
              </>
            ) : (
              <>
                <div style={{ position: 'relative', width: 120, height: 120, marginBottom: 32 }}>
                  <svg width="120" height="120" viewBox="0 0 120 120" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="60" cy="60" r="54" fill="none" stroke="var(--clr-border)" strokeWidth="6" />
                    <circle cx="60" cy="60" r="54" fill="none" stroke="var(--clr-primary)" strokeWidth="6" 
                      strokeDasharray={54 * 2 * Math.PI} 
                      strokeDashoffset={54 * 2 * Math.PI * (1 - (status?.percent || 0)/100)} 
                      style={{ transition: 'stroke-dashoffset 0.5s ease' }}
                    />
                  </svg>
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--clr-navy)', fontFamily: 'Space Grotesk' }}>
                      {status?.percent || 0}%
                    </span>
                  </div>
                </div>
                
                <h3 style={{ color: 'var(--clr-navy)', marginBottom: 8, fontSize: '1.1rem' }}>
                  {status?.stage || 'Initializing...'}
                </h3>
                <p className="text-muted text-sm max-w-md text-center" style={{ marginBottom: 32 }}>
                  Running full clinical pipeline: Pose estimation, kinematic extraction, event detection, and risk scoring.
                </p>

                {/* Pipeline visualizer */}
                <div className="w-full flex flex-col gap-2 max-w-md mx-auto">
                  {['uploading', 'Video Decoding', 'Pose Tracking (MediaPipe)', 'Biomechanical Extraction', 'Risk Assessment'].map((s, i) => {
                    // Simple logic to light up steps based on percent
                    const stepPct = i * 20;
                    const isDone = (status?.percent || 0) > stepPct;
                    const isActive = !isDone && (status?.percent || 0) > (stepPct - 20);
                    return (
                      <div key={s} className="flex items-center gap-3" style={{ padding: '8px 12px', background: isActive ? 'var(--clr-info-bg)' : 'transparent', borderRadius: 8 }}>
                        {isDone ? <CheckCircle size={18} color="var(--clr-success)" /> : isActive ? <Loader2 size={18} color="var(--clr-primary)" className="animate-spin" /> : <div style={{width: 18, height: 18, borderRadius: '50%', border: '2px solid var(--clr-border)'}} />}
                        <span style={{ fontSize: '0.85rem', color: isActive || isDone ? 'var(--clr-navy)' : 'var(--clr-text-disabled)', fontWeight: isActive ? 600 : 400 }}>{s === 'uploading' ? 'Upload Video' : s}</span>
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
