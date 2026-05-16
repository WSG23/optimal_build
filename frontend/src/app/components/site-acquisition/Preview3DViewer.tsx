import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type MutableRefObject,
} from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import {
  buildPreviewFallbackMassing,
  type PreviewFallbackMassingInput,
  type PreviewFallbackMassingSpec,
} from './previewFallbackMassing'

interface Preview3DViewerProps {
  previewUrl: string | null
  metadataUrl?: string | null
  status: string
  thumbnailUrl?: string | null
  layerVisibility?: Record<string, boolean>
  focusLayerId?: string | null
  fallbackMassing?: PreviewFallbackMassingInput | null
}

type PreviewMetadata = {
  camera_orbit_hint?: Record<string, number>
  cameraOrbitHint?: Record<string, number>
}

type NormalizedPreviewStatus =
  | 'queued'
  | 'processing'
  | 'ready'
  | 'failed'
  | 'placeholder'
  | 'unknown'

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
  fallbackMassing = null,
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
  const normalizedStatus = normalizePreviewStatus(status)
  const fallbackMassingSpec = useMemo(
    () => buildPreviewFallbackMassing(fallbackMassing),
    [fallbackMassing],
  )

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
                  setMetadataWarning(
                    err instanceof Error
                      ? err.message
                      : 'Unable to load preview metadata.',
                  )
                }
                return null
              })
          : Promise.resolve(null)

        const loader = new GLTFLoader()
        const [metadata, gltf] = await Promise.all([
          metadataPromise,
          loader.loadAsync(previewUrl),
        ])
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
        scene.background = new THREE.Color(
          getComputedStyle(document.documentElement)
            .getPropertyValue('--ob-color-bg-surface')
            .trim() || '#f5f5f7',
        )
        sceneRef.current = scene

        const camera = new THREE.PerspectiveCamera(
          45,
          width / height,
          0.1,
          5000,
        )
        const renderer = new THREE.WebGLRenderer({
          antialias: true,
          alpha: true,
        })
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
              if (
                typeof material.opacity !== 'number' ||
                material.opacity === 1
              ) {
                material.opacity = 0.94
              }
            }
            const layerId =
              (typeof child.userData?.layer_id === 'string' &&
                child.userData.layer_id) ||
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
        updateMeshVisibility(
          layerObjectsRef.current,
          layerVisibilityRef.current,
        )
        updateMeshHighlight(
          layerObjectsRef.current,
          focusLayerIdRef.current ?? null,
        )

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
            color: 'var(--ob-color-border-subtle, #e5e7eb)',
            roughness: 0.9,
            metalness: 0.05,
          }),
        )
        ground.rotation.x = -Math.PI / 2
        ground.position.set(center.x, bounds.min.y - 0.05, center.z)
        ground.receiveShadow = true
        scene.add(ground)

        const orbitHint =
          metadata?.camera_orbit_hint ?? metadata?.cameraOrbitHint ?? {}
        const radius =
          typeof orbitHint.radius === 'number' && orbitHint.radius > 0
            ? orbitHint.radius
            : Math.max(size.x, size.y, size.z) * 1.6 || 40
        const theta =
          ((typeof orbitHint.theta === 'number' ? orbitHint.theta : 45) *
            Math.PI) /
          180
        const phi =
          ((typeof orbitHint.phi === 'number' ? orbitHint.phi : 45) * Math.PI) /
          180
        const target = new THREE.Vector3(
          typeof orbitHint.target_x === 'number'
            ? orbitHint.target_x
            : center.x,
          typeof orbitHint.target_z === 'number'
            ? orbitHint.target_z
            : center.y,
          typeof orbitHint.target_y === 'number'
            ? orbitHint.target_y
            : center.z,
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
    if (previewUrl || !fallbackMassingSpec) {
      return undefined
    }

    const container = containerRef.current
    if (!container) {
      return undefined
    }

    setIsLoading(false)
    setError(null)
    setMetadataWarning(null)

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

    try {
      const cleanup = renderFallbackMassingScene({
        container,
        fallbackMassingSpec,
        rendererRef,
        sceneRef,
        cameraRef,
        controlsRef,
        animationRef,
        defaultCameraStateRef,
        layerObjectsRef,
        layerVisibility,
      })
      return cleanup
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to render envelope starter model.',
      )
      return undefined
    }
  }, [fallbackMassingSpec, layerVisibility, previewUrl])

  useEffect(() => {
    updateMeshVisibility(layerObjectsRef.current, layerVisibility)
    // Re-render scene after visibility changes
    if (rendererRef.current && sceneRef.current && cameraRef.current) {
      rendererRef.current.render(sceneRef.current, cameraRef.current)
    }
  }, [layerVisibility])

  useEffect(() => {
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

  if (!previewUrl && !fallbackMassingSpec) {
    const statusState = getPreviewStatusState(normalizedStatus)

    return (
      <div
        className="site-acquisition__preview-viewer-empty"
        data-testid="preview-viewer-empty"
      >
        <div className="site-acquisition__preview-viewer-state">
          <span
            className={`ob-status-dot ${statusState.dotClassName}`}
            aria-hidden="true"
          />
          <div className="site-acquisition__preview-viewer-copy">
            <p className="site-acquisition__preview-viewer-eyebrow">
              Starter model
            </p>
            <p className="site-acquisition__preview-viewer-title">
              {statusState.title}
            </p>
            <p className="site-acquisition__preview-viewer-body">
              {statusState.body}
            </p>
          </div>
        </div>
        {thumbnailUrl ? (
          <div className="site-acquisition__preview-viewer-thumb">
            <span className="site-acquisition__preview-viewer-thumb-label">
              Latest thumbnail
            </span>
            <img
              src={thumbnailUrl}
              alt="Starter model thumbnail"
              loading="lazy"
              decoding="async"
              className="site-acquisition__preview-viewer-thumb-image"
            />
          </div>
        ) : null}
      </div>
    )
  }

  return (
    <div className="site-acquisition__preview-viewer-shell">
      <div
        ref={containerRef}
        className="site-acquisition__preview-viewer-canvas"
        style={{ height: `${FALLBACK_HEIGHT}px` }}
      />
      {!previewUrl && fallbackMassingSpec && !error && (
        <p className="site-acquisition__preview-viewer-note">
          Envelope starter model from resolved zoning and parcel controls.
        </p>
      )}
      {isLoading && (
        <p className="site-acquisition__preview-viewer-note">
          Loading starter model assets…
        </p>
      )}
      {metadataWarning && !error && (
        <p className="site-acquisition__preview-viewer-note site-acquisition__preview-viewer-note--warning">
          {metadataWarning}
        </p>
      )}
      {error && (
        <p className="site-acquisition__preview-viewer-note site-acquisition__preview-viewer-note--error">
          Failed to load starter model: {error}
        </p>
      )}
      {!error && !isLoading && thumbnailUrl && (
        <div className="site-acquisition__preview-viewer-thumb">
          <span className="site-acquisition__preview-viewer-thumb-label">
            Thumbnail
          </span>
          <img
            src={thumbnailUrl}
            alt="Preview thumbnail"
            loading="lazy"
            decoding="async"
            className="site-acquisition__preview-viewer-thumb-image"
          />
        </div>
      )}
    </div>
  )
}

function renderFallbackMassingScene({
  container,
  fallbackMassingSpec,
  rendererRef,
  sceneRef,
  cameraRef,
  controlsRef,
  animationRef,
  defaultCameraStateRef,
  layerObjectsRef,
  layerVisibility,
}: {
  container: HTMLDivElement
  fallbackMassingSpec: PreviewFallbackMassingSpec
  rendererRef: MutableRefObject<THREE.WebGLRenderer | null>
  sceneRef: MutableRefObject<THREE.Scene | null>
  cameraRef: MutableRefObject<THREE.PerspectiveCamera | null>
  controlsRef: MutableRefObject<OrbitControls | null>
  animationRef: MutableRefObject<number | null>
  defaultCameraStateRef: MutableRefObject<{
    position: THREE.Vector3
    target: THREE.Vector3
  } | null>
  layerObjectsRef: MutableRefObject<LayerObjectMap>
  layerVisibility?: Record<string, boolean>
}) {
  const width = container.clientWidth || 640
  const height = container.clientHeight || FALLBACK_HEIGHT
  const scene = new THREE.Scene()
  scene.background = new THREE.Color('#0f1115')
  sceneRef.current = scene

  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 5000)
  cameraRef.current = camera

  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
  })
  renderer.shadowMap.enabled = true
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(width, height)
  rendererRef.current = renderer
  container.appendChild(renderer.domElement)

  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controlsRef.current = controls

  const ambient = new THREE.AmbientLight(0xffffff, 0.82)
  scene.add(ambient)

  const directional = new THREE.DirectionalLight(0xffffff, 0.92)
  directional.position.set(120, 220, 160)
  directional.castShadow = true
  scene.add(directional)

  const root = new THREE.Group()
  root.name = 'envelope_fallback_massing'
  layerObjectsRef.current = new Map()

  fallbackMassingSpec.layers.forEach((layer) => {
    const geometry = new THREE.BoxGeometry(
      layer.widthM,
      layer.heightM,
      layer.depthM,
    )
    const material = new THREE.MeshStandardMaterial({
      color: layer.color,
      roughness: 0.62,
      metalness: 0.04,
      transparent: true,
      opacity: 0.92,
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.name = layer.id
    mesh.userData = { layer_id: layer.id, label: layer.label }
    mesh.position.set(0, layer.yOffsetM + layer.heightM / 2, 0)
    mesh.castShadow = true
    mesh.receiveShadow = true
    root.add(mesh)
    layerObjectsRef.current.set(layer.id, [mesh])
  })

  scene.add(root)
  updateMeshVisibility(layerObjectsRef.current, layerVisibility)

  const groundSpan =
    Math.max(
      fallbackMassingSpec.footprintWidthM,
      fallbackMassingSpec.footprintDepthM,
      20,
    ) * 1.75
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(groundSpan, groundSpan),
    new THREE.MeshStandardMaterial({
      color: '#1f2937',
      roughness: 0.95,
      metalness: 0.02,
    }),
  )
  ground.rotation.x = -Math.PI / 2
  ground.position.y = -0.05
  ground.receiveShadow = true
  scene.add(ground)

  const bounds = new THREE.Box3().setFromObject(root)
  const size = bounds.getSize(new THREE.Vector3())
  const center = bounds.getCenter(new THREE.Vector3())
  const radius = Math.max(size.x, size.y, size.z, 30) * 1.55
  const target = new THREE.Vector3(center.x, center.y * 0.65, center.z)
  camera.position.set(
    target.x + radius,
    target.y + radius * 0.8,
    target.z + radius,
  )
  camera.lookAt(target)
  controls.target.copy(target)
  controls.update()
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
    const newWidth = container.clientWidth || width
    const newHeight = container.clientHeight || height
    camera.aspect = newWidth / newHeight
    camera.updateProjectionMatrix()
    renderer.setSize(newWidth, newHeight)
  }

  window.addEventListener('resize', handleResize)

  return () => {
    window.removeEventListener('resize', handleResize)
    if (animationRef.current !== null) {
      cancelAnimationFrame(animationRef.current)
      animationRef.current = null
    }
    controls.dispose()
    renderer.dispose()
    disposeScene(scene)
    sceneRef.current = null
    rendererRef.current = null
    controlsRef.current = null
    layerObjectsRef.current = new Map()
  }
}

function normalizePreviewStatus(status: string): NormalizedPreviewStatus {
  switch (status.trim().toLowerCase()) {
    case 'queued':
      return 'queued'
    case 'processing':
      return 'processing'
    case 'ready':
      return 'ready'
    case 'failed':
      return 'failed'
    case 'placeholder':
      return 'placeholder'
    default:
      return 'unknown'
  }
}

function getPreviewStatusState(status: NormalizedPreviewStatus): {
  title: string
  body: string
  dotClassName: string
} {
  switch (status) {
    case 'queued':
      return {
        title: 'Starter model queued',
        body: 'Capture has queued a scenario-specific starter model and will show it here when the assets are ready.',
        dotClassName: 'ob-status-dot--warning',
      }
    case 'processing':
      return {
        title: 'Generating starter model',
        body: 'Capture is generating the starter model now. This placeholder will switch to the 3D model when processing completes.',
        dotClassName: 'ob-status-dot--live',
      }
    case 'failed':
      return {
        title: 'Starter model unavailable',
        body: 'The last starter-model generation attempt failed. Retry the generation action to request a new model for this scenario.',
        dotClassName: 'ob-status-dot--error',
      }
    case 'ready':
      return {
        title: 'Starter model syncing',
        body: 'Capture marked this starter model ready, but the 3D asset is not available in the viewer yet. Refresh to sync the latest model.',
        dotClassName: 'ob-status-dot--warning',
      }
    case 'placeholder':
      return {
        title: 'Fallback preview only',
        body: 'Capture is still working from parcel-level scalar controls. A full scenario-specific starter model has not been generated yet.',
        dotClassName: 'ob-status-dot--inactive',
      }
    case 'unknown':
    default:
      return {
        title: 'Starter model pending',
        body: 'Capture has not provided a starter model for this scenario yet.',
        dotClassName: 'ob-status-dot--inactive',
      }
  }
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
            material.opacity = isFocus
              ? baseOpacity
              : Math.min(baseOpacity * 0.35, 0.5)
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
