"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { FileUp, Send, FileText, ImageIcon, Bot, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileUploader } from "@/components/file-uploader"

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  attachments?: {
    type: "pdf" | "image"
    name: string
    size: string
  }[]
}

interface ChatPanelProps {
  onDocumentProcessed: (documentType: string) => void
}

export function ChatPanel({ onDocumentProcessed }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm your document assistant. Upload a document, and I'll help you analyze it and suggest actions.",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [isUploading, setIsUploading] = useState(false)
  const [showUploader, setShowUploader] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendMessage = () => {
    if (!input.trim()) return

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")

    // Simulate AI response
    setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I'm analyzing your request. Is there a specific document you'd like me to help with?",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    }, 1000)
  }

  const handleFileUpload = (files: File[]) => {
    setIsUploading(true)
    setShowUploader(false)

    // Simulate file upload and processing
    setTimeout(() => {
      const file = files[0]
      const fileSize = (file.size / 1024).toFixed(0) + " KB"
      const fileType = file.name.endsWith(".pdf") ? "pdf" : "image"

      // Add user message with attachment
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: "user",
        content: "I've uploaded a document for analysis.",
        timestamp: new Date(),
        attachments: [
          {
            type: fileType as "pdf" | "image",
            name: file.name,
            size: fileSize,
          },
        ],
      }

      setMessages((prev) => [...prev, userMessage])
      setIsUploading(false)

      // Simulate AI processing and response
      setTimeout(() => {
        // Determine document type based on filename (in a real app, this would be done by AI)
        let documentType = "unknown"
        if (file.name.toLowerCase().includes("meeting") || file.name.toLowerCase().includes("notes")) {
          documentType = "meeting_notes"
        } else if (file.name.toLowerCase().includes("financial") || file.name.toLowerCase().includes("report")) {
          documentType = "financial"
        } else if (file.name.toLowerCase().includes("project") || file.name.toLowerCase().includes("roadmap")) {
          documentType = "planning"
        }

        // Update parent component with document type
        onDocumentProcessed(documentType)

        // Generate appropriate response based on document type
        let responseContent = ""
        if (documentType === "meeting_notes") {
          responseContent =
            "I've analyzed your meeting notes. I can identify several action items and key decisions. Would you like me to extract the action items or send a summary to your team?"
        } else if (documentType === "financial") {
          responseContent =
            "I've analyzed your financial document. I can extract key financial data, create visualizations, or classify this for your records. What would you like me to do?"
        } else if (documentType === "planning") {
          responseContent =
            "I've analyzed your project planning document. I can help organize tasks, extract deadlines, or create a summary. How would you like to proceed?"
        } else {
          responseContent = "I've analyzed your document. What would you like me to do with it?"
        }

        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: responseContent,
          timestamp: new Date(),
        }

        setMessages((prev) => [...prev, assistantMessage])
      }, 1500)
    }, 2000)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="border-b border-border p-4">
        <h2 className="text-xl font-semibold">Document Assistant</h2>
        <p className="text-sm text-muted-foreground">Upload documents and get AI-powered insights and actions</p>
      </div>

      <ScrollArea className="flex-1 p-4 overflow-auto">
        <div className="space-y-4 pb-2">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`flex max-w-[80%] gap-3 rounded-lg p-4 ${
                  message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {message.role === "assistant" ? <Bot className="h-5 w-5" /> : <User className="h-5 w-5" />}
                </div>
                <div className="space-y-2 overflow-hidden">
                  {message.attachments?.map((attachment, index) => (
                    <div key={index} className="flex items-center gap-2 rounded-md bg-background/20 p-2">
                      {attachment.type === "pdf" ? <FileText className="h-4 w-4" /> : <ImageIcon className="h-4 w-4" />}
                      <div className="flex flex-col overflow-hidden">
                        <span className="text-sm font-medium truncate">{attachment.name}</span>
                        <span className="text-xs opacity-70">{attachment.size}</span>
                      </div>
                    </div>
                  ))}
                  <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                  <div className="text-right text-xs opacity-70">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {showUploader && (
        <div className="border-t border-border p-4">
          <FileUploader onUpload={handleFileUpload} onCancel={() => setShowUploader(false)} isUploading={isUploading} />
        </div>
      )}

      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={() => setShowUploader(!showUploader)} className="shrink-0">
            <FileUp className="h-4 w-4" />
          </Button>
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            className="min-h-10 resize-none"
          />
          <Button onClick={handleSendMessage} disabled={!input.trim()} className="shrink-0">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
