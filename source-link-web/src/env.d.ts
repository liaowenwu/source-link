/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_BASE_API: string
  readonly VITE_APP_MONITOR_ADMIN: string
  readonly VITE_APP_ENCRYPT: string
  readonly VITE_APP_CLIENT_ID: string
  readonly VITE_APP_RSA_PUBLIC_KEY: string
  readonly VITE_APP_RSA_PRIVATE_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
