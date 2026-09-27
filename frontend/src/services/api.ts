const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export interface ApiResponse<T = unknown> {
  success: boolean
  data: T
  error?: string
  meta?: Record<string, unknown>
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
  
  const headers = new Headers(options.headers || {})
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}: ${response.statusText}`
      try {
        const errorJson = await response.json()
        errorMessage = errorJson.detail || errorJson.error || errorMessage
      } catch {
        // Fall back to status text
      }
      throw new ApiError(errorMessage, response.status)
    }

    // Check for raw text/patch response
    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('text/plain') || contentType.includes('text/x-diff')) {
      const text = await response.text()
      return text as unknown as T
    }

    return (await response.json()) as T
  } catch (err) {
    if (err instanceof ApiError) throw err
    throw new ApiError(
      err instanceof Error ? err.message : 'Unknown network failure',
      undefined,
      err
    )
  }
}
