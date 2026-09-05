function svgToDataUri(svg: string): string {
  return 'data:image/svg+xml;base64,' + btoa(svg);
}

export const ENTITY_ICONS = {
  aircraft: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><path d="M16 2 L14 12 L4 18 L6 20 L14 17 L14 24 L10 27 L12 28 L16 26 L20 28 L22 27 L18 24 L18 17 L26 20 L28 18 L18 12 Z" fill="#00d4ff" stroke="#003355" stroke-width="0.5"/></svg>`),

  aircraft_military: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><path d="M16 2 L14 12 L4 18 L6 20 L14 17 L14 24 L10 27 L12 28 L16 26 L20 28 L22 27 L18 24 L18 17 L26 20 L28 18 L18 12 Z" fill="#ff3b5c" stroke="#550011" stroke-width="0.5"/></svg>`),

  aircraft_cargo: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><path d="M16 2 L14 12 L4 18 L6 20 L14 17 L14 24 L10 27 L12 28 L16 26 L20 28 L22 27 L18 24 L18 17 L26 20 L28 18 L18 12 Z" fill="#f0a030" stroke="#553300" stroke-width="0.5"/></svg>`),

  satellite: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><rect x="8" y="8" width="8" height="8" rx="1" fill="#8066ff" stroke="#332266" stroke-width="0.5"/><line x1="3" y1="12" x2="8" y2="12" stroke="#8066ff" stroke-width="1.5"/><line x1="16" y1="12" x2="21" y2="12" stroke="#8066ff" stroke-width="1.5"/><rect x="1" y="9" width="4" height="6" rx="0.5" fill="#8066ff" opacity="0.6"/><rect x="19" y="9" width="4" height="6" rx="0.5" fill="#8066ff" opacity="0.6"/></svg>`),

  satellite_iss: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><rect x="10" y="10" width="8" height="8" rx="1" fill="#00e87b" stroke="#004422" stroke-width="0.5"/><line x1="3" y1="14" x2="10" y2="14" stroke="#00e87b" stroke-width="2"/><line x1="18" y1="14" x2="25" y2="14" stroke="#00e87b" stroke-width="2"/><rect x="1" y="11" width="5" height="6" rx="0.5" fill="#00e87b" opacity="0.7"/><rect x="22" y="11" width="5" height="6" rx="0.5" fill="#00e87b" opacity="0.7"/></svg>`),

  ship: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M4 18 L6 10 L12 8 L18 10 L20 18 Z" fill="#00c5b0" stroke="#003330" stroke-width="0.5"/><line x1="12" y1="8" x2="12" y2="4" stroke="#00c5b0" stroke-width="1.5"/><path d="M2 19 Q6 22 12 22 Q18 22 22 19" fill="none" stroke="#00c5b0" stroke-width="1" opacity="0.5"/></svg>`),

  ship_naval: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M4 18 L6 10 L12 8 L18 10 L20 18 Z" fill="#ff3b5c" stroke="#550011" stroke-width="0.5"/><line x1="12" y1="8" x2="12" y2="4" stroke="#ff3b5c" stroke-width="1.5"/><path d="M2 19 Q6 22 12 22 Q18 22 22 19" fill="none" stroke="#ff3b5c" stroke-width="1" opacity="0.5"/></svg>`),

  ship_tanker: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M4 18 L6 10 L12 8 L18 10 L20 18 Z" fill="#f0a030" stroke="#553300" stroke-width="0.5"/><line x1="12" y1="8" x2="12" y2="4" stroke="#f0a030" stroke-width="1.5"/><path d="M2 19 Q6 22 12 22 Q18 22 22 19" fill="none" stroke="#f0a030" stroke-width="1" opacity="0.5"/></svg>`),

  earthquake: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="none" stroke="#f07030" stroke-width="1.5" opacity="0.5"/><circle cx="12" cy="12" r="4" fill="none" stroke="#f07030" stroke-width="1.5" opacity="0.8"/><circle cx="12" cy="12" r="2" fill="#f07030"/></svg>`),

  earthquake_major: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><circle cx="14" cy="14" r="11" fill="none" stroke="#ff3b5c" stroke-width="1.5" opacity="0.4"/><circle cx="14" cy="14" r="7" fill="none" stroke="#ff3b5c" stroke-width="1.5" opacity="0.6"/><circle cx="14" cy="14" r="3" fill="#ff3b5c"/></svg>`),

  conflict: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><polygon points="12,2 15,9 22,9 16,14 18,22 12,17 6,22 8,14 2,9 9,9" fill="#ff3b5c" stroke="#550011" stroke-width="0.5" opacity="0.9"/></svg>`),

  conflict_protest: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><polygon points="12,2 15,9 22,9 16,14 18,22 12,17 6,22 8,14 2,9 9,9" fill="#f0a030" stroke="#553300" stroke-width="0.5" opacity="0.9"/></svg>`),

  missile: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M12 2 L14 8 L18 10 L14 12 L12 22 L10 12 L6 10 L10 8 Z" fill="#e02060" stroke="#550011" stroke-width="0.5"/><circle cx="12" cy="10" r="2" fill="#ff6688"/></svg>`),

  news: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><rect x="3" y="3" width="14" height="14" rx="2" fill="#f0a030" stroke="#553300" stroke-width="0.5" opacity="0.9"/><line x1="6" y1="7" x2="14" y2="7" stroke="#553300" stroke-width="1"/><line x1="6" y1="10" x2="14" y2="10" stroke="#553300" stroke-width="1" opacity="0.6"/><line x1="6" y1="13" x2="11" y2="13" stroke="#553300" stroke-width="1" opacity="0.4"/></svg>`),

  traffic: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><rect x="7" y="2" width="6" height="16" rx="3" fill="#1a1a2e" stroke="#70c040" stroke-width="1"/><circle cx="10" cy="6" r="1.5" fill="#ff3b5c"/><circle cx="10" cy="10" r="1.5" fill="#f0a030"/><circle cx="10" cy="14" r="1.5" fill="#70c040"/></svg>`),

  weather: svgToDataUri(`<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><circle cx="10" cy="8" r="4" fill="#50b0e0" opacity="0.8"/><path d="M4 14 Q6 12 8 14 Q10 12 12 14 Q14 12 16 14" fill="none" stroke="#50b0e0" stroke-width="1.5" opacity="0.6"/></svg>`),
};

const iconCache = new Map<string, HTMLCanvasElement>();

export function getIconCanvas(key: keyof typeof ENTITY_ICONS): Promise<HTMLCanvasElement> {
  const cached = iconCache.get(key);
  if (cached) return Promise.resolve(cached);

  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(img, 0, 0);
      iconCache.set(key, canvas);
      resolve(canvas);
    };
    img.src = ENTITY_ICONS[key];
  });
}
