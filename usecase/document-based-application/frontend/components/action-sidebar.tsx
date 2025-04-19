"use client"

import type React from "react"
import { useState, useEffect } from "react"
import {
  X,
  CheckSquare,
  FolderSymlink,
  Send,
  BarChart,
  Table,
  ShieldCheck,
  Info,
  Play,
  Clock,
  FileText,
  CalendarClock,
  ClipboardList,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { motion, AnimatePresence } from "framer-motion"
import { Separator } from "@/components/ui/separator"

interface ActionSidebarProps {
  documentType: string | null
  isOpen: boolean
  onClose: () => void
  isPermanent?: boolean
}

interface Action {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  isEnabled: boolean
  tooltipContent: string
}

interface ActionGroup {
  title: string
  actions: Action[]
}

export function ActionSidebar({ documentType, isOpen, onClose, isPermanent = false }: ActionSidebarProps) {
  const [runningAction, setRunningAction] = useState<string | null>(null)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    // Проверяем при монтировании
    checkMobile()
    
    // Добавляем слушатель изменения размера окна
    window.addEventListener('resize', checkMobile)
    
    // Убираем слушатель при размонтировании
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Define which actions are available for each document type
  const getActionAvailability = (actionId: string) => {
    if (!documentType) return false

    switch (actionId) {
      case "generate_action_items":
        return documentType === "meeting_notes" || documentType === "planning"
      case "classify_organize":
        return true // Available for all document types
      case "send_summary":
        return true // Available for all document types
      case "visualize_data":
        return documentType === "financial"
      case "extract_tables":
        return documentType === "financial" || documentType === "planning"
      case "grant_access":
        return documentType === "financial"
      case "create_timeline":
        return documentType === "planning"
      case "summarize":
        return true // Available for all document types
      case "checklist":
        return true // Available for all document types
      default:
        return false
    }
  }

  const handleRunAction = async (actionId: string) => {
    setRunningAction(actionId)

    try {
      if (actionId === "send_summary") {
        const response = await fetch("http://127.0.0.1:8000/send-slack", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
          },
          mode: "cors",
          body: JSON.stringify({
            message: "New document summary has been generated and shared with the team",
          }),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: "Failed to send Slack message" }))
          throw new Error(errorData.detail || "Failed to send Slack message")
        }

        const data = await response.json()
        console.log("Slack message sent:", data)
      } else if (actionId === "checklist") {
        // Call the compare-policy endpoint
        const response = await fetch("http://127.0.0.1:8000/compare-policy", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
          },
          mode: "cors",
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: "Failed to compare policy" }))
          throw new Error(errorData.detail || "Failed to compare policy")
        }

        const data = await response.json()
        console.log("Policy comparison completed:", data)
        
        // Dispatch a custom event to notify the chat interface
        const event = new CustomEvent('policyComparisonComplete', { 
          detail: { 
            formattedResults: data.formatted_results 
          } 
        })
        window.dispatchEvent(event)
      }

      // Simulate other actions running
      setTimeout(() => {
        setRunningAction(null)
      }, 2000)
    } catch (error) {
      console.error("Error running action:", error)
      setRunningAction(null)
    }
  }

  // Define all possible actions grouped by category
  const actionGroups: ActionGroup[] = [
    {
      title: "Analysis",
      actions: [
        {
          id: "summarize",
          title: "Summarize Document",
          description: "Create a concise summary of the key points",
          icon: <FileText className="h-4 w-4" />,
          isEnabled: getActionAvailability("summarize"),
          tooltipContent: "Generate a comprehensive summary of the document's main points and insights.",
        },
        {
          id: "checklist",
          title: "Check Against Internal Policy",
          description: "Generate a checklist and flag deviations from company standards",
          icon: <CheckSquare className="h-4 w-4" />,
          isEnabled: getActionAvailability("checklist"),
          tooltipContent: "Generate a comprehensive summary of the document's main points and insights.",
        },


      ],
    },
    {
      title: "Generation",
      actions: [
        {
          id: "classify_organize",
          title: "Classify & Organize",
          description: "Categorize and file your document",
          icon: <FolderSymlink className="h-4 w-4" />,
          isEnabled: getActionAvailability("classify_organize"),
          tooltipContent:
            "Automatically classify your document and place it in Google Drive storage.",
        },
        {
            id: "extract_tables",
            title: "Extract Tables & Charts",
            description: "Pull structured data from your document",
            icon: <Table className="h-4 w-4" />,
            isEnabled: getActionAvailability("extract_tables"),
            tooltipContent:
              "Identify and extract tables, charts, and structured data from your document for further analysis.",
          },
      ],
    },
    {
      title: "Workflow",
      actions: [
        {
          id: "send_summary",
          title: "Send Summary",
          description: "Share key points via Slack to the team",
          icon: <Send className="h-4 w-4" />,
          isEnabled: getActionAvailability("send_summary"),
          tooltipContent: "Create a concise summary of your document and send it to team members Slack.",
        },
        {
            id: "generate_action_items",
            title: "Extract Action Items",
            description: "Identify tasks from your document, and turn findings into Notion to-do items",
            icon: <ClipboardList className="h-4 w-4" />,
            isEnabled: getActionAvailability("generate_action_items"),
            tooltipContent: "Automatically identify and extract action items, tasks, and to-dos from meeting notes or project documents.",
          },
          {
            id: "setting_calendar_event",
            title: "Set Calendar Event",
            description: "Add renewal/termination dates to Google Calendar",
            icon: <CalendarClock className="h-4 w-4" />,
            isEnabled: getActionAvailability("setting_calendar_event"),
            tooltipContent: "Automatically identify and extract action items, tasks, and to-dos from meeting notes or project documents.",
          },
      ],
    },
  ]

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Mobile overlay - only show when not permanent and on mobile */}
          {!isPermanent && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="md:hidden fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
              onClick={onClose}
            />
          )}

          {/* Sidebar */}
          <motion.div
            initial={isPermanent ? { x: 0 } : { x: "100%" }}
            animate={{ x: 0 }}
            exit={isPermanent ? { x: 0 } : { x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className={`${
              isPermanent ? "relative hidden md:flex" : "fixed md:absolute"
            } top-0 right-0 bottom-0 w-[85vw] md:w-[350px] bg-background border-l border-border/50 shadow-lg z-50 flex flex-col`}
          >
            <div className="border-b border-border/50 p-4 flex justify-between items-center bg-background/80 backdrop-blur-sm">
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-semibold">Available Actions</h2>
                {documentType && (
                  <Badge variant="outline" className="capitalize">
                    {documentType.replace("_", " ")}
                  </Badge>
                )}
              </div>
              {/* Only show close button when not permanent or on mobile */}
              {(!isPermanent || isMobile) && (
                <Button variant="ghost" size="icon" onClick={onClose} className="rounded-full">
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>

            {/* Rest of the sidebar content remains the same */}
            <div className="flex-1 overflow-auto p-6">
              <div className="space-y-8">
                {actionGroups.map((group) => (
                  <div key={group.title} className="space-y-4">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-medium text-muted-foreground">{group.title}</h3>
                      <Separator className="flex-1" />
                    </div>
                    <div className="grid gap-4">
                      {group.actions.map((action) => (
                        <motion.div
                          key={action.id}
                          whileHover={{ y: -2 }}
                          className={`bg-card rounded-xl border border-border/50 shadow-sm overflow-hidden transition-opacity ${
                            action.isEnabled ? "" : "opacity-50"
                          }`}
                        >
                          <div className="p-4">
                            <div className="flex items-center gap-3 mb-2">
                              <div
                                className={`rounded-full p-2 ${
                                  action.isEnabled ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                                }`}
                              >
                                {action.icon}
                              </div>
                              <div className="flex-1">
                                <h4 className="text-base font-medium">{action.title}</h4>
                                <p className="text-xs text-muted-foreground">{action.description}</p>
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 rounded-full"
                                title={action.tooltipContent}
                              >
                                <Info className="h-3.5 w-3.5" />
                              </Button>
                            </div>
                            <Button
                              size="sm"
                              className="w-full rounded-lg gap-1"
                              disabled={!action.isEnabled || runningAction === action.id}
                              onClick={() => handleRunAction(action.id)}
                            >
                              {runningAction === action.id ? (
                                <>Processing...</>
                              ) : (
                                <>
                                  <Play className="h-3 w-3" /> Run
                                </>
                              )}
                            </Button>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
