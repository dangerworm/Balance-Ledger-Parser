import React, { useCallback, useRef, useState } from 'react'
import { BBox } from '../api'

type Size = { width: number; height: number }

type Props = {
  imageUrl?: string
  naturalSize?: Size
  onSelectionDisplayChange: (bbox: BBox | null) => void
  onDisplaySizeChange: (size: Size) => void
  selection?: BBox | null
}

const ImageAnnotator: React.FC<Props> = ({
  imageUrl,
  naturalSize,
  onSelectionDisplayChange,
  onDisplaySizeChange,
  selection,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [isDragging, setDragging] = useState(false)
  const [start, setStart] = useState<{ x: number; y: number } | null>(null)

  const handleMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!imageUrl) return
    const rect = event.currentTarget.getBoundingClientRect()
    const x = event.clientX - rect.left + event.currentTarget.scrollLeft
    const y = event.clientY - rect.top + event.currentTarget.scrollTop
    setStart({ x, y })
    setDragging(true)
  }

  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging || !start) return
    const rect = event.currentTarget.getBoundingClientRect()
    const x = event.clientX - rect.left + event.currentTarget.scrollLeft
    const y = event.clientY - rect.top + event.currentTarget.scrollTop
    const bbox: BBox = {
      x: Math.min(start.x, x),
      y: Math.min(start.y, y),
      w: Math.abs(x - start.x),
      h: Math.abs(y - start.y),
    }
    onSelectionDisplayChange(bbox)
  }

  const handleMouseUp = useCallback(() => {
    setDragging(false)
  }, [])

  const handleImageLoad = (event: React.SyntheticEvent<HTMLImageElement>) => {
    const img = event.currentTarget
    onDisplaySizeChange({ width: img.clientWidth, height: img.clientHeight })
  }

  return (
    <div
      ref={containerRef}
      className="image-area panel"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {imageUrl ? (
        <>
          <img src={imageUrl} alt="Uploaded" onLoad={handleImageLoad} />
          {selection && (
            <div
              className="selection-overlay"
              style={{
                left: selection.x,
                top: selection.y,
                width: selection.w,
                height: selection.h,
              }}
            />
          )}
        </>
      ) : (
        <p>Upload an image to start.</p>
      )}
    </div>
  )
}

export default ImageAnnotator
