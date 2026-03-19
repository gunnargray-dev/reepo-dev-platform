import { useEffect, useRef } from 'react'

const DOT_SPACING = 32

export function NetworkBg() {
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
      const alpha = dark ? 0.12 : 0.08
      const color = dark ? `rgba(255,255,255,${alpha})` : `rgba(0,0,0,${alpha})`

      const cols = Math.ceil(w / DOT_SPACING) + 1
      const rows = Math.ceil(h / DOT_SPACING) + 1
      const offsetX = (w % DOT_SPACING) / 2
      const offsetY = (h % DOT_SPACING) / 2

      ctx.fillStyle = color
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const x = Math.round(offsetX + c * DOT_SPACING)
          const y = Math.round(offsetY + r * DOT_SPACING)
          ctx.fillRect(x, y, 1, 1)
        }
      }
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
      className="absolute inset-0 h-full w-full"
    />
  )
}
