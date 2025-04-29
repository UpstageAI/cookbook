"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Upload, X, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

interface FileUploaderProps {
  onUpload: (files: File[]) => void
  onCancel: () => void
  isUploading: boolean
}

export function FileUploader({ onUpload, onCancel, isUploading }: FileUploaderProps) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const filesArray = Array.from(e.dataTransfer.files)
      setSelectedFiles(filesArray)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const filesArray = Array.from(e.target.files)
      setSelectedFiles(filesArray)
    }
  }

  const handleUpload = () => {
    if (selectedFiles.length > 0) {
      onUpload(selectedFiles)
    }
  }

  const openFileSelector = () => {
    fileInputRef.current?.click()
  }

  return (
    <Card
      className={`relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition-colors ${
        dragActive ? "border-primary bg-primary/5" : "border-border"
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <Button variant="ghost" size="sm" className="absolute right-2 top-2" onClick={onCancel}>
        <X className="h-4 w-4" />
      </Button>

      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleFileChange}
        accept=".pdf,.png,.jpg,.jpeg"
      />

      {isUploading ? (
        <div className="flex flex-col items-center gap-2 py-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Uploading document...</p>
        </div>
      ) : selectedFiles.length > 0 ? (
        <div className="w-full space-y-4">
          <div className="space-y-2">
            {selectedFiles.map((file, index) => (
              <div key={index} className="flex items-center justify-between rounded-md bg-muted p-2">
                <div className="flex items-center gap-2">
                  <div className="rounded-md bg-background p-1">
                    <Upload className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{file.name}</span>
                    <span className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(0)} KB</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setSelectedFiles([])}>
              Clear
            </Button>
            <Button onClick={handleUpload}>Upload</Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-4">
          <div className="rounded-full bg-primary/10 p-3">
            <Upload className="h-6 w-6 text-primary" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium">Drag and drop your files here</p>
            <p className="text-xs text-muted-foreground">Supports PDF, PNG, and JPG files</p>
          </div>
          <Button onClick={openFileSelector}>Select Files</Button>
        </div>
      )}
    </Card>
  )
}
