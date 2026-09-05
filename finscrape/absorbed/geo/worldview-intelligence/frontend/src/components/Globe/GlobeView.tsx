import { useRef, useEffect } from 'react';
import {
  Viewer,
  Cartesian2,
  Cartesian3,
  Color,
  Ion,
  PostProcessStage,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
  defined,
  Entity,
} from 'cesium';
import { useAppStore } from '../../stores/appStore';
import { setGlobeViewer } from '../../services/globe';
import { updateAircraftLayer } from '../../layers/AircraftLayer';
import { updateSatelliteLayer } from '../../layers/SatelliteLayer';
import { updateShipLayer } from '../../layers/ShipLayer';
import { updateEarthquakeLayer } from '../../layers/EarthquakeLayer';
import { updateConflictLayer } from '../../layers/ConflictLayer';
import { updateMissileLayer } from '../../layers/MissileLayer';
import { updateNewsLayer } from '../../layers/NewsLayer';
import { updateTrafficLayer } from '../../layers/TrafficLayer';
import { updateWeatherLayer } from '../../layers/WeatherLayer';
import type { VisualMode, SelectedEntity } from '../../types';

Ion.defaultAccessToken = import.meta.env.VITE_CESIUM_ION_TOKEN ?? '';

const NIGHT_VISION_FRAGMENT = `
  uniform sampler2D colorTexture;
  in vec2 v_textureCoordinates;
  void main() {
    vec4 color = texture(colorTexture, v_textureCoordinates);
    float luminance = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    out_FragColor = vec4(0.0, luminance * 1.5, 0.0, color.a);
  }
`;

const THERMAL_FRAGMENT = `
  uniform sampler2D colorTexture;
  in vec2 v_textureCoordinates;
  void main() {
    vec4 color = texture(colorTexture, v_textureCoordinates);
    float luminance = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    vec3 warm = mix(vec3(0.0, 0.0, 0.4), vec3(1.0, 0.2, 0.0), luminance);
    warm = mix(warm, vec3(1.0, 1.0, 0.0), smoothstep(0.7, 1.0, luminance));
    out_FragColor = vec4(warm, color.a);
  }
`;

const RADAR_FRAGMENT = `
  uniform sampler2D colorTexture;
  uniform float time;
  in vec2 v_textureCoordinates;
  void main() {
    vec4 color = texture(colorTexture, v_textureCoordinates);
    float luminance = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    float scanLine = smoothstep(0.0, 0.02, abs(fract(v_textureCoordinates.y * 300.0 + time * 0.5) - 0.5));
    vec3 radarColor = vec3(0.0, luminance * 0.8, 0.0) * scanLine;
    radarColor += vec3(0.0, 0.05, 0.0);
    out_FragColor = vec4(radarColor, color.a);
  }
`;

function applyVisualMode(viewer: Viewer, mode: VisualMode) {
  const stages = viewer.scene.postProcessStages;
  stages.removeAll();

  const baseLayer = viewer.imageryLayers.get(0);
  if (baseLayer) {
    baseLayer.brightness = 1.0;
    baseLayer.contrast = 1.0;
    baseLayer.saturation = 1.0;
  }

  switch (mode) {
    case 'nightVision':
      stages.add(new PostProcessStage({ fragmentShader: NIGHT_VISION_FRAGMENT }));
      break;
    case 'thermal':
      stages.add(new PostProcessStage({ fragmentShader: THERMAL_FRAGMENT }));
      break;
    case 'radar':
      stages.add(new PostProcessStage({
        fragmentShader: RADAR_FRAGMENT,
        uniforms: { time: () => performance.now() / 1000.0 },
      }));
      break;
    case 'tactical':
      if (baseLayer) {
        baseLayer.brightness = 0.3;
        baseLayer.contrast = 1.4;
        baseLayer.saturation = 0.0;
      }
      break;
    case 'satellite':
    default:
      break;
  }
}

export function GlobeView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const handlerRef = useRef<ScreenSpaceEventHandler | null>(null);

  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;

    const viewer = new Viewer(containerRef.current, {
      animation: false,
      baseLayerPicker: false,
      fullscreenButton: false,
      homeButton: false,
      timeline: false,
      navigationHelpButton: false,
      sceneModePicker: false,
      geocoder: false,
      infoBox: false,
      selectionIndicator: false,
      scene3DOnly: true,
    });

    viewerRef.current = viewer;
    setGlobeViewer(viewer);

    if (viewer.scene.skyAtmosphere) {
      viewer.scene.skyAtmosphere.brightnessShift = -0.4;
      viewer.scene.skyAtmosphere.saturationShift = -0.2;
    }
    viewer.scene.globe.enableLighting = true;
    viewer.scene.backgroundColor = Color.BLACK;
    if (viewer.scene.moon) viewer.scene.moon.show = true;
    if (viewer.scene.sun) viewer.scene.sun.show = true;

    viewer.camera.flyTo({
      destination: Cartesian3.fromDegrees(30, 20, 20_000_000),
      duration: 0,
    });

    const mode = useAppStore.getState().visualMode;
    applyVisualMode(viewer, mode);

    const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);
    handlerRef.current = handler;

    handler.setInputAction(
      (event: { position: { x: number; y: number } }) => {
        const picked = viewer.scene.pick(new Cartesian2(event.position.x, event.position.y));
        if (defined(picked) && picked.id instanceof Entity) {
          const entity = picked.id;
          const props = entity.properties;
          if (props) {
            const sel: SelectedEntity = {
              type: props.layerType?.getValue(viewer.clock.currentTime) ?? 'aircraft',
              id: props.entityId?.getValue(viewer.clock.currentTime) ?? entity.name ?? '',
              data: props.rawData?.getValue(viewer.clock.currentTime),
              position: props.geoPosition?.getValue(viewer.clock.currentTime) ?? { lat: 0, lng: 0 },
            };
            useAppStore.getState().setSelectedEntity(sel);
          }
        } else {
          useAppStore.getState().setSelectedEntity(null);
        }
      },
      ScreenSpaceEventType.LEFT_CLICK
    );

    let prevLayers = useAppStore.getState().layers;
    let prevVis = useAppStore.getState().layerVisibility;

    function syncLayers() {
      const v = viewerRef.current;
      if (!v || v.isDestroyed()) return;
      const state = useAppStore.getState();
      updateAircraftLayer(v, state.layers.aircraft, state.layerVisibility.aircraft);
      updateSatelliteLayer(v, state.layers.satellites, state.layerVisibility.satellites);
      updateShipLayer(v, state.layers.ships, state.layerVisibility.ships);
      updateEarthquakeLayer(v, state.layers.earthquakes, state.layerVisibility.earthquakes);
      updateConflictLayer(v, state.layers.conflicts, state.layerVisibility.conflicts);
      updateMissileLayer(v, state.layers.missiles, state.layerVisibility.missiles);
      updateNewsLayer(v, state.layers.news, state.layerVisibility.news);
      updateTrafficLayer(v, state.layers.traffic, state.layerVisibility.traffic);
      updateWeatherLayer(v, state.layers.weather, state.layerVisibility.weather);
    }

    const unsubLayers = useAppStore.subscribe((state) => {
      if (state.layers !== prevLayers || state.layerVisibility !== prevVis) {
        prevLayers = state.layers;
        prevVis = state.layerVisibility;
        syncLayers();
      }
    });

    const initialSync = setTimeout(syncLayers, 100);

    return () => {
      clearTimeout(initialSync);
      unsubLayers();
      handler.destroy();
      setGlobeViewer(null);
      if (!viewer.isDestroyed()) viewer.destroy();
      viewerRef.current = null;
    };
  }, []);

  useEffect(() => {
    let prevMode = useAppStore.getState().visualMode;
    const unsub = useAppStore.subscribe((state) => {
      if (state.visualMode !== prevMode) {
        prevMode = state.visualMode;
        if (viewerRef.current && !viewerRef.current.isDestroyed()) {
          applyVisualMode(viewerRef.current, state.visualMode);
        }
      }
    });
    return unsub;
  }, []);

  return (
    <div
      ref={containerRef}
      style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
    />
  );
}
