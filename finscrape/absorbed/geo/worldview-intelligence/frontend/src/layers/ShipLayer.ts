import {
  Viewer, CustomDataSource, Cartesian3, Cartesian2, Color,
  NearFarScalar, DistanceDisplayCondition, LabelStyle,
  VerticalOrigin, HorizontalOrigin,
} from 'cesium';
import { ENTITY_ICONS } from '../services/icons';
import type { Ship } from '../types';

const SHIP_COLOR: Record<Ship['shipType'], Color> = {
  cargo: Color.STEELBLUE,
  tanker: Color.GOLD,
  passenger: Color.WHITE,
  naval: Color.RED,
  fishing: Color.GREEN,
  unknown: Color.GRAY,
};

const DS_NAME = 'ship-layer';

let lastData: Ship[] = [];
let dataSource: CustomDataSource | null = null;

export function updateShipLayer(viewer: Viewer, data: Ship[], visible: boolean): void {
  if (!dataSource) {
    dataSource = new CustomDataSource(DS_NAME);
    viewer.dataSources.add(dataSource);
  }

  dataSource.show = visible;

  if (data === lastData) return;
  lastData = data;

  dataSource.entities.removeAll();

  for (const ship of data) {
    const color = SHIP_COLOR[ship.shipType] ?? Color.GRAY;
    const { lng, lat } = ship.position;

    dataSource.entities.add({
      id: `ship-${ship.mmsi}`,
      position: Cartesian3.fromDegrees(lng, lat, 0),
      name: ship.name || ship.mmsi,
      billboard: {
        image: ship.shipType === 'naval' ? ENTITY_ICONS.ship_naval
          : ship.shipType === 'tanker' ? ENTITY_ICONS.ship_tanker
          : ENTITY_ICONS.ship,
        width: 20,
        height: 20,
        scaleByDistance: new NearFarScalar(1e4, 1.2, 1e7, 0.3),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 5e7),
      },
      label: {
        text: ship.name || ship.mmsi,
        font: '10px monospace',
        fillColor: color,
        outlineColor: Color.BLACK,
        outlineWidth: 2,
        style: LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cartesian2(12, -4),
        scaleByDistance: new NearFarScalar(1e4, 1.0, 3e6, 0.0),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 2e6),
        verticalOrigin: VerticalOrigin.CENTER,
        horizontalOrigin: HorizontalOrigin.LEFT,
      },
      properties: {
        layerType: 'ships',
        entityId: ship.mmsi,
        rawData: ship,
        geoPosition: ship.position,
      } as any,
    });
  }
}
