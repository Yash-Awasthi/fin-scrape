"use client";

import { useEffect, useRef } from "react";
import { useMap } from "react-map-gl/maplibre";

function getSunPosition(date: Date): { lat: number; lng: number } {
  const dayOfYear = Math.floor(
    (date.getTime() - new Date(date.getFullYear(), 0, 0).getTime()) / 86400000
  );
  const declination =
    -23.44 * Math.cos(((360 / 365) * (dayOfYear + 10) * Math.PI) / 180);
  const hours = date.getUTCHours() + date.getUTCMinutes() / 60;
  const lng = (12 - hours) * 15;
  return { lat: declination, lng };
}

export default function DayNightOverlay() {
  const { current: map } = useMap();
  const initialized = useRef(false);

  useEffect(() => {
    if (!map) return;
    const m = map.getMap();

    const setup = () => {
      if (initialized.current) return;
      initialized.current = true;

      const update = () => {
        const sun = getSunPosition(new Date());
        // Daytime center = sun position, nighttime = opposite
        const dayCenterLng = sun.lng;

        // Create bands radiating outward from the day center with decreasing brightness
        // This brightens the daytime side, leaving the dark basemap as "night"
        const features: GeoJSON.Feature[] = [];

        // Bright core (directly under the sun)
        features.push(band(dayCenterLng, 40, 0.35));
        // Mid day
        features.push(band(dayCenterLng, 60, 0.22));
        // Outer day
        features.push(band(dayCenterLng, 75, 0.12));
        // Twilight
        features.push(band(dayCenterLng, 88, 0.05));

        const fc: GeoJSON.FeatureCollection = {
          type: "FeatureCollection",
          features,
        };

        const src = m.getSource("day-night") as maplibregl.GeoJSONSource | undefined;
        if (src) {
          src.setData(fc);
        } else {
          m.addSource("day-night", { type: "geojson", data: fc });
          m.addLayer(
            {
              id: "day-night-fill",
              type: "fill",
              source: "day-night",
              paint: {
                "fill-color": "#4a8abf",
                "fill-opacity": ["get", "opacity"],
              },
            },
            // Insert below labels but above base
            getFirstLabelLayerId(m)
          );
        }
      };

      update();
      setInterval(update, 60_000);
    };

    if (m.isStyleLoaded()) {
      setup();
    } else {
      m.on("style.load", setup);
    }
  }, [map]);

  return null;
}

function band(centerLng: number, halfWidth: number, opacity: number): GeoJSON.Feature {
  const west = centerLng - halfWidth;
  const east = centerLng + halfWidth;
  return {
    type: "Feature",
    properties: { opacity },
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [west, -85],
          [east, -85],
          [east, 85],
          [west, 85],
          [west, -85],
        ],
      ],
    },
  };
}

function getFirstLabelLayerId(map: maplibregl.Map): string | undefined {
  const layers = map.getStyle()?.layers;
  if (!layers) return undefined;
  for (const layer of layers) {
    if (layer.type === "symbol") return layer.id;
  }
  return undefined;
}
