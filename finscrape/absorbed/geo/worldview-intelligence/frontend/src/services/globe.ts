import { Viewer, Cartesian3 } from 'cesium';

let viewerInstance: Viewer | null = null;

export function setGlobeViewer(viewer: Viewer | null): void {
  viewerInstance = viewer;
}

export function getGlobeViewer(): Viewer | null {
  return viewerInstance;
}

export function flyTo(lat: number, lng: number, alt?: number): void {
  const viewer = viewerInstance;
  if (!viewer || viewer.isDestroyed()) return;

  viewer.camera.flyTo({
    destination: Cartesian3.fromDegrees(lng, lat, alt ?? 2_000_000),
    duration: 1.5,
  });
}

export function flyToEntity(lat: number, lng: number, zoomAlt?: number): void {
  const viewer = viewerInstance;
  if (!viewer || viewer.isDestroyed()) return;

  viewer.camera.flyTo({
    destination: Cartesian3.fromDegrees(lng, lat, zoomAlt ?? 500_000),
    duration: 1.2,
  });
}
