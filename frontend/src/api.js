export const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const KEY = 'crisismind.token';
export const getToken = () => { try { return localStorage.getItem(KEY) } catch { return null } };
export const setToken = t => { try { t ? localStorage.setItem(KEY, t) : localStorage.removeItem(KEY) } catch { /* private mode */ } };

export async function api(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  const t = getToken();
  if (t) headers.Authorization = 'Bearer ' + t;
  let res;
  try { res = await fetch(API + path, { method, headers, body: body ? JSON.stringify(body) : undefined }); }
  catch { throw new Error('Backend not reachable. Start it with: python main.py'); }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    throw new Error(typeof d === 'string' ? d : Array.isArray(d) ? d.map(x => x.msg).join(', ') : 'Request failed');
  }
  return data;
}

export const logAction = (action, scenario = 'fire', payload) =>
  api('/api/actions', { method: 'POST', body: { action, scenario, payload } }).catch(() => {});

export const MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';
export const MAP_CENTER = {
  lat: parseFloat(import.meta.env.VITE_MAP_CENTER_LAT) || 28.6139,
  lng: parseFloat(import.meta.env.VITE_MAP_CENTER_LNG) || 77.2090,
};
