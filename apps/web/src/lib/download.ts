export const FILE_EXTENSIONS = {
  csv: '.csv',
  xlsx: '.xlsx',
  pdf: '.pdf',
} as const

export type ExportFormat = keyof typeof FILE_EXTENSIONS

export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}
