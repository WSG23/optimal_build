export {}

declare global {
  interface ImportMetaEnv {
    readonly VITE_API_BASE_URL?: string
    readonly VITE_API_BASE?: string
    readonly VITE_API_URL?: string
    readonly VITE_API_ROLE?: string
    readonly VITE_ANALYTICS_API_BASE_URL?: string
    readonly VITE_MAPBOX_ACCESS_TOKEN?: string
  }
}
