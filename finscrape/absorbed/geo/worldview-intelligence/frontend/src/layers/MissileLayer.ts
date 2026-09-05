import {
  Viewer, CustomDataSource, Cartesian3, Cartesian2, Color,
  NearFarScalar, LabelStyle, VerticalOrigin, HorizontalOrigin,
} from 'cesium';
import { ENTITY_ICONS } from '../services/icons';
import type { MissileLaunch } from '../types';

const DS_NAME = 'missile-layer';

let lastData: MissileLaunch[] = [];
let dataSource: CustomDataSource | null = null;

function buildArcTrajectory(launch: MissileLaunch): Cartesian3[] {
  const { trajectory, launchSite, predictedImpact } = launch;

  if (trajectory.length >= 2) {
    return trajectory.map((p) =>
      Cartesian3.fromDegrees(p.lng, p.lat, p.alt ?? 0)
    );
  }

  const start = launchSite;
  const end = predictedImpact ?? launchSite;
  const points: Cartesian3[] = [];
  const segments = 40;

  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    const lng = start.lng + (end.lng - start.lng) * t;
    const lat = start.lat + (end.lat - start.lat) * t;
    const alt = Math.sin(t * Math.PI) * 300_000;
    points.push(Cartesian3.fromDegrees(lng, lat, alt));
  }

  return points;
}

export function updateMissileLayer(viewer: Viewer, data: MissileLaunch[], visible: boolean): void {
  if (!dataSource) {
    dataSource = new CustomDataSource(DS_NAME);
    viewer.dataSources.add(dataSource);
  }

  dataSource.show = visible;

  if (data === lastData) return;
  lastData = data;

  dataSource.entities.removeAll();

  for (const m of data) {
    const { lng, lat } = m.launchSite;

    dataSource.entities.add({
      id: `missile-site-${m.id}`,
      position: Cartesian3.fromDegrees(lng, lat, 0),
      name: m.description,
      billboard: {
        image: ENTITY_ICONS.missile,
        width: 24,
        height: 24,
        scaleByDistance: new NearFarScalar(1e4, 1.2, 1e7, 0.3),
      },
      label: {
        text: `▲ ${m.type.toUpperCase()}`,
        font: '11px monospace',
        fillColor: Color.RED,
        outlineColor: Color.BLACK,
        outlineWidth: 2,
        style: LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cartesian2(14, -8),
        scaleByDistance: new NearFarScalar(1e4, 1.0, 5e6, 0.0),
        verticalOrigin: VerticalOrigin.CENTER,
        horizontalOrigin: HorizontalOrigin.LEFT,
      },
      properties: {
        layerType: 'missiles',
        entityId: m.id,
        rawData: m,
        geoPosition: m.launchSite,
      } as any,
    });

    dataSource.entities.add({
      id: `missile-arc-${m.id}`,
      polyline: {
        positions: buildArcTrajectory(m),
        width: 2,
        material: Color.RED.withAlpha(0.7),
      },
    });

    if (m.predictedImpact) {
      dataSource.entities.add({
        id: `missile-impact-${m.id}`,
        position: Cartesian3.fromDegrees(
          m.predictedImpact.lng,
          m.predictedImpact.lat,
          0
        ),
        point: {
          pixelSize: 10,
          color: Color.RED.withAlpha(0.7),
          outlineColor: Color.RED.withAlpha(0.3),
          outlineWidth: 8,
        },
      });
    }
  }
}
