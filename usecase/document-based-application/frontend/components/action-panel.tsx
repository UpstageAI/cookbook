"use client"

import type React from "react"

import { useState } from "react"
import { CheckSquare, FolderSymlink, Send, BarChart, Table, ShieldCheck, Info, Play } from "lucide-react"
import { Card, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Badge } from "@/components/ui/badge"

interface ActionCardProps {
  title: string
  description: string
  icon: React.ReactNode
  isEnabled: boolean
  tooltipContent: string
  onRun: () => void
}

function ActionCard({ title, description, icon, isEnabled, tooltipContent, onRun }: ActionCardProps) {
  return (
    <Card className={`transition-opacity ${isEnabled ? "" : "opacity-50"}`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`rounded-md p-1 ${isEnabled ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}
            >
              {icon}
            </div>
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6">
                  <Info className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs text-sm">{tooltipContent}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <CardDescription className="text-xs">{description}</CardDescription>
      </CardHeader>
      <CardFooter className="pt-2">
        <Button size="sm" className="w-full gap-1" disabled={!isEnabled} onClick={onRun}>
          <Play className="h-3 w-3" /> Run
        </Button>
      </CardFooter>
    </Card>
  )
}

interface ActionPanelProps {
  documentType: string | null
}

export function ActionPanel({ documentType }: ActionPanelProps) {
  const [runningAction, setRunningAction] = useState<string | null>(null)

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
      default:
        return false
    }
  }

  const handleRunAction = (actionId: string) => {
    setRunningAction(actionId)

    // Simulate action running
    setTimeout(() => {
      setRunningAction(null)
    }, 2000)
  }

  // Define all possible actions
  const actions = [
    {
      id: "generate_action_items",
      title: "Generate Action Items",
      description: "Extract tasks and to-dos from your document",
      icon: <CheckSquare className="h-4 w-4" />,
      tooltipContent:
        "Automatically identify and extract action items, tasks, and to-dos from meeting notes or project documents.",
    },
    {
      id: "classify_organize",
      title: "Classify & Organize",
      description: "Categorize and file your document",
      icon: <FolderSymlink className="h-4 w-4" />,
      tooltipContent:
        "Automatically classify your document and suggest where to store it in your file system or cloud storage.",
    },
    {
      id: "send_summary",
      title: "Send Summary",
      description: "Share key points via email or Slack",
      icon: <Send className="h-4 w-4" />,
      tooltipContent: "Create a concise summary of your document and send it to team members via email or Slack.",
    },
    {
      id: "visualize_data",
      title: "Visualize Key Data",
      description: "Create charts from tables and numbers",
      icon: <BarChart className="h-4 w-4" />,
      tooltipContent:
        "Extract numerical data from your document and generate visual charts and graphs for better insights.",
    },
    {
      id: "extract_tables",
      title: "Extract Tables & Charts",
      description: "Pull structured data from your document",
      icon: <Table className="h-4 w-4" />,
      tooltipContent:
        "Identify and extract tables, charts, and structured data from your document for further analysis.",
    },
    {
      id: "grant_access",
      title: "Grant Access",
      description: "Manage permissions for sensitive documents",
      icon: <ShieldCheck className="h-4 w-4" />,
      tooltipContent: "Set up appropriate access controls and permissions for sensitive or confidential documents.",
    },
  ]

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Available Actions</h2>
          {documentType && (
            <Badge variant="outline" className="capitalize">
              {documentType.replace("_", " ")}
            </Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          {documentType ? "Select an action to perform on your document" : "Upload a document to see available actions"}
        </p>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="grid gap-6">
          {actions.map((action) => (
            <ActionCard
              key={action.id}
              title={action.title}
              description={action.description}
              icon={action.icon}
              isEnabled={getActionAvailability(action.id)}
              tooltipContent={action.tooltipContent}
              onRun={() => handleRunAction(action.id)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
