import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

interface Preview3DViewerProps {
  previewUrl: string | null
  metadataUrl?: string | null
  status: string
  thumbnailUrl?: string | null
  layerVisibility?: Record<string, boolean>
  focusLayerId?: string | null
}

type PreviewMetadata = {
  camera_orbit_hint?: Record<string, number>
  cameraOrbitHint?: Record<string, number>
}

const FALLBACK_HEIGHT = 420
type LayerObjectMap = Map<string, THREE.Object3D[]>

function disposeScene(root: THREE.Object3D | null) {
  if (!root) {
    return
  }
  root.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.geometry?.dispose()
      if (Array.isArray(child.material)) {
        child.material.forEach((mat) => mat.dispose())
      } else if (child.material) {
        child.material.dispose()
      }
    }
  })
}

export function Preview3DViewer({
  previewUrl,
  metadataUrl,
  status,
  thumbnailUrl,
  layerVisibility,
  focusLayerId = null,
}: Preview3DViewerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const animationRef = useRef<number | null>(null)
  const controlsRef = useRef<OrbitControls | null>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const defaultCameraStateRef = useRef<{
    position: THREE.Vector3
    target: THREE.Vector3
  } | null>(null)
  const layerObjectsRef = useRef<LayerObjectMap>(new Map())
  const layerVisibilityRef = useRef<Record<string, boolean> | undefined>()
  const focusLayerIdRef = useRef<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [metadataWarning, setMetadataWarning] = useState<string | null>(null)

  layerVisibilityRef.current = layerVisibility
  focusLayerIdRef.current = focusLayerId

  useEffect(() => {
    if (!previewUrl) {
      return undefined
    }

    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setError(null)
      setMetadataWarning(null)

      try {
        const metadataPromise: Promise<PreviewMetadata | null> = metadataUrl
          ? fetch(metadataUrl, { cache: 'reload' })
              .then((response) => {
                if (!response.ok) {
                  throw new Error(`Metadata fetch failed (${response.status})`)
                }
                return response.json() as Promise<PreviewMetadata>
              })
              .catch((err) => {
                if (!cancelled) {
                  setMetadataWarning(err instanceof Error ? err.message : 'Unable to load preview metadata.')
                }
                return null
              })
          : Promise.resolve(null)

        const loader = new GLTFLoader()
        const [metadata, gltf] = await Promise.all([metadataPromise, loader.loadAsync(previewUrl)])
        if (cancelled) {
          return
        }

        const container = containerRef.current
        if (!container) {
          return
        }

        if (animationRef.current !== null) {
          cancelAnimationFrame(animationRef.current)
          animationRef.current = null
        }
        if (controlsRef.current) {
          controlsRef.current.dispose()
          controlsRef.current = null
        }
        if (rendererRef.current) {
          rendererRef.current.dispose()
          rendererRef.current = null
        }
        if (sceneRef.current) {
          disposeScene(sceneRef.current)
          sceneRef.current = null
        }
        container.innerHTML = ''

        const width = container.clientWidth || 640
        const height = container.clientHeight || FALLBACK_HEIGHT

        layerObjectsRef.current = new Map()

        const scene = new THREE.Scene()
        scene.background = new THREE.Color('#f5f5f7')
        sceneRef.current = scene

        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 5000)
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
        renderer.shadowMap.enabled = true
        renderer.setPixelRatio(window.devicePixelRatio)
        renderer.setSize(width, height)
        rendererRef.current = renderer
        container.appendChild(renderer.domElement)

        const controls = new OrbitControls(camera, renderer.domElement)
        controls.enableDamping = true
        controls.dampingFactor = 0.05
        controlsRef.current = controls

        const root = gltf.scene || new THREE.Group()
        root.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.castShadow = true
            child.receiveShadow = true
            const material = child.material
            if (Array.isArray(material)) {
              material.forEach((mat) => {
                mat.transparent = true
                if (typeof mat.opacity !== 'number' || mat.opacity === 1) {
                  mat.opacity = 0.94
                }
              })
            } else if (material) {
              material.transparent = true
              if (typeof material.opacity !== 'number' || material.opacity === 1) {
                material.opacity = 0.94
              }
            }
            const layerId =
              (typeof child.userData?.layer_id === 'string' && child.userData.layer_id) ||
              (typeof child.name === 'string' && child.name.trim()) ||
              null
            if (layerId) {
              const existing = layerObjectsRef.current.get(layerId) ?? []
              existing.push(child)
              layerObjectsRef.current.set(layerId, existing)
            }
          }
        })
        scene.add(root)
        updateMeshVisibility(layerObjectsRef.current, layerVisibilityRef.current)
        updateMeshHighlight(layerObjectsRef.current, focusLayerIdRef.current ?? null)

        const bounds = new THREE.Box3().setFromObject(root)
        const size = bounds.getSize(new THREE.Vector3())
        const center = bounds.getCenter(new THREE.Vector3())

        const ambient = new THREE.AmbientLight(0xffffff, 0.85)
        scene.add(ambient)

        const directional = new THREE.DirectionalLight(0xffffff, 0.9)
        directional.position.set(150, 240, 140)
        directional.castShadow = true
        scene.add(directional)

        const footprintSpan = Math.max(size.x, size.z, 20)
        const ground = new THREE.Mesh(
          new THREE.PlaneGeometry(footprintSpan * 1.6, footprintSpan * 1.6),
          new THREE.MeshStandardMaterial({
            color: '#e5e7eb',
            roughness: 0.9,
            metalness: 0.05,
          }),
        )
        ground.rotation.x = -Math.PI / 2
        ground.position.set(center.x, bounds.min.y - 0.05, center.z)
        ground.receiveShadow = true
        scene.add(ground)

        const orbitHint = metadata?.camera_orbit_hint ?? metadata?.cameraOrbitHint ?? {}
        const radius =
          typeof orbitHint.radius === 'number' && orbitHint.radius > 0
            ? orbitHint.radius
            : Math.max(size.x, size.y, size.z) * 1.6 || 40
        const theta = ((typeof orbitHint.theta === 'number' ? orbitHint.theta : 45) * Math.PI) / 180
        const phi = ((typeof orbitHint.phi === 'number' ? orbitHint.phi : 45) * Math.PI) / 180
        const target = new THREE.Vector3(
          typeof orbitHint.target_x === 'number' ? orbitHint.target_x : center.x,
          typeof orbitHint.target_z === 'number' ? orbitHint.target_z : center.y,
          typeof orbitHint.target_y === 'number' ? orbitHint.target_y : center.z,
        )

        const orbitX = target.x + radius * Math.sin(phi) * Math.cos(theta)
        const orbitY = target.y + radius * Math.cos(phi)
        const orbitZ = target.z + radius * Math.sin(phi) * Math.sin(theta)

        camera.position.set(orbitX, orbitY, orbitZ)
        camera.lookAt(target)
        controls.target.copy(target)
        controls.update()
        cameraRef.current = camera
        defaultCameraStateRef.current = {
          position: camera.position.clone(),
          target: controls.target.clone(),
        }

        const animate = () => {
          animationRef.current = requestAnimationFrame(animate)
          controls.update()
          renderer.render(scene, camera)
        }
        animate()

        const handleResize = () => {
          if (!containerRef.current || !rendererRef.current) {
            return
          }
          const newWidth = containerRef.current.clientWidth || width
          const newHeight = containerRef.current.clientHeight || height
          camera.aspect = newWidth / newHeight
          camera.updateProjectionMatrix()
          rendererRef.current.setSize(newWidth, newHeight)
        }

        window.addEventListener('resize', handleResize)

        return () => {
          window.removeEventListener('resize', handleResize)
          disposeScene(scene)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown preview error')
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    const resizeCleanupPromise = load()

    return () => {
      cancelled = true
      resizeCleanupPromise?.then((cleanup) => {
        if (typeof cleanup === 'function') {
          cleanup()
        }
      })
      if (animationRef.current !== null) {
        cancelAnimationFrame(animationRef.current)
        animationRef.current = null
      }
      if (rendererRef.current) {
        rendererRef.current.dispose()
        rendererRef.current = null
      }
      if (controlsRef.current) {
        controlsRef.current.dispose()
        controlsRef.current = null
      }
      if (sceneRef.current) {
        disposeScene(sceneRef.current)
        sceneRef.current = null
      }
      layerObjectsRef.current = new Map()
    }
  }, [previewUrl, metadataUrl])

  useEffect(() => {
    console.log('[Preview3DViewer] Layer visibility changed:', layerVisibility)
    console.log('[Preview3DViewer] Available layers:', Array.from(layerObjectsRef.current.keys()))
    updateMeshVisibility(layerObjectsRef.current, layerVisibility)
    // Re-render scene after visibility changes
    if (rendererRef.current && sceneRef.current && cameraRef.current) {
      rendererRef.current.render(sceneRef.current, cameraRef.current)
    }
  }, [layerVisibility])

  useEffect(() => {
    console.log('[Preview3DViewer] Focus layer changed:', focusLayerId)
    console.log('[Preview3DViewer] Available layers:', Array.from(layerObjectsRef.current.keys()))
    updateMeshHighlight(layerObjectsRef.current, focusLayerId)
    focusCameraOnLayer(
      focusLayerId,
      layerObjectsRef.current,
      cameraRef.current,
      controlsRef.current,
      defaultCameraStateRef.current,
    )
    // Re-render scene after focus/highlight changes
    if (rendererRef.current && sceneRef.current && cameraRef.current) {
      rendererRef.current.render(sceneRef.current, cameraRef.current)
    }
  }, [focusLayerId])

  if (!previewUrl) {
    return (
      <div
        style={{
          border: '1px dashed #d1d5db',
          borderRadius: '12px',
          padding: '1.5rem',
          textAlign: 'center',
          background: '#f9fafb',
        }}
      >
        <p style={{ margin: 0, fontSize: '0.95rem', color: '#6b7280' }}>
          Preview assets are not ready yet. Status: <strong>{status.toUpperCase()}</strong>
        </p>
      </div>
    )
  }

  return (
    <div
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        padding: '1rem',
        background: '#ffffff',
      }}
    >
      <div
        ref={containerRef}
        style={{ width: '100%', height: `${FALLBACK_HEIGHT}px`, borderRadius: '8px', overflow: 'hidden' }}
      />
      {isLoading && (
        <p style={{ marginTop: '0.75rem', fontSize: '0.9rem', color: '#6b7280' }}>
          Loading preview assets…
        </p>
      )}
      {metadataWarning && !error && (
        <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#b45309' }}>
          {metadataWarning}
        </p>
      )}
      {error && (
        <p style={{ marginTop: '0.75rem', fontSize: '0.9rem', color: '#b91c1c' }}>
          Failed to load preview: {error}
        </p>
      )}
      {!error && !isLoading && thumbnailUrl && (
        <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>Thumbnail:</span>
          <img
            src={thumbnailUrl}
            alt="Preview thumbnail"
            style={{ width: '64px', height: '64px', borderRadius: '8px', objectFit: 'cover' }}
          />
        </div>
      )}
    </div>
  )
}

function updateMeshVisibility(
  map: LayerObjectMap,
  visibility?: Record<string, boolean>,
) {
  if (!map.size) {
    return
  }
  if (!visibility) {
    map.forEach((objects) => {
      objects.forEach((object) => {
        object.visible = true
      })
    })
    return
  }
  map.forEach((objects, layerId) => {
    const isVisible = visibility[layerId] !== false
    objects.forEach((object) => {
      object.visible = isVisible
    })
  })
}

function updateMeshHighlight(map: LayerObjectMap, focusLayerId: string | null) {
  if (!map.size) {
    return
  }
  const hasFocus = Boolean(focusLayerId)
  map.forEach((objects, layerId) => {
    const isFocus = !hasFocus || layerId === focusLayerId
    objects.forEach((object) => {
      object.traverse((node) => {
        if (node instanceof THREE.Mesh) {
          const materials = Array.isArray(node.material)
            ? node.material
            : [node.material]
          materials.forEach((material) => {
            if (!material) {
              return
            }
            const materialWithUserData = material as {
              userData?: { __baseOpacity?: number; [key: string]: unknown }
              opacity?: number
              transparent: boolean
              needsUpdate: boolean
            }
            const baseOpacity =
              materialWithUserData.userData?.__baseOpacity ??
              (typeof materialWithUserData.opacity === 'number'
                ? materialWithUserData.opacity
                : 0.94)
            materialWithUserData.userData = {
              ...materialWithUserData.userData,
              __baseOpacity: baseOpacity,
            }
            material.transparent = true
            material.opacity = isFocus ? baseOpacity : Math.min(baseOpacity * 0.35, 0.5)
            material.needsUpdate = true
          })
        }
      })
    })
  })
}

function focusCameraOnLayer(
  layerId: string | null,
  map: LayerObjectMap,
  camera: THREE.PerspectiveCamera | null,
  controls: OrbitControls | null,
  defaults: { position: THREE.Vector3; target: THREE.Vector3 } | null,
) {
  if (!camera || !controls) {
    return
  }
  if (!layerId) {
    if (defaults) {
      camera.position.copy(defaults.position)
      controls.target.copy(defaults.target)
      controls.update()
    }
    return
  }
  const objects = map.get(layerId)
  if (!objects || objects.length === 0) {
    return
  }
  const box = new THREE.Box3()
  objects.forEach((object) => box.expandByObject(object))
  if (box.isEmpty()) {
    return
  }
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3())
  const radius = Math.max(size.x, size.y, size.z) * 1.6 || 30
  const offset = new THREE.Vector3(radius, radius, radius)
  camera.position.copy(center.clone().add(offset))
  controls.target.copy(center)
  controls.update()
}
