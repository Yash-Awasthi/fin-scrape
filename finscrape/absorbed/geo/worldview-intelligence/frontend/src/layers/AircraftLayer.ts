import {
  Viewer, CustomDataSource, Cartesian3, Cartesian2, Color,
  NearFarScalar, DistanceDisplayCondition, LabelStyle,
  VerticalOrigin, HorizontalOrigin,
} from 'cesium';
import { ENTITY_ICONS } from '../services/icons';
import type { Aircraft } from '../types';

const CATEGORY_COLOR: Record<Aircraft['category'], Color> = {
  commercial: Color.CYAN,
  military: Color.RED,
  private: Color.LIGHTYELLOW,
  cargo: Color.ORANGE,
  unknown: Color.GRAY,
};

const DS_NAME = 'aircraft-layer';

let lastData: Aircraft[] = [];
let dataSource: CustomDataSource | null = null;

function buildTrailPositions(ac: Aircraft): Cartesian3[] {
  const { lng, lat, alt = 10000 } = ac.position;
  const headingRad = (ac.heading * Math.PI) / 180;
  const trailLength = 0.5;
  const trailLng = lng - Math.sin(headingRad) * trailLength;
  const trailLat = lat - Math.cos(headingRad) * trailLength;
  return [
    Cartesian3.fromDegrees(trailLng, trailLat, alt),
    Cartesian3.fromDegrees(lng, lat, alt),
  ];
}

export function updateAircraftLayer(viewer: Viewer, data: Aircraft[], visible: boolean): void {
  if (!dataSource) {
    dataSource = new CustomDataSource(DS_NAME);
    viewer.dataSources.add(dataSource);
  }

  dataSource.show = visible;

  if (data === lastData) return;
  lastData = data;

  dataSource.entities.removeAll();

  for (const ac of data) {
    const color = CATEGORY_COLOR[ac.category] ?? Color.GRAY;
    const { lng, lat, alt = 10000 } = ac.position;

    dataSource.entities.add({
      id: `aircraft-${ac.icao24}`,
      position: Cartesian3.fromDegrees(lng, lat, alt),
      name: ac.callsign || ac.icao24,
      billboard: {
        image: ac.category === 'military' ? ENTITY_ICONS.aircraft_military
          : ac.category === 'cargo' ? ENTITY_ICONS.aircraft_cargo
          : ENTITY_ICONS.aircraft,
        width: 22,
        height: 22,
        scaleByDistance: new NearFarScalar(1e4, 1.2, 1e7, 0.3),
        rotation: -(ac.heading * Math.PI) / 180,
        alignedAxis: Cartesian3.UNIT_Z,
        distanceDisplayCondition: new DistanceDisplayCondition(0, 5e7),
      },
      label: ac.callsign ? {
        text: ac.callsign,
        font: '11px monospace',
        fillColor: color,
        outlineColor: Color.BLACK,
        outlineWidth: 2,
        style: LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cartesian2(12, -4),
        scaleByDistance: new NearFarScalar(1e4, 1.0, 5e6, 0.0),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 2e6),
        verticalOrigin: VerticalOrigin.CENTER,
        horizontalOrigin: HorizontalOrigin.LEFT,
      } : undefined,
      polyline: {
        positions: buildTrailPositions(ac),
        width: 1,
        material: color.withAlpha(0.4),
      },
      properties: {
        layerType: 'aircraft',
        entityId: ac.icao24,
        rawData: ac,
        geoPosition: ac.position,
      } as any,
    });
  }
}
