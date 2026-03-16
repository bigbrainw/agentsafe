"use client";

import { useEffect, useState } from "react";

const SPOT_RADIUS = 500;

export function CursorBackground() {
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY });
    };

    const handleMouseLeave = () => setPosition(null);

    window.addEventListener("mousemove", handleMouseMove);
    document.documentElement.addEventListener("mouseleave", handleMouseLeave);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      document.documentElement.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  if (!position) return null;

  return (
    <div
      className="pointer-events-none fixed z-0"
      aria-hidden
      style={{
        left: position.x - SPOT_RADIUS,
        top: position.y - SPOT_RADIUS,
        width: SPOT_RADIUS * 2,
        height: SPOT_RADIUS * 2,
      }}
    >
      <div
        className="h-full w-full rounded-full"
        style={{
          background: `radial-gradient(
            circle at center,
            rgba(139, 92, 246, 0.2) 0%,
            rgba(139, 92, 246, 0.06) 40%,
            transparent 70%
          )`,
        }}
      />
    </div>
  );
}
