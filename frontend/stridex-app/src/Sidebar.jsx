import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Users, ClipboardList, Activity,
  BarChart2, FileText, LogOut, User, TrendingUp, Target,
} from 'lucide-react';
import { useAuth } from './AuthContext';

const DOCTOR_NAV = [
  { section: 'Overview', items: [
    { label: 'Dashboard',      icon: LayoutDashboard, path: '/app/dashboard' },
    { label: 'Patients',       icon: Users,           path: '/app/patients' },
    { label: 'Assessments',    icon: ClipboardList,   path: '/app/assessments' },
  ]},
  { section: 'Clinical Tools', items: [
    { label: 'New Assessment', icon: Activity,        path: '/app/assess/new' },
    { label: 'Reports',        icon: FileText,        path: '/app/reports' },
    { label: 'Analytics',      icon: BarChart2,       path: '/app/analytics' },
  ]},
];

const PATIENT_NAV = [
  { section: 'My Health', items: [
    { label: 'Dashboard',        icon: LayoutDashboard, path: '/app/patient/dashboard' },
    { label: 'New Assessment',   icon: Activity,        path: '/app/patient/assessment/new' },
    { label: 'My Assessments',   icon: ClipboardList,   path: '/app/patient/assessments' },
    { label: 'My Baseline',      icon: Target,          path: '/app/patient/baseline' },
    { label: 'Progress',         icon: TrendingUp,      path: '/app/patient/progress' },
    { label: 'Reports',          icon: FileText,        path: '/app/patient/reports' },
  ]},
  { section: 'Account', items: [
    { label: 'Profile',          icon: User,            path: '/app/patient/profile' },
  ]},
];

function initials(name) {
  if (!name) return 'U';
  return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
}

export default function Sidebar() {
  const navigate  = useNavigate();
  const location  = useLocation();
  const { user, signOut, isDoctor } = useAuth();

  const navGroups = isDoctor ? DOCTOR_NAV : PATIENT_NAV;

  const handleSignOut = () => {
    signOut();
    navigate('/login');
  };

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo" style={{ cursor:'pointer' }} onClick={() => navigate('/')}>
        <div style={{
          width:36, height:36, borderRadius:10,
          background:'linear-gradient(135deg,#1a56db 0%,#3b82f6 100%)',
          display:'flex', alignItems:'center', justifyContent:'center',
          fontSize:'1.1rem', color:'#fff', fontWeight:700, fontFamily:'Space Grotesk,sans-serif'
        }}>S</div>
        <div>
          <div className="sidebar-logo-text">StrideX</div>
          <div className="sidebar-logo-tag">{isDoctor ? 'Clinical Portal' : 'Patient Portal'}</div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ padding:'8px 0', flex:1, overflowY:'auto' }}>
        {navGroups.map(group => (
          <div key={group.section} className="sidebar-section">
            <div className="sidebar-section-label">{group.section}</div>
            {group.items.map(item => {
              const Icon   = item.icon;
              const active = location.pathname === item.path ||
                             location.pathname.startsWith(item.path + '/');
              return (
                <div
                  key={item.path}
                  className={`nav-item${active ? ' active' : ''}`}
                  onClick={() => navigate(item.path)}
                >
                  <Icon size={16} />
                  <span style={{ flex:1 }}>{item.label}</span>
                </div>
              );
            })}
          </div>
        ))}
      </nav>

      {/* User Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-user" style={{ cursor:'default' }}>
          <div className="sidebar-avatar">{initials(user?.name)}</div>
          <div style={{ flex:1, minWidth:0 }}>
            <div className="sidebar-user-name" style={{ whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>
              {user?.name || 'User'}
            </div>
            <div className="sidebar-user-role">
              {isDoctor ? 'Clinician' : `Patient · ${user?.id || ''}`}
            </div>
          </div>
        </div>
        <div
          style={{ display:'flex', alignItems:'center', gap:8, padding:'8px 16px',
                   cursor:'pointer', color:'rgba(255,255,255,0.5)', fontSize:'0.8125rem' }}
          onClick={handleSignOut}
        >
          <LogOut size={14} /> Sign Out
        </div>
      </div>
    </aside>
  );
}
