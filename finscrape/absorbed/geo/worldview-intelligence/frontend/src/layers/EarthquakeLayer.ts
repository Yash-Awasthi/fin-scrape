import {
  Viewer, CustomDataSource, Cartesian3, Cartesian2, Color,
  NearFarScalar, DistanceDisplayCondition, LabelStyle,
  VerticalOrigin, HorizontalOrigin,
} from 'cesium';
import { ENTITY_ICONS } from '../services/icons';
import type { Earthquake } from '../types';

const DS_NAME = 'earthquake-layer';

let lastData: Earthquake[] = [];
let dataSource: CustomDataSource | null = null;

function magnitudeToColor(mag: number): Color {
  if (mag < 3.0) return Color.YELLOW;
  if (mag < 5.0) return Color.ORANGE;
  return Color.RED;
}

export function updateEarthquakeLayer(viewer: Viewer, data: Earthquake[], visible: boolean): void {
  if (!dataSource) {
    dataSource = new CustomDataSource(DS_NAME);
    viewer.dataSources.add(dataSource);
  }

  dataSource.show = visible;

  if (data === lastData) return;
  lastData = data;

  dataSource.entities.removeAll();

  for (const eq of data) {
    const color = magnitudeToColor(eq.magnitude);
    const { lng, lat } = eq.position;
    const iconSize = Math.max(16, eq.magnitude * 4);

    dataSource.entities.add({
      id: `earthquake-${eq.id}`,
      position: Cartesian3.fromDegrees(lng, lat, 0),
      name: `M${eq.magnitude} - ${eq.place}`,
      billboard: {
        image: eq.magnitude >= 5.0 ? ENTITY_ICONS.earthquake_major : ENTITY_ICONS.earthquake,
        width: iconSize,
        height: iconSize,
        scaleByDistance: new NearFarScalar(1e4, 1.2, 1e7, 0.3),
      },
      label: {
        text: `M${eq.magnitude.toFixed(1)}`,
        font: '10px monospace',
        fillColor: color,
        outlineColor: Color.BLACK,
        outlineWidth: 2,
        style: LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cartesian2(12, -6),
        scaleByDistance: new NearFarScalar(1e4, 1.0, 5e6, 0.0),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 5e6),
        verticalOrigin: VerticalOrigin.CENTER,
        horizontalOrigin: HorizontalOrigin.LEFT,
      },
      properties: {
        layerType: 'earthquakes',
        entityId: eq.id,
        rawData: eq,
        geoPosition: eq.position,
      } as any,
    });
  }
}
