import React, { ChangeEvent } from 'react'

interface Props {
  onFileSelected: (file: File) => void
}

const Dropzone: React.FC<Props> = ({ onFileSelected }) => {
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onFileSelected(file)
    }
  }

  return (
    <div>
      <label htmlFor="file-input">Upload image</label>
      <input id="file-input" type="file" accept="image/*" onChange={handleChange} />
    </div>
  )
}

export default Dropzone
