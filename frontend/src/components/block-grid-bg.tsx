import { useEffect, useRef } from 'react'

const MINOR = 32
const MAJOR = 128
const SEED = 1337

function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5)
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export function BlockGridBg() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const draw = () => {
      const dpr = window.devicePixelRatio || 1
      const parent = canvas.parentElement
      const w = parent ? parent.clientWidth : window.innerWidth
      const h = parent ? parent.clientHeight : window.innerHeight
      canvas.width = w * dpr
      canvas.height = h * dpr
      canvas.style.width = w + 'px'
      canvas.style.height = h + 'px'
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, w, h)

      const dark = document.documentElement.classList.contains('dark')
      const lineMinor = dark ? 'rgba(255,255,255,0.018)' : 'rgba(0,0,0,0.014)'
      const lineMajor = dark ? 'rgba(255,255,255,0.045)' : 'rgba(0,0,0,0.032)'
      const blockFill = dark ? 'rgba(255,255,255,0.012)' : 'rgba(0,0,0,0.01)'
      const tick = dark ? 'rgba(255,255,255,0.09)' : 'rgba(0,0,0,0.075)'

      const offX = (w % MINOR) / 2
      const offY = (h % MINOR) / 2

      // Procedural highlighted blocks (drawn first so lines draw over them)
      const rand = mulberry32(SEED)
      const cols = Math.ceil(w / MINOR)
      const rows = Math.ceil(h / MINOR)
      ctx.fillStyle = blockFill
      const blockCount = Math.max(6, Math.floor(cols * rows * 0.012))
      for (let i = 0; i < blockCount; i++) {
        const cx = Math.floor(rand() * cols)
        const cy = Math.floor(rand() * rows)
        const x = Math.round(offX + cx * MINOR)
        const y = Math.round(offY + cy * MINOR)
        // 50/50 single-cell vs 2x1 block for variety
        const wide = rand() > 0.55 ? 2 : 1
        ctx.fillRect(x + 1, y + 1, wide * MINOR - 1, MINOR - 1)
      }

      // Minor grid lines
      ctx.strokeStyle = lineMinor
      ctx.lineWidth = 1
      ctx.beginPath()
      for (let x = offX; x <= w + 0.5; x += MINOR) {
        const px = Math.round(x) + 0.5
        ctx.moveTo(px, 0)
        ctx.lineTo(px, h)
      }
      for (let y = offY; y <= h + 0.5; y += MINOR) {
        const py = Math.round(y) + 0.5
        ctx.moveTo(0, py)
        ctx.lineTo(w, py)
      }
      ctx.stroke()

      // Major grid lines
      ctx.strokeStyle = lineMajor
      ctx.beginPath()
      for (let x = offX; x <= w + 0.5; x += MAJOR) {
        const px = Math.round(x) + 0.5
        ctx.moveTo(px, 0)
        ctx.lineTo(px, h)
      }
      for (let y = offY; y <= h + 0.5; y += MAJOR) {
        const py = Math.round(y) + 0.5
        ctx.moveTo(0, py)
        ctx.lineTo(w, py)
      }
      ctx.stroke()

      // Tick marks (drafting crosshairs) at major intersections
      ctx.strokeStyle = tick
      ctx.beginPath()
      for (let x = offX; x <= w + 0.5; x += MAJOR) {
        for (let y = offY; y <= h + 0.5; y += MAJOR) {
          const cx = Math.round(x) + 0.5
          const cy = Math.round(y) + 0.5
          ctx.moveTo(cx - 4, cy)
          ctx.lineTo(cx + 4, cy)
          ctx.moveTo(cx, cy - 4)
          ctx.lineTo(cx, cy + 4)
        }
      }
      ctx.stroke()
    }

    draw()

    const observer = new MutationObserver(draw)
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    window.addEventListener('resize', draw)

    return () => {
      observer.disconnect()
      window.removeEventListener('resize', draw)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 h-full w-full opacity-0 [mask-image:linear-gradient(to_bottom,black_0%,black_30%,transparent_95%)] [-webkit-mask-image:linear-gradient(to_bottom,black_0%,black_30%,transparent_95%)] motion-safe:animate-[fade-in_0.9s_cubic-bezier(0.16,1,0.3,1)_forwards] motion-reduce:opacity-100"
    />
  )
}
