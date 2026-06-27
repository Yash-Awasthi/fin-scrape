// Thin globe.gl wrapper: plot events by lat/lon, colored by verdict, click → select.

import Globe, { type GlobeInstance } from "globe.gl";
import type { EventOut } from "../api";
import { type GlobePoint, toPoints } from "./points";

export class GlobeView {
  private globe: GlobeInstance;

  constructor(container: HTMLElement, onSelect: (e: EventOut) => void) {
    this.globe = new Globe(container)
      .globeImageUrl("//unpkg.com/three-globe/example/img/earth-dark.jpg")
      .backgroundColor("#0b0e14")
      .pointLat("lat")
      .pointLng("lng")
      .pointColor("color")
      .pointAltitude("size")
      .pointRadius(0.4)
      .pointLabel("label")
      .onPointClick((p: object) => onSelect((p as GlobePoint).event));

    const controls = this.globe.controls() as { autoRotate: boolean; autoRotateSpeed: number };
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.4;
  }

  setEvents(events: EventOut[]): void {
    this.globe.pointsData(toPoints(events));
  }

  resize(w: number, h: number): void {
    this.globe.width(w).height(h);
  }
}
