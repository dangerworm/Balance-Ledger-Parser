import React, { useCallback, useMemo, useState } from 'react'
import Dropzone from './components/Dropzone'
import ImageAnnotator from './components/ImageAnnotator'
import Controls from './components/Controls'
import ResultPanel from './components/ResultPanel'
import { API_BASE_URL, BBox, HtrResponse, runHtr, uploadImage } from './api'

type Size = { width: number; height: number }

const App: React.FC = () => {
  const [imageId, setImageId] = useState<string | null>(null)
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [naturalSize, setNaturalSize] = useState<Size | null>(null)
  const [displaySize, setDisplaySize] = useState<Size | null>(null)
  const [selectionDisplay, setSelectionDisplay] = useState<BBox | null>(null)
  const [selectionImage, setSelectionImage] = useState<BBox | null>(null)
  const [result, setResult] = useState<HtrResponse | null>(null)
  const [engine, setEngine] = useState<string>('dummy')
  const [error, setError] = useState<string | null>(null)

  const handleFileSelected = useCallback(async (file: File) => {
    try {
      const res = await uploadImage(file)
      setImageId(res.image_id)
      setImageUrl(`${API_BASE_URL}/api/image/${res.image_id}`)
      setNaturalSize({ width: res.width, height: res.height })
      setSelectionDisplay(null)
      setSelectionImage(null)
      setResult(null)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [])

  const convertSelection = useCallback(
    (selection: BBox | null, natural: Size | null, display: Size | null) => {
      if (!selection || !natural || !display) return null
      const scaleX = natural.width / display.width
      const scaleY = natural.height / display.height
      return {
        x: Math.round(selection.x * scaleX),
        y: Math.round(selection.y * scaleY),
        w: Math.round(selection.w * scaleX),
        h: Math.round(selection.h * scaleY),
      }
    },
    [],
  )

  const handleSelectionChange = (bbox: BBox | null) => {
    setSelectionDisplay(bbox)
    setSelectionImage(convertSelection(bbox, naturalSize, displaySize))
  }

  const handleRun = async () => {
    if (!imageId || !selectionImage) return
    try {
      const response = await runHtr(imageId, selectionImage, engine)
      setResult(response)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleClear = () => {
    setSelectionDisplay(null)
    setSelectionImage(null)
    setResult(null)
    setError(null)
  }

  const handleDisplaySizeChange = (size: Size) => {
    setDisplaySize(size)
    if (selectionDisplay) {
      setSelectionImage(convertSelection(selectionDisplay, naturalSize, size))
    }
  }

  const selectionInfo = useMemo(() => selectionImage ?? selectionDisplay, [selectionDisplay, selectionImage])

  return (
    <div className="app-container">
      <ImageAnnotator
        imageUrl={imageUrl ?? undefined}
        naturalSize={naturalSize ?? undefined}
        selection={selectionDisplay}
        onSelectionDisplayChange={handleSelectionChange}
        onDisplaySizeChange={handleDisplaySizeChange}
      />
      <div className="panel">
        <h2>Ledger HTR Lab</h2>
        <Dropzone onFileSelected={handleFileSelected} />
        <Controls
          hasImage={Boolean(imageId)}
          selection={selectionDisplay}
          engine={engine}
          onEngineChange={setEngine}
          onRun={handleRun}
          onClear={handleClear}
        />
        <ResultPanel result={result} bbox={selectionInfo} error={error} />
      </div>
    </div>
  )
}

export default App
