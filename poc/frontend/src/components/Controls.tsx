import React from 'react'
import { PreprocessConfig } from '../api'

type Props = {
  hasImage: boolean
  preprocess: PreprocessConfig
  onPreprocessChange: (config: PreprocessConfig) => void
  onTranscribePage: () => void
  onClear: () => void
  isTranscribing: boolean
}

const Controls: React.FC<Props> = ({
  hasImage,
  preprocess,
  onPreprocessChange,
  onTranscribePage,
  onClear,
  isTranscribing,
}) => {
  return (
    <div className="controls panel">
      <div className="preprocess-controls">
        <label>Preprocessing</label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.875rem' }}>
          <label>
            <input
              type="checkbox"
              checked={preprocess.grayscale}
              onChange={(e) => onPreprocessChange({ ...preprocess, grayscale: e.target.checked })}
            />
            {' '}Grayscale
          </label>
          <label>
            <input
              type="checkbox"
              checked={preprocess.binarize}
              onChange={(e) => onPreprocessChange({ ...preprocess, binarize: e.target.checked })}
            />
            {' '}Binarize
          </label>
        </div>
      </div>

      <button onClick={onTranscribePage} disabled={!hasImage || isTranscribing} style={{ marginTop: '0.5rem' }}>
        {isTranscribing ? 'Transcribing...' : 'Transcribe Full Page'}
      </button>
      <button onClick={onClear} disabled={!hasImage}>
        Clear results
      </button>
    </div>
  )
}

export default Controls
