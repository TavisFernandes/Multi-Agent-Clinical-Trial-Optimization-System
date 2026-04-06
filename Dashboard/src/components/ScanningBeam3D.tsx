import { useMotionValue } from "framer-motion";
import { animate } from "framer-motion";
import { useFrame } from "@react-three/fiber";
import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * 3D scanning beam: Framer Motion animates a motion value; R3F `useFrame` applies it to a mesh.
 * This is the requested Framer Motion ↔ Three.js bridge (beam passes through the scene over the robot).
 */
export function ScanningBeam3D({ active }: { active: boolean }) {
  const mesh = useRef<THREE.Mesh>(null);
  const z = useMotionValue(-14);

  useEffect(() => {
    if (!active) {
      z.set(-14);
      return;
    }
    const ctrl = animate(z, [12, -12], {
      duration: 2.2,
      ease: "easeInOut",
    });
    return () => ctrl.stop();
  }, [active, z]);

  useFrame(() => {
    if (mesh.current) {
      mesh.current.position.z = z.get();
    }
  });

  if (!active) return null;

  return (
    <mesh ref={mesh} rotation={[0, Math.PI, 0]}>
      <planeGeometry args={[16, 10]} />
      <meshBasicMaterial
        color="#2dd4bf"
        transparent
        opacity={0.16}
        side={THREE.DoubleSide}
        depthWrite={false}
      />
    </mesh>
  );
}
