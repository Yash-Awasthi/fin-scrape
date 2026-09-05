"use client";

import { useRef, useMemo, useCallback } from "react";
import { useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";
import { useNewsStore } from "@/lib/newsStore";
import { CATEGORY_COLORS, NewsArticle } from "@/lib/types";

function latLngToVector3(lat: number, lng: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

function Dot({
  article,
  position,
  color,
}: {
  article: NewsArticle;
  position: THREE.Vector3;
  color: string;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const { hoveredArticle, setHoveredArticle } = useNewsStore();
  const isHovered = hoveredArticle?.id === article.id;

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const scale = 1 + Math.sin(clock.elapsedTime * 2 + position.x * 10) * 0.2;
    meshRef.current.scale.setScalar(isHovered ? 2 : scale);
  });

  const handleClick = useCallback(() => {
    window.open(article.url, "_blank");
  }, [article.url]);

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onClick={handleClick}
        onPointerOver={() => setHoveredArticle(article)}
        onPointerOut={() => setHoveredArticle(null)}
      >
        <sphereGeometry args={[0.03, 8, 8]} />
        <meshBasicMaterial color={color} />
      </mesh>

      {/* Glow */}
      <mesh>
        <sphereGeometry args={[0.06, 8, 8]} />
        <meshBasicMaterial color={color} transparent opacity={0.15} />
      </mesh>

      {isHovered && (
        <Html distanceFactor={8} style={{ pointerEvents: "none" }}>
          <div className="bg-black/90 border border-white/20 rounded-lg p-3 max-w-[250px] backdrop-blur-sm">
            <p className="text-white text-xs font-semibold leading-tight">
              {article.title}
            </p>
            <p className="text-gray-400 text-[10px] mt-1">{article.source}</p>
          </div>
        </Html>
      )}
    </group>
  );
}

export default function GlobeDots() {
  const { filteredArticles } = useNewsStore();

  const dots = useMemo(
    () =>
      filteredArticles.slice(0, 100).map((article) => ({
        article,
        position: latLngToVector3(article.lat, article.lng, 2.05),
        color: CATEGORY_COLORS[article.category] || "#ffffff",
      })),
    [filteredArticles]
  );

  return (
    <group>
      {dots.map((dot) => (
        <Dot key={dot.article.id} {...dot} />
      ))}
    </group>
  );
}
