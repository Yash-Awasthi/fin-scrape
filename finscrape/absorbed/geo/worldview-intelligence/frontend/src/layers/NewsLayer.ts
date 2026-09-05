import {
  Viewer, CustomDataSource, Cartesian3, Cartesian2, Color,
  NearFarScalar, DistanceDisplayCondition, LabelStyle,
  VerticalOrigin, HorizontalOrigin,
} from 'cesium';
import { ENTITY_ICONS } from '../services/icons';
import type { NewsEvent } from '../types';

const CATEGORY_COLOR: Record<NewsEvent['category'], Color> = {
  conflict: Color.RED,
  disaster: Color.ORANGE,
  politics: Color.DODGERBLUE,
  economic: Color.LIME,
  protest: Color.YELLOW,
  technology: Color.CYAN,
};

const DS_NAME = 'news-layer';

let lastData: NewsEvent[] = [];
let dataSource: CustomDataSource | null = null;

function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max - 1) + '…' : text;
}

export function updateNewsLayer(viewer: Viewer, data: NewsEvent[], visible: boolean): void {
  if (!dataSource) {
    dataSource = new CustomDataSource(DS_NAME);
    viewer.dataSources.add(dataSource);
  }

  dataSource.show = visible;

  if (data === lastData) return;
  lastData = data;

  dataSource.entities.removeAll();

  const positioned = data.filter((n) => n.position !== null);

  for (const news of positioned) {
    const color = CATEGORY_COLOR[news.category] ?? Color.WHITE;
    const pos = news.position!;

    dataSource.entities.add({
      id: `news-${news.id}`,
      position: Cartesian3.fromDegrees(pos.lng, pos.lat, 0),
      name: news.title,
      billboard: {
        image: ENTITY_ICONS.news,
        width: 16,
        height: 16,
        scaleByDistance: new NearFarScalar(1e4, 1.2, 1e7, 0.3),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 5e7),
      },
      label: {
        text: truncate(news.title, 30),
        font: '10px monospace',
        fillColor: color,
        outlineColor: Color.BLACK,
        outlineWidth: 2,
        style: LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cartesian2(10, -4),
        scaleByDistance: new NearFarScalar(1e4, 1.0, 3e6, 0.0),
        distanceDisplayCondition: new DistanceDisplayCondition(0, 2e6),
        verticalOrigin: VerticalOrigin.CENTER,
        horizontalOrigin: HorizontalOrigin.LEFT,
      },
      properties: {
        layerType: 'news',
        entityId: news.id,
        rawData: news,
        geoPosition: news.position,
      } as any,
    });
  }
}
