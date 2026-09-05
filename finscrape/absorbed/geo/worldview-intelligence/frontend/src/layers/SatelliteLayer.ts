import {
  Viewer, CustomDataSource, Cartesian3, Cartesian2, Color,
  NearFarScalar, DistanceDisplayCondition, LabelStyle,
  VerticalOrigin, HorizontalOrigin,
} from 'cesium';
import { ENTITY_ICONS } from '../services/icons';
import type { Satellite } from '../types';

const CATEGORY_COLOR: Record<Satellite['category'], Color> = {
  iss: Color.LIME,
  starlink: Color.WHITE,
  military: Color.ORANGE,
  communication: Color.LIGHTBLUE,
  weather: Color.LIGHTBLUE,
  navigation: Color.LIGHTBLUE,
  scientific: Color.LIGHTBLUE,
  unknown: Color.LIGHTBLUE,
};

const DS_NAME = 'satellite-layer';

let lastData: Satellite[] = [];
let dataSource: CustomDataSource | null = null;

function buildOrbitalArc(sat: Satellite): Cartesian3[] {
  const { lng, lat, alt = 400_000 } = sat.position;
  const incRad = (sat.inclination * Math.PI) / 180;
  const points: Cartesian3[] = [];
  const arcSpan = 30;
  const segments = 60;

  for (let i = 0; i <= segments; i++) {
    const t = (i / segments - 0.5) * arcSpan;
    const aLng = lng + t;
    const aLat = lat + Math.sin((t * Math.PI) / arcSpan) * Math.sin(incRad) * 5;
    points.push(Cartesian3.fromDegrees(aLng, aLat, alt));
  }
  return points;
}

export function updateSatelliteLayer(viewer: Viewer, data: Satellite[], visible: boolean): void {
  if (!dataSource) {
    dataSource = new CustomDataSource(DS_NAME);
    viewer.dataSources.add(dataSource);
  }

  dataSource.show = visible;

  if (data === lastData) return;
  lastData = data;

  dataSource.entities.removeAll();

  for (const sat of data) {
    const color = CATEGORY_COLOR[sat.category] ?? Color.LIGHTBLUE;
    const { lng, lat, alt = 400_000 } = sat.position;
    const isISS = sat.category === 'iss';
    const isStarlink = sat.category === 'starlink';

    dataSource.entities.add({
      id: `satellite-${sat.id}`,
      position: Cartesian3.fromDegrees(lng, lat, alt),
      name: sat.name,
      billboard: {
        image: isISS ? ENTITY_ICONS.satellite_iss : ENTITY_ICONS.satellite,
        width: isISS ? 24 : isStarlink ? 12 : 16,
        height: isISS ? 24 : isStarlink ? 12 : 16,
        scaleByDistance: new NearFarScalar(1e5, 1.2, 1e8, 0.3),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 1e8),
      },
      label: (isISS || !isStarlink) ? {
        text: isISS ? sat.name : sat.name,
        font: isISS ? '12px monospace' : '10px monospace',
        fillColor: color,
        outlineColor: Color.BLACK,
        outlineWidth: 2,
        style: LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cartesian2(12, -4),
        scaleByDistance: new NearFarScalar(1e5, 1.0, isISS ? 1e7 : 3e6, 0.0),
        distanceDisplayCondition: new DistanceDisplayCondition(0, isISS ? 1e7 : 3e6),
        verticalOrigin: VerticalOrigin.CENTER,
        horizontalOrigin: HorizontalOrigin.LEFT,
      } : undefined,
      properties: {
        layerType: 'satellite',
        entityId: sat.id,
        rawData: sat,
        geoPosition: sat.position,
      } as any,
    });

    if (!isStarlink) {
      dataSource.entities.add({
        id: `satellite-orbit-${sat.id}`,
        polyline: {
          positions: buildOrbitalArc(sat),
          width: 1,
          material: color.withAlpha(0.15),
        },
      });
    }
  }
}
