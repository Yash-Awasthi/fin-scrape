"use client";

import { useRef } from "react";
import { Sphere, useTexture } from "@react-three/drei";
import * as THREE from "three";

export default function Globe() {
  const meshRef = useRef<THREE.Mesh>(null);
  const [colorMap, bumpMap] = useTexture([
    "/earth-night.jpg",
    "/earth-topology.png",
  ]);

  return (
    <group>
      {/* Main globe with texture */}
      <Sphere ref={meshRef} args={[2, 128, 128]}>
        <meshStandardMaterial
          map={colorMap}
          bumpMap={bumpMap}
          bumpScale={0.03}
          roughness={0.7}
          metalness={0.1}
        />
      </Sphere>

      {/* Atmosphere glow - inner */}
      <Sphere args={[2.02, 64, 64]}>
        <meshBasicMaterial
          color="#1a6aaa"
          transparent
          opacity={0.04}
          side={THREE.FrontSide}
        />
      </Sphere>

      {/* Atmosphere glow - outer */}
      <Sphere args={[2.15, 64, 64]}>
        <shaderMaterial
          transparent
          side={THREE.BackSide}
          uniforms={{
            glowColor: { value: new THREE.Color("#0a4a8a") },
          }}
          vertexShader={`
            varying vec3 vNormal;
            void main() {
              vNormal = normalize(normalMatrix * normal);
              gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
          `}
          fragmentShader={`
            varying vec3 vNormal;
            uniform vec3 glowColor;
            void main() {
              float intensity = pow(0.6 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 3.0);
              gl_FragColor = vec4(glowColor, intensity * 0.4);
            }
          `}
        />
      </Sphere>
    </group>
  );
}
