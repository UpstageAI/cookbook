export interface ChatMessage {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  timestamp: Date
  attachments?: {
    type: "pdf" | "image"
    name: string
    size: string
  }[]
  suggestion?: {
    text: string
    action: string
  }
} 