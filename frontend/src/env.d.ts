export {}

declare global {
  interface ImportMetaEnv {
    readonly VITE_API_BASE_URL?: string
    readonly VITE_API_BASE?: string
    readonly VITE_API_ROLE?: string
  }
}
