"use client"

import type React from "react"

import { useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { Upload, FileText, AlertCircle, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/hooks/use-toast"

export function FileUpload() {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()
  const router = useRouter()

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files.length) {
      validateAndSetFile(files[0])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      validateAndSetFile(files[0])
    }
  }

  const validateAndSetFile = (file: File) => {
    // Check if file is PDF
    if (file.type !== "application/pdf") {
      toast({
        title: "Invalid file type",
        description: "Please upload a PDF document",
        variant: "destructive",
      })
      return
    }

    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Please upload a file smaller than 10MB",
        variant: "destructive",
      })
      return
    }

    setSelectedFile(file)
    toast({
      title: "File selected",
      description: `${file.name} (${formatFileSize(file.size)})`,
    })
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + " bytes"
    else if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB"
    else return (bytes / (1024 * 1024)).toFixed(1) + " MB"
  }

  const handleFileUpload = async () => {
    if (!selectedFile) {
      toast({
        title: "No file selected",
        description: "Please select a PDF document to upload",
        variant: "destructive",
      })
      return
    }

    setIsUploading(true)
    setUploadProgress(0)

    // 업로드 시작 시 토스트 메시지 표시
    toast({
      title: "Upload started",
      description: "Your document is being uploaded and processed...",
    })

    try {
      // 업로드 진행 상태를 시뮬레이션 (실제로는 진행 상태를 보려면 서버 응답이 필요)
      const updateProgress = () => {
        setUploadProgress(prev => {
          // 95%까지만 진행 (실제 완료는 서버 응답 후)
          if (prev < 95) {
            return prev + (5 + Math.random() * 10)
          }
          return prev
        })
      }

      // 진행 상태 업데이트 시작
      const progressInterval = setInterval(updateProgress, 500)

      // FormData 생성
      console.log(selectedFile)
      const formData = new FormData()
      formData.append('document', selectedFile)

      // Next.js API 라우트로 파일 업로드
      const response = await fetch('/api/pdf-upload', {
        method: 'POST',
        body: formData,
      })

      // 진행 상태 업데이트 중지
      clearInterval(progressInterval)

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const data = await response.json()
      
      // 업로드 성공 처리
      setUploadProgress(100)
      setUploadedFiles((prev) => [...prev, selectedFile.name])

      toast({
        title: "Upload successful",
        description: "Your document has been uploaded and is being analyzed",
        variant: "default",
      })

      // 상태 초기화
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }

      // 대시보드로 리다이렉트 (모든 데이터와 함께)
      console.log(data)
      const queryParams = new URLSearchParams({
        fileUrl: data.file_url,
        summary: data.summary,
        keyValues: JSON.stringify(data.key_values),
        keyFindings: JSON.stringify(data.key_findings),
        highlights: JSON.stringify(data.highlights)
      }).toString()
      // Router 이동
      router.push(`/dashboard/${data.pdf_id}?${queryParams}`)

    } catch (error) {
      console.error('Upload error:', error)
      toast({
        title: "Upload failed",
        description: "There was an error uploading your document. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  return (
    <div className="space-y-6">
      <Card
        className={`border-2 border-dashed transition-colors ${
          isDragging ? "border-primary bg-primary/5" : "border-border"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="flex flex-col items-center justify-center p-6 text-center">
          <div className="flex flex-col items-center justify-center space-y-4 py-8">
            <div className="rounded-full bg-primary/10 p-4">
              <Upload className="h-8 w-8 text-primary" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-semibold">Upload Financial Document</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Drag and drop your financial PDF document or click to browse. We support investment prospectuses,
                product explanations, and other financial documents.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">PDF files only (Max 10MB)</span>
            </div>
            {isUploading ? (
              <div className="w-full max-w-xs space-y-2">
                <Progress value={uploadProgress} className="h-2 w-full" />
                <p className="text-xs text-muted-foreground">Uploading... {uploadProgress}%</p>
              </div>
            ) : (
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
                  Browse Files
                </Button>
                <input
                  ref={fileInputRef}
                  id="file-upload"
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={handleFileChange}
                  disabled={isUploading}
                />
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <AlertCircle className="h-3 w-3" />
            <span>Your documents are securely processed and analyzed</span>
          </div>
        </CardContent>
      </Card>

      {selectedFile && !isUploading && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="rounded-md bg-primary/10 p-2">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-xs text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
                </div>
              </div>
              <Button 
                onClick={handleFileUpload} 
                disabled={isUploading}
                className="min-w-[120px]"
              >
                {isUploading ? (
                  <div className="flex items-center gap-2">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent"></div>
                    <span>Uploading...</span>
                  </div>
                ) : (
                  'Upload and Analyze'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {uploadedFiles.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h3 className="font-medium mb-2">Recently Uploaded</h3>
            <ul className="space-y-2">
              {uploadedFiles.map((fileName, index) => (
                <li key={index} className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-green-500" />
                  {fileName}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

