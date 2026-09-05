import {
  Viewer, CustomDataSource, Cartesian3, Cartesian2, Color,
  NearFarScalar, DistanceDisplayCondition, LabelStyle,
  VerticalOrigin, HorizontalOrigin,
} from 'cesium';
import { ENTITY_ICONS } from '../services/icons';
import type { WeatherData } from '../types';

const DS_NAME = 'weather-layer';

let lastData: WeatherData[] = [];
let dataSource: CustomDataSource | null = null;

function temperatureColor(temp: number): Color {
  if (temp < 0) return Color.BLUE;
  if (temp < 10) return Color.CYAN;
  if (temp < 20) return Color.GREEN;
  if (temp < 30) return Color.YELLOW;
  return Color.RED;
}

export function updateWeatherLayer(viewer: Viewer, data: WeatherData[], visible: boolean): void {
  if (!dataSource) {
    dataSource = new CustomDataSource(DS_NAME);
    viewer.dataSources.add(dataSource);
  }

  dataSource.show = visible;

  if (data === lastData) return;
  lastData = data;

  dataSource.entities.removeAll();

  for (let i = 0; i < data.length; i++) {
    const wd = data[i];
    const color = temperatureColor(wd.temperature);
    const { lng, lat } = wd.position;

    dataSource.entities.add({
      id: `weather-${i}-${lng.toFixed(2)}-${lat.toFixed(2)}`,
      position: Cartesian3.fromDegrees(lng, lat, 0),
      name: `${wd.condition} ${wd.temperature}°C`,
      billboard: {
        image: ENTITY_ICONS.weather,
        width: 18,
        height: 18,
        scaleByDistance: new NearFarScalar(1e4, 1.2, 1e7, 0.3),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 5e7),
      },
      label: {
        text: `${wd.condition}\n${wd.temperature.toFixed(0)}°C`,
        font: '10px monospace',
        fillColor: color,
        outlineColor: Color.BLACK,
        outlineWidth: 2,
        style: LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cartesian2(12, -4),
        scaleByDistance: new NearFarScalar(1e4, 1.0, 3e6, 0.0),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 3e6),
        verticalOrigin: VerticalOrigin.CENTER,
        horizontalOrigin: HorizontalOrigin.LEFT,
      },
      properties: {
        layerType: 'weather',
        entityId: `${i}`,
        rawData: wd,
        geoPosition: wd.position,
      } as any,
    });
  }
}
