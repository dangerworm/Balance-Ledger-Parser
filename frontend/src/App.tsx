import React, { useCallback, useState } from 'react'
import {
    API_BASE_URL,
    FullPageResponse,
    PreprocessConfig,
    transcribeFullPage,
    uploadImage,
} from './api'
import Controls from './components/Controls'
import Dropzone from './components/Dropzone'
import ResultPanel from './components/ResultPanel'

const App: React.FC = () => {
  const [imageId, setImageId] = useState<string | null>(null)
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [fullPageResult, setFullPageResult] = useState<FullPageResponse | null>(null)
  const [preprocess, setPreprocess] = useState<PreprocessConfig>({
    grayscale: false,
    binarize: false,
  })
  const [error, setError] = useState<string | null>(null)
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false)

  const handleFileSelected = useCallback(async (file: File) => {
    console.log('File selected:', file.name, 'API_BASE_URL:', API_BASE_URL)
    try {
      const res = await uploadImage(file)
      console.log('Upload successful:', res)
      setImageId(res.image_id)
      setImageUrl(`${API_BASE_URL}/api/image/${res.image_id}`)
      setFullPageResult(null)
      setError(null)
    } catch (err) {
      console.error('Upload error:', err)
      setError(`Upload failed: ${(err as Error).message}`)
      setImageId(null)
      setImageUrl(null)
    }
  }, [])

  const handleTranscribePage = async () => {
    if (!imageId) return
    setIsTranscribing(true)
    try {
      const response = await transcribeFullPage(imageId, preprocess)
      setFullPageResult(response)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setIsTranscribing(false)
    }
  }

  const handleClear = () => {
    setFullPageResult(null)
    setError(null)
  }

  return (
    <div className="app-container">
      <div className="image-panel-container">
        {imageUrl && (
          <div style={{ maxWidth: '100%', maxHeight: '80vh', overflow: 'auto' }}>
            <img src={imageUrl} alt="Uploaded document" style={{ maxWidth: '100%', height: 'auto' }} />
          </div>
        )}
      </div>
      <div className="panel">
        <h2>Ledger HTR Lab</h2>
        <Dropzone onFileSelected={handleFileSelected} />
        <Controls
          hasImage={Boolean(imageId)}
          preprocess={preprocess}
          onPreprocessChange={setPreprocess}
          onTranscribePage={handleTranscribePage}
          onClear={handleClear}
          isTranscribing={isTranscribing}
        />
        <ResultPanel fullPageResult={fullPageResult} error={error} />
      </div>
    </div>
  )
}

export default App
