export type UploadResponse = {
  image_id: string
  filename: string
  content_type: string
  width: number
  height: number
}

export type BBox = { x: number; y: number; w: number; h: number }

export type PreprocessConfig = {
  grayscale: boolean
  binarize: boolean
}

export type TranscribedLine = {
  line_id: string
  text: string
  confidence?: number | null
  bbox: BBox
  baseline: [number, number][]
}

export type FullPageResponse = {
  image_id: string
  preprocess_applied: string[]
  lines: TranscribedLine[]
  elapsed_ms: number
  total_lines: number
}

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const API_BASE_URL = BASE_URL

export async function uploadImage(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    throw new Error(`Upload failed: ${res.statusText}`)
  }
  return res.json()
}

export async function transcribeFullPage(
  imageId: string,
  preprocess?: PreprocessConfig
): Promise<FullPageResponse> {
  const res = await fetch(`${BASE_URL}/api/transcribe-page`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_id: imageId,
      preprocess: preprocess || undefined,
    }),
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || 'Full page transcription failed')
  }
  return res.json()
}
