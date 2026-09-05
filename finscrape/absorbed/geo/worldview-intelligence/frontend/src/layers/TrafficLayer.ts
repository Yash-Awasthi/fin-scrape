import {
  Viewer, CustomDataSource, Cartesian3, Cartesian2, Color,
  NearFarScalar, DistanceDisplayCondition, LabelStyle,
  VerticalOrigin, HorizontalOrigin,
} from 'cesium';
import { ENTITY_ICONS } from '../services/icons';
import type { TrafficData } from '../types';

const DS_NAME = 'traffic-layer';

let lastData: TrafficData[] = [];
let dataSource: CustomDataSource | null = null;

function congestionColor(level: number): Color {
  if (level < 40) return Color.GREEN;
  if (level < 70) return Color.YELLOW;
  return Color.RED;
}

export function updateTrafficLayer(viewer: Viewer, data: TrafficData[], visible: boolean): void {
  if (!dataSource) {
    dataSource = new CustomDataSource(DS_NAME);
    viewer.dataSources.add(dataSource);
  }

  dataSource.show = visible;

  if (data === lastData) return;
  lastData = data;

  dataSource.entities.removeAll();

  for (const td of data) {
    const color = congestionColor(td.congestionLevel);
    const { lng, lat } = td.position;
    const size = 10 + (td.congestionLevel / 100) * 15;

    dataSource.entities.add({
      id: `traffic-${td.city}`,
      position: Cartesian3.fromDegrees(lng, lat, 0),
      name: td.city,
      billboard: {
        image: ENTITY_ICONS.traffic,
        width: 20,
        height: 20,
        scaleByDistance: new NearFarScalar(1e4, 1.2, 1e7, 0.3),
      },
      label: {
        text: `${td.city} ${td.congestionLevel}%`,
        font: '11px monospace',
        fillColor: color,
        outlineColor: Color.BLACK,
        outlineWidth: 2,
        style: LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cartesian2(0, -20),
        scaleByDistance: new NearFarScalar(1e4, 1.0, 5e6, 0.0),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 5e6),
        verticalOrigin: VerticalOrigin.BOTTOM,
        horizontalOrigin: HorizontalOrigin.CENTER,
      },
      properties: {
        layerType: 'traffic',
        entityId: td.city,
        rawData: td,
        geoPosition: td.position,
      } as any,
    });
  }
}
