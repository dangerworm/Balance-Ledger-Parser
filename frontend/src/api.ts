export type UploadResponse = {
  image_id: string
  filename: string
  content_type: string
  width: number
  height: number
}

export type BBox = { x: number; y: number; w: number; h: number }

export type HtrResponse = {
  image_id: string
  engine: string
  bbox: BBox
  text: string
  confidence?: number | null
  crop_image_url: string
}

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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

export async function runHtr(imageId: string, bbox: BBox, engine: string): Promise<HtrResponse> {
  const res = await fetch(`${BASE_URL}/api/htr`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_id: imageId, bbox, engine }),
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || 'HTR failed')
  }
  const data: HtrResponse = await res.json()
  if (data.crop_image_url.startsWith('/')) {
    data.crop_image_url = `${BASE_URL}${data.crop_image_url}`
  }
  return data
}

export const API_BASE_URL = BASE_URL
