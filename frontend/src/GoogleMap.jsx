import React, { useEffect, useRef, useState } from 'react';
import { MAPS_KEY } from './api.js';

let loader;
function loadMaps() {
  if (window.google?.maps) return Promise.resolve(window.google.maps);
  if (loader) return loader;
  loader = new Promise((resolve, reject) => {
    window.__cmMapsReady = () => resolve(window.google.maps);
    window.gm_authFailure = () => reject(new Error('Google rejected the API key. Check the key, billing and allowed referrers.'));
    const s = document.createElement('script');
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(MAPS_KEY)}&callback=__cmMapsReady&v=weekly`;
    s.async = true;
    s.onerror = () => reject(new Error('Could not load Google Maps. Check your internet connection.'));
    document.head.append(s);
  });
  loader.catch(() => { loader = null; });
  return loader;
}

const DARK = [
  { elementType: 'geometry', stylers: [{ color: '#0f1923' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#8b99a6' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#0a1016' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#1f2d3a' }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#2c4157' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#08141f' }] },
  { featureType: 'poi', stylers: [{ visibility: 'off' }] },
];

/**
 * props: center {lat,lng}, zoom, markers [{id,position,title,color,label,info}],
 * circles [{center,radius,color}], lines [{path,color,dashed}], onPick(latlng), picked {lat,lng}
 */
export default function GoogleMap({ center, zoom = 13, markers = [], circles = [], lines = [], onPick, picked, className = '' }) {
  const el = useRef(null), map = useRef(null), layers = useRef([]), pickRef = useRef(null), onPickRef = useRef(onPick);
  const [err, setErr] = useState('');
  onPickRef.current = onPick;

  useEffect(() => {
    if (!MAPS_KEY) return;
    let dead = false;
    loadMaps().then(maps => {
      if (dead || !el.current) return;
      map.current = new maps.Map(el.current, { center, zoom, styles: DARK, disableDefaultUI: true, zoomControl: true, fullscreenControl: true, clickableIcons: false, gestureHandling: 'cooperative' });
      map.current.addListener('click', e => onPickRef.current?.({ lat: +e.latLng.lat().toFixed(6), lng: +e.latLng.lng().toFixed(6) }));
      setErr('ready');
    }).catch(e => !dead && setErr(e.message));
    return () => { dead = true; };
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    const maps = window.google?.maps;
    if (!maps || !map.current || err !== 'ready') return;
    layers.current.forEach(l => l.setMap(null)); layers.current = [];
    const iw = new maps.InfoWindow();
    markers.forEach(m => {
      const mk = new maps.Marker({ map: map.current, position: m.position, title: m.title, label: m.label ? { text: m.label, color: '#fff', fontWeight: '700' } : undefined,
        icon: { path: maps.SymbolPath.CIRCLE, scale: 11, fillColor: m.color || '#5aa9ff', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 2 } });
      mk.addListener('click', () => { iw.setContent(`<div style="color:#111;font:13px Figtree,sans-serif"><b>${m.title}</b>${m.info ? '<br>' + m.info : ''}</div>`); iw.open(map.current, mk); });
      layers.current.push(mk);
    });
    circles.forEach(c => layers.current.push(new maps.Circle({ map: map.current, center: c.center, radius: c.radius, strokeColor: c.color, strokeOpacity: .8, strokeWeight: 2, fillColor: c.color, fillOpacity: .18 })));
    lines.forEach(l => layers.current.push(new maps.Polyline({ map: map.current, path: l.path, strokeColor: l.color, strokeOpacity: l.dashed ? 0 : .9, strokeWeight: 5,
      icons: l.dashed ? [{ icon: { path: 'M 0,-1 0,1', strokeOpacity: 1, scale: 3 }, offset: '0', repeat: '14px' }] : undefined })));
  }, [markers, circles, lines, err]);

  useEffect(() => {
    const maps = window.google?.maps;
    if (!maps || !map.current || err !== 'ready') return;
    pickRef.current?.setMap(null);
    if (picked) pickRef.current = new maps.Marker({ map: map.current, position: picked, title: 'Selected location', animation: maps.Animation.DROP });
  }, [picked, err]);

  useEffect(() => { if (map.current && center) map.current.panTo(center); }, [center?.lat, center?.lng]);

  if (!MAPS_KEY) return (
    <div className={'gmap gmap-setup ' + className}>
      <b>Google Maps key not added yet</b>
      <ol>
        <li>Open <code>frontend/.env.example</code> and copy it to <code>frontend/.env</code></li>
        <li>Paste your key: <code>VITE_GOOGLE_MAPS_API_KEY=AIza...</code></li>
        <li>Restart <code>npm run dev</code></li>
      </ol>
      <small>Maps JavaScript API must be enabled in Google Cloud.</small>
    </div>);
  return <div className={'gmap ' + className}><div ref={el} className="gmap-canvas" />{err && err !== 'ready' && <div className="gmap-error">{err}</div>}</div>;
}
