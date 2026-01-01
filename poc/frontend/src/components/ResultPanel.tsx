import React from 'react'
import { FullPageResponse } from '../api'

type Props = {
  fullPageResult: FullPageResponse | null
  error: string | null
}

const ResultPanel: React.FC<Props> = ({ fullPageResult, error }) => {
  return (
    <div className="panel">
      <h3>Result</h3>
      {error && <p className="error">{error}</p>}

      {fullPageResult ? (
        <div>
          <p>
            <strong>Elapsed:</strong> {fullPageResult.elapsed_ms}ms
          </p>
          <p>
            <strong>Total Lines:</strong> {fullPageResult.total_lines}
          </p>
          {fullPageResult.preprocess_applied.length > 0 && (
            <p>
              <strong>Preprocessing:</strong> {fullPageResult.preprocess_applied.join(', ')}
            </p>
          )}

          <div style={{ marginTop: '1rem', maxHeight: '400px', overflowY: 'auto' }}>
            <h4>Transcribed Lines</h4>
            {fullPageResult.lines.map((line, idx) => (
              <div key={line.line_id} style={{
                marginBottom: '1rem',
                padding: '0.5rem',
                border: '1px solid #e5e7eb',
                borderRadius: '4px'
              }}>
                <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                  Line {idx + 1} | BBox: x={line.bbox.x} y={line.bbox.y} w={line.bbox.w} h={line.bbox.h}
                  {line.confidence && ` | Confidence: ${line.confidence.toFixed(3)}`}
                </div>
                <div style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                  {line.text || <em>empty</em>}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p>No result yet.</p>
      )}
    </div>
  )
}

export default ResultPanel
