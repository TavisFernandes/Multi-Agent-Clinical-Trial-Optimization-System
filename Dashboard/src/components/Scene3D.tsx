import { Canvas } from "@react-three/fiber";
import { ParticleNetwork } from "./ParticleNetwork";
import { ScanningBeam3D } from "./ScanningBeam3D";

export interface Scene3DProps {
  labels: string[];
  pulse: number;
  scanActive: boolean;
}

export function Scene3D({ labels, pulse, scanActive }: Scene3DProps) {
  return (
    <Canvas
      dpr={[1, 2]}
      gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
      className="h-full w-full"
      onCreated={({ gl }) => gl.setClearColor(0x000000, 0)}
    >
      <ambientLight intensity={0.35} />
      <pointLight position={[8, 10, 12]} intensity={1.1} color="#2dd4bf" />
      <pointLight position={[-10, -6, 4]} intensity={0.35} color="#ffffff" />
      <ParticleNetwork labels={labels} pulse={pulse} />
      <ScanningBeam3D active={scanActive} />
    </Canvas>
  );
}
