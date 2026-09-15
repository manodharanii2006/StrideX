import React, { useEffect, useState } from 'react';
import { useAuth } from '../AuthContext';
import { getPatientProfile } from '../api';
import { User, Mail, Calendar, Activity as ActivityIcon } from 'lucide-react';

export default function PatientProfile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPatientProfile()
      .then(r => setProfile(r.data.profile))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-wrapper"><div className="spinner" style={{ margin:'60px auto' }} /></div>;

  const p = profile || {};

  return (
    <div className="page-wrapper animate-in" style={{ maxWidth:700 }}>
      <div className="page-header">
        <h1 className="page-title">My Profile</h1>
        <p className="page-subtitle">Your personal information and gait monitoring preferences</p>
      </div>

      <div className="card" style={{ marginBottom:20 }}>
        <div className="card-header"><div className="card-title">Personal Information</div></div>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
          {[
            { icon:User,         label:'Full Name',   value:p.name || user?.name },
            { icon:Mail,         label:'Email',        value:p.email || user?.email },
            { icon:Calendar,     label:'Date of Birth',value:p.dob || '—' },
            { icon:User,         label:'Gender',       value:p.gender || '—' },
            { icon:ActivityIcon, label:'Age',           value:p.age != null ? `${p.age} years` : '—' },
            { icon:User,         label:'Patient ID',   value:user?.id || p.id },
          ].map(f => (
            <div key={f.label} style={{ display:'flex', gap:12, alignItems:'center' }}>
              <div style={{ width:36, height:36, borderRadius:8, background:'#eff6ff', display:'flex', alignItems:'center', justifyContent:'center' }}>
                <f.icon size={16} color="var(--clr-primary)" />
              </div>
              <div>
                <div style={{ fontSize:'0.7rem', fontWeight:600, color:'var(--clr-text-muted)', textTransform:'uppercase' }}>{f.label}</div>
                <div style={{ fontWeight:600, color:'var(--clr-navy)' }}>{f.value}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-header"><div className="card-title">Gait & Activity Profile</div></div>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
          {[
            { label:'Mobility Level',     value:p.mobility_level },
            { label:'Activity Frequency', value:p.activity_frequency },
            { label:'Walking Changes',    value:p.walking_change },
            { label:'Assessment Goal',    value:p.assessment_goal },
          ].map(f => (
            <div key={f.label}>
              <div style={{ fontSize:'0.7rem', fontWeight:600, color:'var(--clr-text-muted)', textTransform:'uppercase', marginBottom:4 }}>{f.label}</div>
              <div style={{ fontWeight:600, color:'var(--clr-navy)', padding:'8px 12px', background:'var(--clr-surface-2)', borderRadius:8 }}>{f.value || '—'}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop:20, textAlign:'center', fontSize:'0.8rem', color:'var(--clr-text-muted)' }}>
        Account created: {p.created_at ? new Date(p.created_at).toLocaleDateString('en-GB', { day:'numeric', month:'long', year:'numeric' }) : '—'}
      </div>
    </div>
  );
}
