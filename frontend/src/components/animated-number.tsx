import { useEffect, useRef, useState } from 'react';

interface AnimatedNumberProps {
  value: number | null | undefined;
  duration?: number;
  className?: string;
  style?: React.CSSProperties;
}

export function AnimatedNumber({ value, duration = 800, className, style }: AnimatedNumberProps) {
  const [display, setDisplay] = useState(0);
  const frameRef = useRef(0);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    if (value == null) return;

    const target = value;
    const start = 0;
    startRef.current = null;

    const animate = (timestamp: number) => {
      if (startRef.current === null) startRef.current = timestamp;
      const elapsed = timestamp - startRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(start + (target - start) * eased));

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      }
    };

    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [value, duration]);

  if (value == null) return <span className={className} style={style}>--</span>;

  return <span className={className} style={style}>{display}</span>;
}
