"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { FileUp, Send, FileText, ImageIcon, Bot, User, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { FileUploader } from "@/components/file-uploader"
import { motion, AnimatePresence } from "framer-motion"
import { sendChatMessage } from "@/services/chat"
import { uploadDocument } from "@/services/upload"

interface ChatMessage {
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

interface ChatInterfaceProps {
  onDocumentProcessed: (documentType: string) => void
  documentType: string | null
  onToggleActionSidebar: () => void
  showActionSidebar: boolean
}

export function ChatInterface({
  onDocumentProcessed,
  documentType,
  onToggleActionSidebar,
  showActionSidebar,
}: ChatInterfaceProps) {
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
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const [isSending, setIsSending] = useState(false)
  const isSendingRef = useRef(false)
  const [currentDocument, setCurrentDocument] = useState<{ id?: string; content?: string } | null>(null)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [uploadAnnouncement, setUploadAnnouncement] = useState<{ text: string; visible: boolean } | null>(null)

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Listen for policy comparison complete event
  useEffect(() => {
    const handlePolicyComparisonComplete = (event: CustomEvent) => {
      const { formattedResults } = event.detail;
      
      // Add the policy comparison results to the chat
      const policyMessage: ChatMessage = {
        id: `${Date.now()}-policy-comparison`,
        role: "assistant",
        content: formattedResults,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, policyMessage]);
    };
    
    // Add event listener
    window.addEventListener('policyComparisonComplete', handlePolicyComparisonComplete as EventListener);
    
    // Clean up
    return () => {
      window.removeEventListener('policyComparisonComplete', handlePolicyComparisonComplete as EventListener);
    };
  }, []);

  const handleSendMessage = async () => {
    if (!input.trim() || isSendingRef.current) return

    isSendingRef.current = true
    setIsSending(true)
    
    const userMessage: ChatMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    // Show user message immediately
    setMessages(prev => [...prev, userMessage])
    setInput("")

    try {
      // Include document info in the chat request if available
      const chatPayload = {
        messages: [...messages, userMessage],
        documentId: currentDocument?.id,
        documentContent: currentDocument?.content
      }

      // Send messages to backend and get response
      const updatedMessages = await sendChatMessage(chatPayload)
      
      // Update messages with the complete response
      setMessages(updatedMessages)
    } catch (error) {
      console.error("Error sending message:", error)
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: `${Date.now()}-error`,
        role: "assistant",
        content: "Sorry, I encountered an error while processing your message. Please try again.",
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsSending(false)
      isSendingRef.current = false
    }
  }

  
  
  const handleFileUpload = async (files: File[]) => {
    if (!files.length) return
  
    const file = files[0]
    const fileSize = (file.size / 1024).toFixed(0) + " KB"
    const fileType = file.name.endsWith(".pdf") ? "pdf" : "image"
  
    setIsUploading(true)
    setShowUploader(false)
    setUploadSuccess(false)
  
    // Create a message indicating file upload
    const uploadMessage: ChatMessage = {
      id: `${Date.now()}-user-upload`,
      role: "user",
      content: "",
      timestamp: new Date(),
      attachments: [
        {
          type: fileType,
          name: file.name,
          size: fileSize,
        },
      ],
    }
    setMessages((prev) => [...prev, uploadMessage])
  
    try {
      const uploadResponse = await uploadDocument(file)
  
    //   if (!uploadResponse.success || !uploadResponse.documentId) {
    //     throw new Error("Upload failed or documentId missing")
    //   }
  
      setCurrentDocument({
        id: uploadResponse.documentId,
        content: uploadResponse.content,
      })
      setUploadSuccess(true)
  
      // Determine document type
      let docType = "document"
      let suggestion = "Would you like me to summarize this document?"
      let assistantContent = "I've analyzed your document and extracted the key information."
  
      const name = file.name.toLowerCase()
      if (name.includes("meeting") || name.includes("notes")) {
        docType = "meeting_notes"
        suggestion = "Would you like me to extract action items from these meeting notes?"
        assistantContent =
          "I've analyzed your meeting notes and identified action items and decisions discussed."
      } else if (name.includes("financial") || name.includes("report")) {
        docType = "financial"
        suggestion = "Would you like me to visualize the key financial data in this report?"
        assistantContent =
          "I've analyzed your financial report. It includes revenue figures, expenses, and projections."
      } else if (name.includes("project") || name.includes("roadmap")) {
        docType = "planning"
        suggestion = "Would you like me to create a timeline from this project document?"
        assistantContent =
          "I've analyzed your project planning doc with key milestones and launch dates."
      }
  
      onDocumentProcessed(docType)
  
      const systemMessage: ChatMessage = {
        id: `${Date.now()}-system`,
        role: "system",
        content: `${file.name} has been uploaded successfully.`,
        timestamp: new Date(),
      }
  
      const assistantMessage: ChatMessage = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        content: assistantContent,
        timestamp: new Date(),
        suggestion: {
          text: suggestion,
          action: docType === "meeting_notes"
            ? "extract_action_items"
            : docType === "financial"
            ? "visualize_data"
            : docType === "planning"
            ? "create_timeline"
            : "summarize",
        },
      }
  
      setMessages((prev) => [...prev, systemMessage, assistantMessage])
    } catch (err) {
      console.error("Upload error:", err)
      
    //   const errorMessage: ChatMessage = {
    //     id: `${Date.now()}-upload-error`,
    //     role: "assistant",
    //     content: "",
    //     timestamp: new Date(),
    //   }
    //   setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsUploading(false)
      setTimeout(() => setUploadSuccess(false), 2000)
    }
  }
  

  const handleSuggestionAction = async (action: string) => {
    // Add user message accepting the suggestion
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: "Yes, please do that.",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])

    // Simulate AI processing the action
    setTimeout(async () => {
      let responseContent = ""

      switch (action) {
        case "extract_action_items":
          responseContent =
            "I've extracted the following action items from your meeting notes:\n\n1. @John to finalize the Q3 product roadmap by Friday\n2. @Sarah to schedule user testing sessions for the new feature\n3. @Team to review the competitor analysis before next meeting\n4. @Michael to update the project timeline in Jira"
          break
        case "visualize_data":
          responseContent =
            "I've created visualizations based on your financial data. The charts show a 15% increase in revenue compared to last quarter, with marketing expenses decreasing by 8%. Would you like me to send these visualizations to your team?"
          break
        case "create_timeline":
          responseContent =
            "I've created a project timeline based on your planning document. The critical path shows the product launch is scheduled for October 15th, with beta testing beginning on September 1st. Would you like me to export this timeline to your project management tool?"
          break
        case "summarize":
          const response = await fetch("http://127.0.0.1:8000/send-slack?only_summary=true", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({}),
          })
          const data = await response.json()
          responseContent = data.summary
          break
        default:
          responseContent =
            "I've processed your request. Is there anything else you'd like me to do with this document?"
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: responseContent,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    }, 1500)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-background to-background/50">
      <div className="border-b border-border/50 p-4 flex justify-between items-center bg-background/80 backdrop-blur-sm">
        <h2 className="text-xl font-semibold">DocZilla</h2>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" className="text-muted-foreground">
            New Chat
          </Button>
          {/* Add a mobile-only button to toggle the action sidebar */}
          <Button variant="outline" size="sm" className="md:hidden" onClick={onToggleActionSidebar}>
            Actions
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4 md:p-6" ref={chatContainerRef}>
        <div className="max-w-3xl mx-auto space-y-6">
          <AnimatePresence initial={false}>
            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "system" ? (
                  // System announcement style
                  <div className="flex items-center justify-center w-full my-4">
                    <div className="flex items-center gap-2 px-4 py-2 bg-muted/50 rounded-full text-sm text-muted-foreground">
                      <FileText className="h-4 w-4" />
                      <span>{message.content}</span>
                    </div>
                  </div>
                ) : (
                  // Regular message style
                  <div
                    className={`flex max-w-[85%] gap-3 rounded-2xl p-4 ${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    <div className="mt-1 shrink-0">
                      {message.role === "assistant" ? (
                        <div className="rounded-full bg-primary/10 p-1">
                          <Bot className="h-5 w-5 text-primary" />
                        </div>
                      ) : (
                        <div className="rounded-full bg-primary-foreground/20 p-1">
                          <User className="h-5 w-5" />
                        </div>
                      )}
                    </div>
                    <div className="space-y-3 overflow-hidden">
                      {message.attachments?.map((attachment, index) => (
                        <div key={index} className="flex items-center gap-2 rounded-md bg-background/20 p-2">
                          {attachment.type === "pdf" ? (
                            <FileText className="h-4 w-4" />
                          ) : (
                            <ImageIcon className="h-4 w-4" />
                          )}
                          <div className="flex flex-col overflow-hidden">
                            <span className="text-sm font-medium truncate">{attachment.name}</span>
                            <span className="text-xs opacity-70">{attachment.size}</span>
                          </div>
                        </div>
                      ))}
                      <div className="whitespace-pre-wrap text-sm">{message.content}</div>

                      {message.suggestion && (
                        <div className="mt-4 pt-3 border-t border-border/20">
                          <p className="text-sm font-medium mb-3">{message.suggestion.text}</p>
                          <div className="flex flex-wrap gap-2">
                            <Button
                              size="sm"
                              className="rounded-full px-4 shadow-sm"
                              onClick={() => handleSuggestionAction(message.suggestion!.action)}
                            >
                              Yes
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="rounded-full px-4"
                              onClick={onToggleActionSidebar}
                            >
                              More actions <ChevronRight className="ml-1 h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      )}

                      <div className="text-right text-xs opacity-70">
                        {message.timestamp.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
      </div>

      {showUploader && (
        <div className="border-t border-border/50 p-4 bg-background/80 backdrop-blur-sm">
          <FileUploader onUpload={handleFileUpload} onCancel={() => setShowUploader(false)} isUploading={isUploading} />
        </div>
      )}

      <div className="border-t border-border/50 p-4 bg-background/80 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setShowUploader(!showUploader)}
              className={`shrink-0 rounded-full relative ${
                uploadSuccess ? "bg-green-500/10 border-green-500" : ""
              }`}
            >
              <FileUp className={`h-4 w-4 ${uploadSuccess ? "text-green-500" : ""}`} />
              {uploadSuccess && (
                <div className="absolute -top-1 -right-1 bg-green-500 rounded-full p-1">
                  <svg
                    className="h-2 w-2 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              )}
            </Button>
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message..."
              className="min-h-10 resize-none rounded-xl border-muted bg-background"
            />
            <Button onClick={handleSendMessage} disabled={!input.trim()} className="shrink-0 rounded-full">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
