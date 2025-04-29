"use client"

import { useState } from "react"
import { ChatInterface } from "@/components/chat-interface"
import { ActionSidebar } from "@/components/action-sidebar"

export default function Dashboard() {
  const [documentType, setDocumentType] = useState<string | null>(null)
  // Always show the action sidebar
  const [showActionSidebar, setShowActionSidebar] = useState(true)

  // Function to update document type when a document is processed
  const handleDocumentProcessed = (type: string) => {
    setDocumentType(type)
  }

  const toggleActionSidebar = () => {
    setShowActionSidebar(!showActionSidebar)
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <main className="flex flex-1 flex-col overflow-hidden">
        <div className="flex flex-1 overflow-hidden">
          {/* Chat Interface (full screen minus sidebar width) */}
          <div className="flex-1 transition-all duration-300">
            <ChatInterface
              onDocumentProcessed={handleDocumentProcessed}
              documentType={documentType}
              onToggleActionSidebar={toggleActionSidebar}
              showActionSidebar={showActionSidebar}
            />
          </div>

          {/* Action Sidebar (permanent on desktop, toggleable on mobile) */}
          <ActionSidebar
            documentType={documentType}
            isOpen={showActionSidebar}
            onClose={() => setShowActionSidebar(false)}
            isPermanent={true}
          />
        </div>
      </main>
    </div>
  )
}
