import React from 'react'
import { BBox } from '../api'

type Props = {
  hasImage: boolean
  selection: BBox | null
  engine: string
  onEngineChange: (value: string) => void
  onRun: () => void
  onClear: () => void
}

const Controls: React.FC<Props> = ({ hasImage, selection, engine, onEngineChange, onRun, onClear }) => {
  return (
    <div className="controls panel">
      <div>
        <label htmlFor="engine">Engine</label>
        <select id="engine" value={engine} onChange={(e) => onEngineChange(e.target.value)}>
          <option value="dummy">Dummy</option>
          <option value="tesseract">Tesseract</option>
        </select>
      </div>
      <button onClick={onRun} disabled={!hasImage || !selection}>
        Run HTR
      </button>
      <button onClick={onClear} disabled={!selection}>
        Clear selection
      </button>
    </div>
  )
}

export default Controls
