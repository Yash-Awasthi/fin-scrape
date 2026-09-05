"use client";

import { useEffect, useRef, useCallback } from "react";
import * as THREE from "three";
import type { GlobePin } from "@/types";

// Ported from ../BlackSwan-Website1/globe.js

const GLOBE_RADIUS = 2.2;
const DRAG_SENSITIVITY = 0.005;
const FRICTION = 0.95;
const MOMENTUM_THRESHOLD = 0.0001;

const PIN_COLORS: Record<string, number> = {
  red: 0xe63946,
  amber: 0xf4a261,
  green: 0x2ecc71,
};

function latLonToVec3(lat: number, lon: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

interface GlobeViewProps {
  pins: GlobePin[];
}

export default function GlobeView({ pins }: GlobeViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<{
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    renderer: THREE.WebGLRenderer;
    globeGroup: THREE.Group;
    animationId: number | null;
  } | null>(null);

  const dragState = useRef({
    isDragging: false,
    previousMouse: { x: 0, y: 0 },
    autoRotate: true,
    momentum: { x: 0, y: 0 },
    lastDelta: { x: 0, y: 0 },
  });

  const initGlobe = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const container = canvas.parentElement!;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    const scene = new THREE.Scene();

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 6.5);

    // Renderer
    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);

    // Globe group
    const globeGroup = new THREE.Group();
    globeGroup.rotation.y = Math.PI / 2;
    scene.add(globeGroup);

    // Dark sphere
    const sphereGeo = new THREE.SphereGeometry(GLOBE_RADIUS, 64, 64);
    const sphereMat = new THREE.MeshBasicMaterial({
      color: 0x111111,
      transparent: true,
      opacity: 0.9,
    });
    globeGroup.add(new THREE.Mesh(sphereGeo, sphereMat));

    // Wireframe
    const wireGeo = new THREE.SphereGeometry(GLOBE_RADIUS + 0.005, 36, 18);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x1a1a1a,
      wireframe: true,
      transparent: true,
      opacity: 0.4,
    });
    globeGroup.add(new THREE.Mesh(wireGeo, wireMat));

    // Atmosphere glow
    const glowGeo = new THREE.SphereGeometry(GLOBE_RADIUS + 0.12, 32, 32);
    const glowMat = new THREE.MeshBasicMaterial({
      color: 0x7cb9e8,
      transparent: true,
      opacity: 0.06,
      side: THREE.BackSide,
    });
    globeGroup.add(new THREE.Mesh(glowGeo, glowMat));

    // Load world borders
    loadWorldBorders(globeGroup);

    // Create pins
    createPins(globeGroup, pins);

    sceneRef.current = { scene, camera, renderer, globeGroup, animationId: null };

    // Mouse controls
    setupMouseControls(canvas);

    // Animation loop
    const animate = () => {
      const state = dragState.current;
      const ref = sceneRef.current;
      if (!ref) return;

      if (!state.isDragging) {
        const speed = Math.sqrt(
          state.momentum.x ** 2 + state.momentum.y ** 2
        );
        if (speed > MOMENTUM_THRESHOLD) {
          ref.globeGroup.rotation.y += state.momentum.x;
          ref.globeGroup.rotation.x += state.momentum.y;
          ref.globeGroup.rotation.x = Math.max(
            -Math.PI / 2,
            Math.min(Math.PI / 2, ref.globeGroup.rotation.x)
          );
          state.momentum.x *= FRICTION;
          state.momentum.y *= FRICTION;
        } else if (!state.autoRotate) {
          state.autoRotate = true;
        }
      }

      if (state.autoRotate && !state.isDragging) {
        ref.globeGroup.rotation.y -= 0.001;
      }

      ref.renderer.render(ref.scene, ref.camera);
      ref.animationId = requestAnimationFrame(animate);
    };

    animate();

    // Resize
    const handleResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (sceneRef.current?.animationId) {
        cancelAnimationFrame(sceneRef.current.animationId);
      }
      renderer.dispose();
    };
  }, [pins]);

  const setupMouseControls = (canvas: HTMLCanvasElement) => {
    const state = dragState.current;

    canvas.style.cursor = "grab";

    const onMouseDown = (e: MouseEvent) => {
      state.isDragging = true;
      state.autoRotate = false;
      canvas.style.cursor = "grabbing";
      state.previousMouse = { x: e.clientX, y: e.clientY };
      e.preventDefault();
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!state.isDragging || !sceneRef.current) return;
      const dx = e.clientX - state.previousMouse.x;
      const dy = e.clientY - state.previousMouse.y;
      sceneRef.current.globeGroup.rotation.y += dx * DRAG_SENSITIVITY;
      sceneRef.current.globeGroup.rotation.x += dy * DRAG_SENSITIVITY;
      sceneRef.current.globeGroup.rotation.x = Math.max(
        -Math.PI / 2,
        Math.min(Math.PI / 2, sceneRef.current.globeGroup.rotation.x)
      );
      state.lastDelta = { x: dx * DRAG_SENSITIVITY, y: dy * DRAG_SENSITIVITY };
      state.previousMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => {
      state.isDragging = false;
      canvas.style.cursor = "grab";
      state.momentum = {
        x: state.lastDelta.x * 0.5,
        y: state.lastDelta.y * 0.5,
      };
      state.autoRotate = false;
    };

    canvas.addEventListener("mousedown", onMouseDown);
    canvas.addEventListener("mousemove", onMouseMove);
    canvas.addEventListener("mouseup", onMouseUp);
    canvas.addEventListener("mouseleave", () => {
      state.isDragging = false;
      canvas.style.cursor = "grab";
      state.autoRotate = true;
    });

    // Touch support
    canvas.addEventListener(
      "touchstart",
      (e) => {
        if (e.touches.length === 1) {
          state.isDragging = true;
          state.autoRotate = false;
          state.previousMouse = {
            x: e.touches[0].clientX,
            y: e.touches[0].clientY,
          };
        }
      },
      { passive: false }
    );

    canvas.addEventListener(
      "touchmove",
      (e) => {
        if (!state.isDragging || !sceneRef.current || e.touches.length !== 1)
          return;
        const dx = e.touches[0].clientX - state.previousMouse.x;
        const dy = e.touches[0].clientY - state.previousMouse.y;
        sceneRef.current.globeGroup.rotation.y += dx * DRAG_SENSITIVITY;
        sceneRef.current.globeGroup.rotation.x += dy * DRAG_SENSITIVITY;
        sceneRef.current.globeGroup.rotation.x = Math.max(
          -Math.PI / 2,
          Math.min(Math.PI / 2, sceneRef.current.globeGroup.rotation.x)
        );
        state.lastDelta = {
          x: dx * DRAG_SENSITIVITY,
          y: dy * DRAG_SENSITIVITY,
        };
        state.previousMouse = {
          x: e.touches[0].clientX,
          y: e.touches[0].clientY,
        };
        e.preventDefault();
      },
      { passive: false }
    );

    canvas.addEventListener("touchend", () => {
      state.isDragging = false;
      state.momentum = {
        x: state.lastDelta.x * 0.5,
        y: state.lastDelta.y * 0.5,
      };
      state.autoRotate = false;
    });
  };

  useEffect(() => {
    const cleanup = initGlobe();
    return () => cleanup?.();
  }, [initGlobe]);

  return (
    <div className="relative w-full h-[calc(100vh-200px)] min-h-[500px]">
      {/* Under construction banner */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-[#1a1a1a] border border-[#F4A261] text-[#F4A261] px-4 py-2 rounded-lg text-sm font-medium">
        Under Construction — Full monitoring with notifications coming soon
      </div>

      <canvas ref={canvasRef} className="w-full h-full" />

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg p-3 space-y-1.5 z-10">
        <div className="text-[10px] uppercase tracking-wider text-[#6B7280] font-semibold mb-1">
          Supplier Risk
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-[#E63946]" />
          <span className="text-xs text-[#8B9098]">High Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-[#F4A261]" />
          <span className="text-xs text-[#8B9098]">Medium Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-[#2ECC71]" />
          <span className="text-xs text-[#8B9098]">Low Risk</span>
        </div>
      </div>
    </div>
  );
}

async function loadWorldBorders(globeGroup: THREE.Group) {
  try {
    const resp = await fetch(
      "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
    );
    const topology = await resp.json();

    // Dynamic import for topojson
    const topojson = await import("topojson-client");
    const countries = topojson.feature(
      topology,
      topology.objects.countries
    ) as unknown as GeoJSON.FeatureCollection;

    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0x505050,
      transparent: true,
      opacity: 0.6,
    });

    countries.features.forEach((feature) => {
      const coords: THREE.Vector3[] = [];
      const processRing = (ring: number[][]) => {
        for (const [lon, lat] of ring) {
          coords.push(latLonToVec3(lat, lon, GLOBE_RADIUS + 0.008));
        }
      };

      const geom = feature.geometry;
      if (geom.type === "Polygon") {
        (geom.coordinates as number[][][]).forEach(processRing);
      } else if (geom.type === "MultiPolygon") {
        (geom.coordinates as number[][][][]).forEach((polygon) =>
          polygon.forEach(processRing)
        );
      }

      if (coords.length > 1) {
        const geo = new THREE.BufferGeometry();
        const positions = new Float32Array(coords.length * 3);
        coords.forEach((v, i) => {
          positions[i * 3] = v.x;
          positions[i * 3 + 1] = v.y;
          positions[i * 3 + 2] = v.z;
        });
        geo.setAttribute(
          "position",
          new THREE.BufferAttribute(positions, 3)
        );
        globeGroup.add(new THREE.Line(geo, lineMaterial));
      }
    });
  } catch (e) {
    console.warn("Could not load world borders:", e);
  }
}

function createPins(globeGroup: THREE.Group, pins: GlobePin[]) {
  pins.forEach((pin, i) => {
    const pos = latLonToVec3(pin.lat, pin.lon, GLOBE_RADIUS + 0.04);
    const color = PIN_COLORS[pin.color] ?? 0x7cb9e8;

    // Pin sphere
    const geo = new THREE.SphereGeometry(0.035, 8, 8);
    const mat = new THREE.MeshBasicMaterial({ color });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(pos);
    mesh.visible = false;
    globeGroup.add(mesh);

    // Glow sprite
    const spriteMat = new THREE.SpriteMaterial({
      color,
      transparent: true,
      opacity: 0,
    });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.position.copy(pos);
    sprite.scale.set(0, 0, 1);
    sprite.visible = false;
    globeGroup.add(sprite);

    // Staggered entry animation
    setTimeout(() => {
      mesh.visible = true;
      sprite.visible = true;

      const startTime = performance.now();
      const duration = 500;

      const animatePin = (t: number) => {
        const elapsed = t - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);

        mesh.scale.setScalar(0.01 + ease * 0.99);
        sprite.scale.set(ease * 0.12, ease * 0.12, 1);
        spriteMat.opacity = ease * 0.5;

        if (progress < 1) requestAnimationFrame(animatePin);
      };

      requestAnimationFrame(animatePin);
    }, 500 + i * 80);
  });
}
