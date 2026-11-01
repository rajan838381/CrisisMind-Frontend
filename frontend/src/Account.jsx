import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { X, MapPin, Trash2, LogIn, FileText } from 'lucide-react';
import GoogleMap from './GoogleMap.jsx';
import { api, MAP_CENTER, setToken } from './api.js';

export function AuthModal({ onClose, onDone, notify }) {
  const [mode, setMode] = useState('login'), [f, setF] = useState({ name: '', email: '', phone: '', city: '', password: '', role: 'operator' }), [busy, setBusy] = useState(false), [err, setErr] = useState('');
  const set = k => e => setF({ ...f, [k]: e.target.value });
  const submit = async e => {
    e.preventDefault(); setBusy(true); setErr('');
    try {
      const r = await api('/api/auth/' + mode, { method: 'POST', body: mode === 'login' ? { email: f.email, password: f.password } : f });
      setToken(r.token); onDone(r.user); notify(`Welcome, ${r.user.name}`, 'ok'); onClose();
    } catch (x) { setErr(x.message); } finally { setBusy(false); }
  };
  return <div className="modal-back" onMouseDown={e => e.target === e.currentTarget && onClose()}>
    <form className="modal" onSubmit={submit} role="dialog" aria-modal="true" aria-label="Sign in">
      <button type="button" className="modal-x" onClick={onClose} aria-label="Close"><X size={18} /></button>
      <h2>{mode === 'login' ? 'Sign in' : 'Create account'}</h2>
      <p className="muted-p">Your reports, simulations and decisions are saved to the SQL database.</p>
      {mode === 'register' && <label>Full name<input required minLength={2} value={f.name} onChange={set('name')} autoComplete="name" /></label>}
      <label>Email<input required type="email" value={f.email} onChange={set('email')} autoComplete="email" /></label>
      {mode === 'register' && <div className="two"><label>Phone<input value={f.phone} onChange={set('phone')} autoComplete="tel" /></label>
        <label>City<input value={f.city} onChange={set('city')} autoComplete="address-level2" /></label></div>}
      {mode === 'register' && <div className="two"><label>Role<select value={f.role} onChange={set('role')}><option value="operator">Operator</option><option value="commander">Commander</option><option value="citizen">Citizen</option></select></label></div>}
      <label>Password<input required type="password" minLength={6} value={f.password} onChange={set('password')} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} /></label>
      {err && <div className="form-err" role="alert">{err}</div>}
      <button className="primary full" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}</button>
      <button type="button" className="switch" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setErr(''); }}>
        {mode === 'login' ? 'New here? Create an account' : 'Already registered? Sign in'}</button>
    </form></div>;
}

const COLORS = { fire: '#ff5a4e', flood: '#5aa9ff', accident: '#ff9a3d', chemical: '#b779ff', crowd: '#f2c14e', storm: '#7ee0e0', other: '#9aa7b3' };
const hosp = [{ id: 'h', d: [.03, .045], t: 'Hospital B — St. Jude', c: '#5aa9ff', l: 'H' }, { id: 's', d: [-.028, .05], t: 'Shelter 2 — North County', c: '#3ddc97', l: 'S' }, { id: 'f', d: [-.035, -.05], t: 'Fire Station 01', c: '#ff9a3d', l: 'F' }];
const off = (c, [a, b]) => ({ lat: c.lat + a, lng: c.lng + b });

export function GoogleMapPage({ user, requireLogin, notify, risk, scenario }) {
  const [reports, setReports] = useState([]), [picked, setPicked] = useState(null), [busy, setBusy] = useState(false);
  const [f, setF] = useState({ category: scenario === 'accident' ? 'accident' : scenario, title: '', description: '', severity: 'medium', address: '' });
  const load = useCallback(() => api('/api/reports').then(setReports).catch(() => {}), []);
  useEffect(() => { load(); }, [load, user]);
  const c = MAP_CENTER;
  const markers = useMemo(() => [
    { position: c, title: 'Hazard zone — Sector 7', color: '#ff5a4e', label: '!', info: `Risk ${risk}/100` },
    ...hosp.map(h => ({ position: off(c, h.d), title: h.t, color: h.c, label: h.l })),
    ...reports.filter(r => r.latitude != null).map(r => ({ position: { lat: r.latitude, lng: r.longitude }, title: r.title, color: COLORS[r.category] || '#9aa7b3', info: `${r.category} · ${r.severity}<br>${r.description || ''}` })),
  ], [reports, risk, c.lat, c.lng]);
  const circles = useMemo(() => [{ center: c, radius: 500 + risk * 14, color: '#ff5a4e' }], [risk, c.lat, c.lng]);
  const lines = useMemo(() => [
    { path: [off(c, [-.035, -.05]), off(c, [-.035, .045]), off(c, [.03, .045])], color: '#3ddc97' },
    { path: [off(c, [-.035, -.05]), off(c, [0, 0]), off(c, [.03, .045])], color: '#ff5a4e', dashed: true },
  ], [c.lat, c.lng]);
  const submit = async e => {
    e.preventDefault();
    if (!user) return requireLogin();
    if (!picked) return notify('Click on the map to choose the incident location', 'bad');
    setBusy(true);
    try { await api('/api/reports', { method: 'POST', body: { ...f, latitude: picked.lat, longitude: picked.lng } }); notify('Report saved to database', 'ok'); setF({ ...f, title: '', description: '', address: '' }); setPicked(null); load(); }
    catch (x) { notify(x.message, 'bad'); } finally { setBusy(false); }
  };
  const set = k => e => setF({ ...f, [k]: e.target.value });
  return <div className="page"><div className="section-intro"><div><h2>Live Google Map</h2><p>Real street map with hazard zone, routes, facilities and citizen reports. Click the map to report an incident.</p></div></div>
    <div className="gmap-layout">
      <section className="card gmap-card"><GoogleMap center={c} markers={markers} circles={circles} lines={lines} onPick={setPicked} picked={picked} />
        <div className="map-legend static"><span><i className="green-dot" /> SAFE ROUTE</span><span><i className="red-dot" /> HAZARD / AVOID</span><span><i className="blue-dot" /> FACILITY</span></div></section>
      <form className="card report-form" onSubmit={submit}>
        <div className="card-title"><span>Report an incident</span></div>
        <div className={'loc-chip' + (picked ? ' on' : '')}><MapPin size={15} />{picked ? `${picked.lat}, ${picked.lng}` : 'Click on the map to set location'}</div>
        <label>Type<select value={f.category} onChange={set('category')}>{Object.keys(COLORS).map(k => <option key={k} value={k}>{k[0].toUpperCase() + k.slice(1)}</option>)}</select></label>
        <label>Title<input required minLength={3} maxLength={140} value={f.title} onChange={set('title')} placeholder="e.g. Smoke near market road" /></label>
        <label>Severity<select value={f.severity} onChange={set('severity')}>{['low', 'medium', 'high', 'critical'].map(k => <option key={k}>{k}</option>)}</select></label>
        <label>Address / landmark<input value={f.address} onChange={set('address')} maxLength={300} /></label>
        <label>Details<textarea rows={3} maxLength={2000} value={f.description} onChange={set('description')} /></label>
        <button className="primary full" disabled={busy}>{user ? (busy ? 'Saving…' : 'Save report') : 'Sign in to report'}</button>
      </form>
    </div></div>;
}

function Profile({ user, onSaved, notify }) {
  const init = () => ({ name: user.name || '', phone: user.phone || '', city: user.city || '', address: user.address || '', bloodGroup: user.bloodGroup || '', emergencyContactName: user.emergencyContactName || '', emergencyContactPhone: user.emergencyContactPhone || '' });
  const [f, setF] = useState(init), [busy, setBusy] = useState(false);
  useEffect(() => setF(init()), [user]);
  const set = k => e => setF({ ...f, [k]: e.target.value });
  const save = async e => {
    e.preventDefault(); setBusy(true);
    try { const r = await api('/api/auth/profile', { method: 'PUT', body: f }); onSaved(r.user); notify('Profile saved to database', 'ok'); }
    catch (x) { notify(x.message, 'bad'); } finally { setBusy(false); }
  };
  return <form className="card profile" onSubmit={save}><div className="card-title"><span>My profile (saved in SQL)</span></div>
    <div className="profile-grid">
      <label>Name<input required minLength={2} value={f.name} onChange={set('name')} /></label>
      <label>Email<input value={user.email} disabled /></label>
      <label>Phone<input value={f.phone} onChange={set('phone')} /></label>
      <label>City<input value={f.city} onChange={set('city')} /></label>
      <label>Blood group<select value={f.bloodGroup} onChange={set('bloodGroup')}><option value="">—</option>{['A+','A-','B+','B-','AB+','AB-','O+','O-'].map(b => <option key={b}>{b}</option>)}</select></label>
      <label>Address<input value={f.address} onChange={set('address')} /></label>
      <label>Emergency contact name<input value={f.emergencyContactName} onChange={set('emergencyContactName')} /></label>
      <label>Emergency contact phone<input value={f.emergencyContactPhone} onChange={set('emergencyContactPhone')} /></label>
    </div><button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save profile'}</button></form>;
}

export function MyData({ user, setUser, requireLogin, notify }) {
  const [d, setD] = useState({ reports: [], actions: [], sims: [] });
  const load = useCallback(async () => {
    if (!user) return;
    try { const [reports, actions, sims] = await Promise.all([api('/api/reports?mine=true'), api('/api/actions'), api('/api/simulations')]); setD({ reports, actions, sims }); }
    catch (x) { notify(x.message, 'bad'); }
  }, [user, notify]);
  useEffect(() => { load(); }, [load]);
  if (!user) return <div className="page"><section className="card empty"><LogIn size={28} /><h3>Sign in to see your saved data</h3><p>Reports, simulations and approved actions are stored in the SQL database against your account.</p><button className="primary" onClick={requireLogin}>Sign in</button></section></div>;
  const del = async id => { try { await api('/api/reports/' + id, { method: 'DELETE' }); notify('Report deleted', 'info'); load(); } catch (x) { notify(x.message, 'bad'); } };
  return <div className="page"><div className="section-intro"><div><h2>My Data</h2><p>Everything saved for {user.email}.</p></div></div>
    <Profile user={user} onSaved={setUser} notify={notify} />
    <div className="metrics three"><div className="metric"><div className="metric-label">Reports</div><div className="metric-value">{d.reports.length}</div></div><div className="metric"><div className="metric-label">Simulations</div><div className="metric-value">{d.sims.length}</div></div><div className="metric"><div className="metric-label">Actions logged</div><div className="metric-value">{d.actions.length}</div></div></div>
    <div className="data-cols">
      <section className="card"><div className="card-title"><span>My incident reports</span></div>{!d.reports.length && <p className="muted-p">No reports yet. Use the Live Google Map page.</p>}
        {d.reports.map(r => <div className="list-row" key={r.id}><FileText size={16} /><div><b>{r.title}</b><small>{r.category} · {r.severity} · {r.createdAt}{r.latitude != null && ` · ${r.latitude}, ${r.longitude}`}</small></div><button onClick={() => del(r.id)} aria-label="Delete report"><Trash2 size={15} /></button></div>)}</section>
      <section className="card"><div className="card-title"><span>Simulation history</span></div>{!d.sims.length && <p className="muted-p">Run the What-If Simulator to save results.</p>}
        {d.sims.map(s => <div className="list-row" key={s.id}><div><b>Risk {s.baselineRisk} → {s.simulatedRisk}</b><small>{s.scenario} · {Object.entries(s.actions).filter(([, v]) => v).length} actions · {s.createdAt}</small></div></div>)}</section>
      <section className="card"><div className="card-title"><span>Action history</span></div>{!d.actions.length && <p className="muted-p">Approvals and button actions appear here.</p>}
        {d.actions.slice(0, 30).map(a => <div className="list-row" key={a.id}><div><b>{a.action}</b><small>{a.scenario} · {a.createdAt}</small></div></div>)}</section>
    </div></div>;
}
