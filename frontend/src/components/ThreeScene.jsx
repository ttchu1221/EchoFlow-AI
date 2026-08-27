import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Stars } from '@react-three/drei';
import * as THREE from 'three';

/* ── 粒子系统 ──────────────────────────────────── */
function ParticleField({ count = 600 }) {
  const mesh = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);

  const particles = useMemo(() => {
    const arr = [];
    for (let i = 0; i < count; i++) {
      arr.push({
        x: (Math.random() - 0.5) * 30,
        y: (Math.random() - 0.5) * 20,
        z: (Math.random() - 0.5) * 20,
        scale: Math.random() * 0.04 + 0.01,
        speed: Math.random() * 0.3 + 0.1,
        offset: Math.random() * Math.PI * 2,
      });
    }
    return arr;
  }, [count]);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    particles.forEach((p, i) => {
      dummy.position.set(
        p.x + Math.sin(t * p.speed + p.offset) * 0.5,
        p.y + Math.cos(t * p.speed * 0.7 + p.offset) * 0.3,
        p.z + Math.sin(t * p.speed * 0.5 + p.offset) * 0.4
      );
      dummy.scale.setScalar(p.scale * (1 + Math.sin(t * 2 + p.offset) * 0.3));
      dummy.updateMatrix();
      mesh.current.setMatrixAt(i, dummy.matrix);
    });
    mesh.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={mesh} args={[null, null, count]}>
      <sphereGeometry args={[1, 8, 8]} />
      <meshBasicMaterial color="#22d3ee" transparent opacity={0.7} />
    </instancedMesh>
  );
}

/* ── 发光连接线 ────────────────────────────────── */
function GlowingLines() {
  const linesRef = useRef();
  const lineCount = 30;

  const positions = useMemo(() => {
    const arr = new Float32Array(lineCount * 6);
    for (let i = 0; i < lineCount; i++) {
      arr[i * 6] = (Math.random() - 0.5) * 24;
      arr[i * 6 + 1] = (Math.random() - 0.5) * 16;
      arr[i * 6 + 2] = (Math.random() - 0.5) * 16;
      arr[i * 6 + 3] = (Math.random() - 0.5) * 24;
      arr[i * 6 + 4] = (Math.random() - 0.5) * 16;
      arr[i * 6 + 5] = (Math.random() - 0.5) * 16;
    }
    return arr;
  }, []);

  useFrame(({ clock }) => {
    if (!linesRef.current) return;
    const t = clock.getElapsedTime();
    const pos = linesRef.current.geometry.attributes.position.array;
    for (let i = 0; i < lineCount; i++) {
      pos[i * 6 + 1] += Math.sin(t * 0.5 + i) * 0.003;
      pos[i * 6 + 4] += Math.cos(t * 0.5 + i) * 0.003;
    }
    linesRef.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <lineSegments ref={linesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={lineCount * 2}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <lineBasicMaterial color="#22d3ee" transparent opacity={0.15} />
    </lineSegments>
  );
}

/* ── 浮动几何体 ────────────────────────────────── */
function FloatingShape({ geometry, color, position, rotationSpeed = [0.01, 0.015, 0.005], scale = 1 }) {
  const meshRef = useRef();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    meshRef.current.rotation.x = t * rotationSpeed[0];
    meshRef.current.rotation.y = t * rotationSpeed[1];
    meshRef.current.rotation.z = t * rotationSpeed[2];
    meshRef.current.position.y = position[1] + Math.sin(t * 0.5) * 0.3;
  });

  return (
    <Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.5}>
      <mesh ref={meshRef} position={position} scale={scale}>
        {geometry}
        <meshStandardMaterial
          color={color}
          transparent
          opacity={0.6}
          wireframe
          emissive={color}
          emissiveIntensity={0.3}
        />
      </mesh>
    </Float>
  );
}

/* ── 中心核心球体 ──────────────────────────────── */
function CoreSphere() {
  const meshRef = useRef();
  const glowRef = useRef();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    meshRef.current.rotation.y = t * 0.15;
    meshRef.current.rotation.x = Math.sin(t * 0.1) * 0.1;
    const pulse = 1 + Math.sin(t * 1.5) * 0.05;
    glowRef.current.scale.setScalar(pulse * 1.15);
    glowRef.current.material.opacity = 0.08 + Math.sin(t * 2) * 0.03;
  });

  return (
    <group position={[0, 0, 0]}>
      {/* 核心球 */}
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[1.5, 2]} />
        <meshStandardMaterial
          color="#06b6d4"
          transparent
          opacity={0.3}
          wireframe
          emissive="#22d3ee"
          emissiveIntensity={0.5}
        />
      </mesh>
      {/* 外层光晕 */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[2, 32, 32]} />
        <meshBasicMaterial
          color="#22d3ee"
          transparent
          opacity={0.08}
          side={THREE.BackSide}
        />
      </mesh>
      {/* 轨道环 */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[2.5, 0.02, 16, 100]} />
        <meshBasicMaterial color="#22d3ee" transparent opacity={0.3} />
      </mesh>
      <mesh rotation={[Math.PI / 3, Math.PI / 4, 0]}>
        <torusGeometry args={[3, 0.015, 16, 100]} />
        <meshBasicMaterial color="#a78bfa" transparent opacity={0.2} />
      </mesh>
    </group>
  );
}

/* ── 数据点柱状体 ──────────────────────────────── */
function DataPillar({ position, height, color }) {
  const meshRef = useRef();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    meshRef.current.scale.y = 1 + Math.sin(t * 2 + position[0]) * 0.15;
    meshRef.current.material.opacity = 0.4 + Math.sin(t * 1.5 + position[0]) * 0.15;
  });

  return (
    <mesh ref={meshRef} position={[position[0], position[1] + height / 2, position[2]]}>
      <boxGeometry args={[0.15, height, 0.15]} />
      <meshStandardMaterial
        color={color}
        transparent
        opacity={0.5}
        emissive={color}
        emissiveIntensity={0.4}
      />
    </mesh>
  );
}

/* ── 数据柱状阵列 ──────────────────────────────── */
function DataPillarRing() {
  const pillars = useMemo(() => {
    const count = 20;
    const radius = 5;
    return Array.from({ length: count }, (_, i) => {
      const angle = (i / count) * Math.PI * 2;
      return {
        position: [Math.cos(angle) * radius, 0, Math.sin(angle) * radius],
        height: 0.5 + Math.random() * 2,
        color: ['#22d3ee', '#3b82f6', '#a78bfa', '#34d399', '#fbbf24'][i % 5],
      };
    });
  }, []);

  return (
    <group>
      {pillars.map((p, i) => (
        <DataPillar key={i} {...p} />
      ))}
    </group>
  );
}

/* ── 主场景 ────────────────────────────────────── */
export default function ThreeScene({ className = '' }) {
  return (
    <div className={className} style={{ width: '100%', height: '100%' }}>
      <Canvas
        camera={{ position: [0, 3, 10], fov: 50 }}
        gl={{ alpha: true, antialias: true }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={0.5} color="#22d3ee" />
        <pointLight position={[-10, -5, 5]} intensity={0.3} color="#a78bfa" />

        <Stars radius={50} depth={50} count={2000} factor={3} saturation={0} fade speed={1} />

        <CoreSphere />
        <ParticleField count={500} />
        <GlowingLines />
        <DataPillarRing />

        <FloatingShape
          geometry={<octahedronGeometry args={[0.5, 0]} />}
          color="#22d3ee"
          position={[-4, 2, -3]}
          scale={0.8}
          rotationSpeed={[0.02, 0.01, 0.015]}
        />
        <FloatingShape
          geometry={<dodecahedronGeometry args={[0.4, 0]} />}
          color="#a78bfa"
          position={[4, -1, -2]}
          scale={0.9}
          rotationSpeed={[0.015, 0.02, 0.01]}
        />
        <FloatingShape
          geometry={<tetrahedronGeometry args={[0.5, 0]} />}
          color="#34d399"
          position={[-3, -2, 2]}
          scale={0.7}
          rotationSpeed={[0.01, 0.015, 0.02]}
        />
        <FloatingShape
          geometry={<icosahedronGeometry args={[0.35, 0]} />}
          color="#fbbf24"
          position={[3.5, 2.5, 1]}
          scale={0.8}
          rotationSpeed={[0.025, 0.01, 0.015]}
        />
        <FloatingShape
          geometry={<torusGeometry args={[0.4, 0.15, 8, 20]} />}
          color="#f472b6"
          position={[0, 3.5, -4]}
          scale={1}
          rotationSpeed={[0.02, 0.025, 0.01]}
        />
      </Canvas>
    </div>
  );
}
