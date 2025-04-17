"use client"

import { useState } from "react"
import { FileText, FolderOpen, Home, Settings } from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

// Mock recent documents data
const recentDocuments = [
  { id: 1, name: "Meeting Notes - Product Team", date: "2 hours ago", type: "meeting_notes" },
  { id: 2, name: "Q2 Financial Report", date: "Yesterday", type: "financial" },
  { id: 3, name: "Project Roadmap 2025", date: "3 days ago", type: "planning" },
  { id: 4, name: "Customer Feedback Summary", date: "1 week ago", type: "feedback" },
]

export function AppSidebar() {
  const [activeItem, setActiveItem] = useState("home")

  return (
    <Sidebar variant="floating" collapsible="icon">
      <SidebarHeader className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <div className="rounded-md bg-primary p-1">
            <FileText className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="font-semibold group-data-[collapsible=icon]:hidden">DocZilla</span>
        </div>
        <SidebarTrigger />
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  isActive={activeItem === "home"}
                  onClick={() => setActiveItem("home")}
                  tooltip="Home"
                >
                  <Home className="h-4 w-4" />
                  <span>Home</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  isActive={activeItem === "documents"}
                  onClick={() => setActiveItem("documents")}
                  tooltip="All Documents"
                >
                  <FolderOpen className="h-4 w-4" />
                  <span>All Documents</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Recent Documents</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {recentDocuments.map((doc) => (
                <SidebarMenuItem key={doc.id}>
                  <SidebarMenuButton tooltip={doc.name} className="py-3">
                    <FileText className="h-4 w-4 shrink-0" />
                    <div className="flex flex-col overflow-hidden">
                      <span className="truncate">{doc.name}</span>
                      <span className="text-xs text-muted-foreground">{doc.date}</span>
                    </div>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton tooltip="Settings" className="group-data-[collapsible=icon]:justify-center">
              <Settings className="h-4 w-4" />
              <span>Settings</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        <div className="mt-4 flex items-center gap-2 group-data-[collapsible=icon]:justify-center">
          <Avatar className="h-8 w-8">
            <AvatarImage src="/placeholder.svg?height=32&width=32" />
            <AvatarFallback>JD</AvatarFallback>
          </Avatar>
          <div className="flex flex-col group-data-[collapsible=icon]:hidden">
            <span className="text-sm font-medium">John Doe</span>
            <span className="text-xs text-muted-foreground">john@example.com</span>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
