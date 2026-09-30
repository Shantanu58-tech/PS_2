import { useEffect, useRef } from 'react'
import * as THREE from 'three'

/**
 * Landing hero: a slowly turning globe of posts. Saffron "lamps" sit on the surface and
 * narratives arc between them, drawn out over time like a story spreading. Respects
 * prefers-reduced-motion (renders one still frame) and cleans up on unmount.
 */
export default function Hero3D() {
  const box = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = box.current
    if (!el) return
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    el.appendChild(renderer.domElement)
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100)
    camera.position.set(0, 0, 6.2)
    const globe = new THREE.Group()
    globe.rotation.x = 0.35
    scene.add(globe)

    // dotted sphere (Fibonacci lattice)
    const N = 1600, R = 2
    const pos = new Float32Array(N * 3)
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2, r = Math.sqrt(1 - y * y), th = Math.PI * (3 - Math.sqrt(5)) * i
      pos.set([Math.cos(th) * r * R, y * R, Math.sin(th) * r * R], i * 3)
    }
    const dotsGeo = new THREE.BufferGeometry()
    dotsGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    const dots = new THREE.Points(dotsGeo, new THREE.PointsMaterial({ color: 0xe8dfd5, size: 0.022, transparent: true, opacity: 0.55 }))
    globe.add(dots)

    // faint wire sphere for depth
    const wire = new THREE.Mesh(new THREE.SphereGeometry(R * 0.995, 36, 24),
      new THREE.MeshBasicMaterial({ color: 0xc87d43, wireframe: true, transparent: true, opacity: 0.06 }))
    globe.add(wire)

    // lamps (nodes) + arcs (narratives spreading between them)
    const rnd = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647 })()
    const onSphere = () => {
      const u = rnd() * 2 - 1, t = rnd() * Math.PI * 2, r = Math.sqrt(1 - u * u)
      return new THREE.Vector3(Math.cos(t) * r * R, u * R, Math.sin(t) * r * R)
    }
    const lamps: THREE.Vector3[] = Array.from({ length: 22 }, onSphere)
    const glowTex = (() => {
      const c = document.createElement('canvas'); c.width = c.height = 64
      const g = c.getContext('2d')!, grd = g.createRadialGradient(32, 32, 0, 32, 32, 32)
      grd.addColorStop(0, 'rgba(255,214,150,1)'); grd.addColorStop(0.3, 'rgba(255,153,51,0.8)'); grd.addColorStop(1, 'rgba(255,153,51,0)')
      g.fillStyle = grd; g.fillRect(0, 0, 64, 64)
      return new THREE.CanvasTexture(c)
    })()
    const sprites = lamps.map(p => {
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }))
      s.position.copy(p.clone().multiplyScalar(1.01)); s.scale.setScalar(0.22); globe.add(s); return s
    })
    type Arc = { line: THREE.Line; n: number; t: number; speed: number }
    const arcs: Arc[] = []
    const SEG = 64
    for (let k = 0; k < 16; k++) {
      const a = lamps[Math.floor(rnd() * lamps.length)], b = lamps[Math.floor(rnd() * lamps.length)]
      if (a.distanceTo(b) < 0.8) continue
      const mid = a.clone().add(b).multiplyScalar(0.5).normalize().multiplyScalar(R + 0.35 + a.distanceTo(b) * 0.25)
      const curve = new THREE.QuadraticBezierCurve3(a, mid, b)
      const geo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(SEG))
      const hot = k < 5  // a few coordinated pushes in red, the rest organic copper
      const line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: hot ? 0xe05a4b : 0xd8904f, transparent: true, opacity: hot ? 0.9 : 0.55 }))
      geo.setDrawRange(0, 0)
      globe.add(line)
      arcs.push({ line, n: SEG + 1, t: rnd(), speed: 0.12 + rnd() * 0.18 })
    }

    const resize = () => {
      const w = el.clientWidth, h = el.clientHeight
      renderer.setSize(w, h); camera.aspect = w / Math.max(1, h); camera.updateProjectionMatrix()
    }
    const ro = new ResizeObserver(resize); ro.observe(el); resize()

    let raf = 0, last = performance.now()
    const frame = (now: number) => {
      const dt = Math.min(0.05, (now - last) / 1000); last = now
      globe.rotation.y += dt * 0.08
      for (const a of arcs) {
        a.t = (a.t + dt * a.speed) % 1.6  // draw out, hold, then restart
        a.line.geometry.setDrawRange(0, Math.floor(Math.min(1, a.t) * a.n))
      }
      sprites.forEach((s, i) => s.scale.setScalar(0.18 + 0.06 * Math.sin(now / 600 + i)))
      renderer.render(scene, camera)
      raf = requestAnimationFrame(frame)
    }
    if (reduce) {
      arcs.forEach(a => a.line.geometry.setDrawRange(0, a.n)); renderer.render(scene, camera)
    } else raf = requestAnimationFrame(frame)

    return () => {
      cancelAnimationFrame(raf); ro.disconnect()
      scene.traverse(o => {
        const m = o as THREE.Mesh
        m.geometry?.dispose?.()
        const mat = m.material as THREE.Material | THREE.Material[] | undefined
        if (Array.isArray(mat)) mat.forEach(x => x.dispose()); else mat?.dispose?.()
      })
      glowTex.dispose(); renderer.dispose(); renderer.domElement.remove()
    }
  }, [])

  return <div ref={box} className="hero3d" aria-hidden="true" />
}
