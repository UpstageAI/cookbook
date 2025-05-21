const API_BASE_URL = "http://127.0.0.1:8000"

export interface UploadResponse {
  success: boolean
  message: string
  documentId?: string
  content?: string
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  try {
    const formData = new FormData()
    formData.append("file", file)

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error("Error uploading document:", error)
    throw error
  }
} 