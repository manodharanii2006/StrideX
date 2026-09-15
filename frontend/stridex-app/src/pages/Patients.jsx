import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPatients, createPatient } from '../api';
import { Search, Plus, User, Calendar, Activity, ChevronRight, X } from 'lucide-react';

export default function Patients() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [newPatient, setNewPatient] = useState({ name: '', email: '', dob: '', gender: 'Female', condition: '' });

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const res = await getPatients();
      setPatients(res.data.patients || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAddPatient = async (e) => {
    e.preventDefault();
    try {
      await createPatient(newPatient);
      setShowAdd(false);
      setNewPatient({ name: '', email: '', dob: '', gender: 'Female', condition: '' });
      fetchPatients();
    } catch (e) {
      console.error(e);
    }
  };

  const filtered = patients.filter(p => 
    p.name?.toLowerCase().includes(search.toLowerCase()) || 
    p.id?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page-wrapper animate-in">
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">Patient Registry</h1>
          <p className="page-subtitle">Manage clinical profiles and view assessment histories.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
          <Plus size={16} /> Register Patient
        </button>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <div className="card-header" style={{ padding: '20px 24px' }}>
          <div style={{ position: 'relative', width: '300px' }}>
            <Search size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--clr-text-muted)' }} />
            <input 
              type="text" 
              className="form-control" 
              placeholder="Search by name or ID..." 
              style={{ paddingLeft: 38 }}
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Patient ID</th>
                <th>Last Assessment</th>
                <th>Gait Score</th>
                <th>Risk</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ padding: 24 }}>
                  {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 40, marginBottom: 12 }} />)}
                </td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: 'var(--clr-text-muted)' }}>
                  No patients found.
                </td></tr>
              ) : (
                filtered.map(p => {
                  const riskColor = p.latest_risk_level === 'HIGH' ? '#dc2626' : p.latest_risk_level === 'MODERATE' ? '#d97706' : '#16a34a';
                  const riskBg    = p.latest_risk_level === 'HIGH' ? '#fef2f2' : p.latest_risk_level === 'MODERATE' ? '#fffbeb' : '#f0fdf4';
                  return (
                    <tr key={p.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/app/patients/${p.id}`)}>
                      <td>
                        <div className="flex items-center gap-3">
                          <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--clr-surface-2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--clr-navy-light)' }}>
                            <User size={18} />
                          </div>
                          <div>
                            <div style={{ fontWeight: 600, color: 'var(--clr-navy)' }}>{p.name}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>{p.age ? `${p.age} yrs` : '—'} · {p.gender || '—'}</div>
                          </div>
                        </div>
                      </td>
                      <td style={{ fontFamily: 'Space Grotesk', fontSize: '0.8125rem', color: 'var(--clr-text-muted)' }}>{p.id}</td>
                      <td style={{ fontSize: '0.8125rem' }}>{p.last_assessment_date ? new Date(p.last_assessment_date).toLocaleDateString('en-GB', { day:'numeric', month:'short', year:'numeric' }) : '—'}</td>
                      <td><span style={{ fontFamily:'Space Grotesk', fontWeight:700, color:'var(--clr-navy)' }}>{p.latest_gait_score ?? '—'}</span></td>
                      <td>{p.latest_risk_level ? <span style={{ padding:'2px 10px', borderRadius:20, background:riskBg, color:riskColor, fontWeight:700, fontSize:'0.75rem' }}>{p.latest_risk_level}</span> : '—'}</td>
                      <td>
                        <button className="btn btn-ghost btn-sm"><ChevronRight size={16} /></button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Patient Modal */}
      {showAdd && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Register New Patient</h3>
              <button className="btn btn-icon btn-ghost" onClick={() => setShowAdd(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleAddPatient}>
              <div className="modal-body flex flex-col gap-4">
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input required className="form-control" value={newPatient.name} onChange={e => setNewPatient({...newPatient, name: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Email Address (Optional)</label>
                  <input type="email" className="form-control" value={newPatient.email} onChange={e => setNewPatient({...newPatient, email: e.target.value})} />
                </div>
                <div className="grid gap-4" style={{ gridTemplateColumns: '1fr 1fr' }}>
                  <div className="form-group">
                    <label className="form-label">Date of Birth</label>
                    <input type="date" className="form-control" value={newPatient.dob} onChange={e => {
                      const dob = e.target.value;
                      let age = '';
                      if (dob) {
                        const diff = Date.now() - new Date(dob).getTime();
                        age = Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
                      }
                      setNewPatient({...newPatient, dob, age});
                    }} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Gender</label>
                    <select className="form-control" value={newPatient.gender} onChange={e => setNewPatient({...newPatient, gender: e.target.value})}>
                      <option>Female</option>
                      <option>Male</option>
                      <option>Other</option>
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Primary Condition / Diagnosis</label>
                  <input className="form-control" placeholder="e.g. Post-op knee arthroscopy" value={newPatient.condition} onChange={e => setNewPatient({...newPatient, condition: e.target.value})} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Register Patient</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
