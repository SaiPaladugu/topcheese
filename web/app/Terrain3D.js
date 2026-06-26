"use client";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";
import terrain from "../data/terrain.json";

// A 3D heightfield of his death density — the literal "valley of death".
function DeathMesh() {
  const geo = useMemo(() => {
    const n = terrain.n, size = 10;
    const g = new THREE.PlaneGeometry(size, size, n - 1, n - 1);
    const pos = g.attributes.position;
    const colors = [];
    const c = new THREE.Color();
    for (let i = 0; i < pos.count; i++) {
      const ix = i % n, iy = Math.floor(i / n);
      const h = terrain.h[iy] ? terrain.h[iy][ix] || 0 : 0;
      pos.setZ(i, h * 3.4);
      // dark valleys -> hot red/orange peaks where he dies a lot
      c.setHSL(0.04 + (1 - h) * 0.04, 0.85, 0.12 + h * 0.5);
      colors.push(c.r, c.g, c.b);
    }
    g.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    g.computeVertexNormals();
    return g;
  }, []);
  return (
    <mesh geometry={geo} rotation={[-Math.PI / 2, 0, 0]}>
      <meshStandardMaterial vertexColors side={THREE.DoubleSide} roughness={0.7} metalness={0.1} />
    </mesh>
  );
}

export default function Terrain3D() {
  return (
    <Canvas camera={{ position: [0, 8, 9], fov: 45 }}
      style={{ height: 520, background: "#0f1419", borderRadius: 12 }}>
      <ambientLight intensity={0.55} />
      <directionalLight position={[6, 12, 4]} intensity={1.2} />
      <pointLight position={[-6, 5, -6]} intensity={0.5} color="#f85149" />
      <DeathMesh />
      <OrbitControls autoRotate autoRotateSpeed={0.9} enablePan={false}
        minDistance={6} maxDistance={22} maxPolarAngle={Math.PI / 2.05} />
    </Canvas>
  );
}
