const DEFAULT_API_BASE_URL =
  'http://127.0.0.1:9950'

export const config = {
  apiBaseUrl:
    import.meta.env.VITE_API_BASE_URL ||
    DEFAULT_API_BASE_URL,
}