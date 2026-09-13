import React, { useEffect, useRef } from 'react';
// @ts-ignore
import { Renderer, Program, Mesh, Triangle } from 'ogl';

export interface WavesProps {
  lineColor?: string;
  backgroundColor?: string;
  waveSpeedX?: number;
  waveSpeedY?: number;
  waveAmpX?: number;
  waveAmpY?: number;
  xGap?: number;
  yGap?: number;
}

export default function Waves({
  lineColor = 'rgba(99, 102, 241, 0.35)',
  backgroundColor = 'transparent',
  waveSpeedX = 0.0125,
  waveSpeedY = 0.005,
  waveAmpX = 32,
  waveAmpY = 16,
  xGap = 12,
  yGap = 32,
}: WavesProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const renderer = new Renderer({ alpha: true, dpr: Math.min(window.devicePixelRatio, 2) });
    const gl = renderer.gl;
    container.appendChild(gl.canvas);

    const vertex = `
      attribute vec2 position;
      void main() {
        gl_Position = vec4(position, 0.0, 1.0);
      }
    `;

    const fragment = `
      precision highp float;
      uniform vec2 uResolution;
      uniform float uTime;
      uniform vec4 uLineColor;

      void main() {
        vec2 uv = gl_FragCoord.xy / uResolution.xy;
        float wave = sin(uv.x * 10.0 + uTime * 2.0) * 0.05 + cos(uv.x * 20.0 - uTime) * 0.02;
        float dist = abs(uv.y - 0.5 - wave);
        float alpha = smoothstep(0.02, 0.0, dist) * uLineColor.a;
        gl_FragColor = vec4(uLineColor.rgb, alpha);
      }
    `;

    const geometry = new Triangle(gl);
    const program = new Program(gl, {
      vertex,
      fragment,
      uniforms: {
        uTime: { value: 0 },
        uResolution: { value: new Float32Array([container.clientWidth || window.innerWidth, container.clientHeight || window.innerHeight]) },
        uLineColor: { value: [0.388, 0.4, 0.945, 0.4] }, // Indigo tint
      },
      transparent: true,
    });

    const mesh = new Mesh(gl, { geometry, program });

    function resize() {
      if (!container) return;
      const width = container.clientWidth || window.innerWidth;
      const height = container.clientHeight || window.innerHeight;
      renderer.setSize(width, height);
      program.uniforms.uResolution.value[0] = width;
      program.uniforms.uResolution.value[1] = height;
    }

    window.addEventListener('resize', resize);
    resize();

    let animationId: number;
    let t = 0;
    function update() {
      t += 0.015;
      program.uniforms.uTime.value = t;
      renderer.render({ scene: mesh });
      animationId = requestAnimationFrame(update);
    }
    update();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', resize);
      if (gl.canvas && container.contains(gl.canvas)) {
        container.removeChild(gl.canvas);
      }
    };
  }, [lineColor, backgroundColor, waveSpeedX, waveSpeedY, waveAmpX, waveAmpY, xGap, yGap]);

  return <div ref={containerRef} className="absolute inset-0 pointer-events-none w-full h-full overflow-hidden" />;
}

export { Waves };
