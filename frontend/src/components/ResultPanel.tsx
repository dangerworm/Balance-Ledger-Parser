import React from 'react'
import { BBox, HtrResponse } from '../api'

type Props = {
  result: HtrResponse | null
  bbox: BBox | null
  error: string | null
}

const ResultPanel: React.FC<Props> = ({ result, bbox, error }) => {
  return (
    <div className="panel">
      <h3>Result</h3>
      {error && <p className="error">{error}</p>}
      {result ? (
        <div>
          <p>
            <strong>Engine:</strong> {result.engine}
          </p>
          <div className="result-block">
            {result.text || <em>No text returned</em>}
          </div>
          <p>Confidence: {result.confidence ?? 'N/A'}</p>
          <p>BBox: {JSON.stringify(result.bbox)}</p>
          {result.crop_image_url && (
            <img src={result.crop_image_url} alt="Crop preview" style={{ maxWidth: '100%', marginTop: '0.5rem' }} />
          )}
        </div>
      ) : (
        <p>No result yet.</p>
      )}
      {bbox && !result && <p>Selection: {JSON.stringify(bbox)}</p>}
    </div>
  )
}

export default ResultPanel
