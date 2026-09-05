import {
  Viewer, CustomDataSource, Cartesian3, Cartesian2, Color,
  NearFarScalar, DistanceDisplayCondition, LabelStyle,
  VerticalOrigin, HorizontalOrigin,
} from 'cesium';
import { ENTITY_ICONS } from '../services/icons';
import type { ConflictEvent } from '../types';

const SEVERITY_COLOR: Record<ConflictEvent['severity'], Color> = {
  red: Color.RED,
  orange: Color.ORANGE,
  yellow: Color.YELLOW,
};

const DS_NAME = 'conflict-layer';

let lastData: ConflictEvent[] = [];
let dataSource: CustomDataSource | null = null;

export function updateConflictLayer(viewer: Viewer, data: ConflictEvent[], visible: boolean): void {
  if (!dataSource) {
    dataSource = new CustomDataSource(DS_NAME);
    viewer.dataSources.add(dataSource);
  }

  dataSource.show = visible;

  if (data === lastData) return;
  lastData = data;

  dataSource.entities.removeAll();

  for (const ev of data) {
    const color = SEVERITY_COLOR[ev.severity] ?? Color.YELLOW;
    const { lng, lat } = ev.position;

    const labelText = ev.fatalities > 0
      ? `${ev.fatalities} fatalities`
      : ev.eventType.replace(/_/g, ' ');

    dataSource.entities.add({
      id: `conflict-${ev.id}`,
      position: Cartesian3.fromDegrees(lng, lat, 0),
      name: ev.description,
      billboard: {
        image: (ev.eventType === 'protest' || ev.eventType === 'riot')
          ? ENTITY_ICONS.conflict_protest
          : ENTITY_ICONS.conflict,
        width: 20,
        height: 20,
        scaleByDistance: new NearFarScalar(1e4, 1.2, 1e7, 0.3),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 5e7),
      },
      label: {
        text: labelText,
        font: '10px monospace',
        fillColor: color,
        outlineColor: Color.BLACK,
        outlineWidth: 2,
        style: LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cartesian2(14, -6),
        scaleByDistance: new NearFarScalar(1e4, 1.0, 3e6, 0.0),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 3e6),
        verticalOrigin: VerticalOrigin.CENTER,
        horizontalOrigin: HorizontalOrigin.LEFT,
      },
      properties: {
        layerType: 'conflicts',
        entityId: ev.id,
        rawData: ev,
        geoPosition: ev.position,
      } as any,
    });
  }
}
