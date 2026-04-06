import { useMemo, useRef } from "react";
import { Line } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

export interface ParticleNetworkProps {
  labels: string[];
  /** 0 = idle edge glow, 1 = strong teal pulse */
  pulse: number;
}

function fibonacciSphere(count: number, radius: number): THREE.Vector3[] {
  const pts: THREE.Vector3[] = [];
  const golden = Math.PI * (3 - Math.sqrt(5));
  const n = Math.max(count, 1);
  for (let i = 0; i < n; i++) {
    const y = 1 - (i / (n - 1 || 1)) * 2;
    const r = Math.sqrt(Math.max(0, 1 - y * y));
    const theta = golden * i;
    const x = Math.cos(theta) * r * radius;
    const z = Math.sin(theta) * r * radius;
    pts.push(new THREE.Vector3(x, y * radius, z));
  }
  return pts;
}

export function ParticleNetwork({ labels, pulse }: ParticleNetworkProps) {
  const group = useRef<THREE.Group>(null);
  const nodes = useMemo(
    () => fibonacciSphere(Math.max(labels.length, 6), 3.35),
    [labels.join("|")],
  );

  const edges = useMemo(() => {
    const e: [number, number][] = [];
    for (let i = 0; i < nodes.length; i++) {
      if (i + 1 < nodes.length) e.push([i, i + 1]);
      if (i + 3 < nodes.length) e.push([i, i + 3]);
    }
    return e;
  }, [nodes]);

  useFrame((_, delta) => {
    if (group.current) {
      group.current.rotation.y += delta * 0.06;
    }
  });

  const edgeOpacity = THREE.MathUtils.lerp(0.12, 0.55, pulse);
  const nodeOpacity = THREE.MathUtils.lerp(0.35, 1, pulse);
  const teal = "#2dd4bf";

  return (
    <group ref={group}>
      {edges.map(([a, b], i) => (
        <Line
          key={`e-${i}`}
          points={[nodes[a], nodes[b]]}
          color={teal}
          lineWidth={pulse > 0.5 ? 2.2 : 1}
          transparent
          opacity={edgeOpacity}
          dashed={false}
        />
      ))}
      {nodes.map((p, i) => (
        <mesh key={`n-${i}`} position={p}>
          <sphereGeometry args={[0.12 + pulse * 0.05, 16, 16]} />
          <meshStandardMaterial
            color={teal}
            emissive={teal}
            emissiveIntensity={0.25 + pulse * 1.1}
            transparent
            opacity={nodeOpacity}
            metalness={0.2}
            roughness={0.35}
          />
        </mesh>
      ))}
    </group>
  );
}
