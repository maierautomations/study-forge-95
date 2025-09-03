import { useState, useCallback } from "react"
import { FileText, Upload as UploadIcon, X, Check, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { Link } from "react-router-dom"

interface UploadFile {
  id: string
  file: File
  progress: number
  status: 'uploading' | 'completed' | 'error'
  error?: string
}

const supportedTypes = [
  { type: 'PDF', extension: '.pdf', description: 'Portable Document Format' },
  { type: 'DOC', extension: '.doc,.docx', description: 'Microsoft Word Documents' },
  { type: 'TXT', extension: '.txt', description: 'Plain Text Files' },
  { type: 'MD', extension: '.md', description: 'Markdown Files' },
]

export default function Upload() {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const { toast } = useToast()

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }, [])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files)
      handleFiles(files)
    }
  }, [])

  const handleFiles = (files: File[]) => {
    const validFiles = files.filter(file => {
      const validExtensions = ['.pdf', '.doc', '.docx', '.txt', '.md']
      const extension = '.' + file.name.split('.').pop()?.toLowerCase()
      return validExtensions.includes(extension)
    })

    const newUploadFiles: UploadFile[] = validFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      progress: 0,
      status: 'uploading'
    }))

    setUploadFiles(prev => [...prev, ...newUploadFiles])

    // Simulate upload process
    newUploadFiles.forEach(uploadFile => {
      simulateUpload(uploadFile.id)
    })

    if (files.length > validFiles.length) {
      toast({
        title: "Some files were skipped",
        description: "Only PDF, DOC, DOCX, TXT, and MD files are supported.",
        variant: "destructive"
      })
    }
  }

  const simulateUpload = (fileId: string) => {
    const interval = setInterval(() => {
      setUploadFiles(prev => prev.map(file => {
        if (file.id === fileId) {
          const newProgress = Math.min(file.progress + Math.random() * 20, 100)
          if (newProgress >= 100) {
            clearInterval(interval)
            // Simulate random success/failure
            const success = Math.random() > 0.1 // 90% success rate
            return {
              ...file,
              progress: 100,
              status: success ? 'completed' : 'error',
              error: success ? undefined : 'Upload failed. Please try again.'
            }
          }
          return { ...file, progress: newProgress }
        }
        return file
      }))
    }, 500)
  }

  const removeFile = (fileId: string) => {
    setUploadFiles(prev => prev.filter(file => file.id !== fileId))
  }

  const retryUpload = (fileId: string) => {
    setUploadFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, progress: 0, status: 'uploading' as const, error: undefined }
        : file
    ))
    simulateUpload(fileId)
  }

  const completedUploads = uploadFiles.filter(file => file.status === 'completed')

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Upload Documents</h1>
          <p className="text-muted-foreground mt-2">
            Add new study materials to your library and start learning with AI
          </p>
        </div>
        <Link to="/library">
          <Button variant="outline">
            View Library
          </Button>
        </Link>
      </div>

      {/* Supported File Types */}
      <Card>
        <CardHeader>
          <CardTitle>Supported File Types</CardTitle>
          <CardDescription>
            Upload these document types to create interactive learning experiences
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {supportedTypes.map((type) => (
              <div key={type.type} className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <Badge variant="secondary" className="mb-1">{type.type}</Badge>
                  <p className="text-xs text-muted-foreground">{type.description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Upload Area */}
      <Card>
        <CardContent className="p-8">
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              isDragOver 
                ? 'border-primary bg-primary/5' 
                : 'border-border hover:border-primary/50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <UploadIcon className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              Drag & drop your documents here
            </h3>
            <p className="text-muted-foreground mb-6">
              or click to browse and select files from your computer
            </p>
            <div>
              <input
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt,.md"
                onChange={handleFileInput}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload">
                <Button className="button-glow cursor-pointer">
                  Choose Files
                </Button>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Upload Progress */}
      {uploadFiles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Upload Progress</CardTitle>
            <CardDescription>
              Track the status of your document uploads
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {uploadFiles.map((uploadFile) => (
              <div key={uploadFile.id} className="flex items-center gap-4 p-4 bg-muted/30 rounded-lg">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  {uploadFile.status === 'completed' ? (
                    <Check className="w-5 h-5 text-success" />
                  ) : uploadFile.status === 'error' ? (
                    <AlertCircle className="w-5 h-5 text-destructive" />
                  ) : (
                    <FileText className="w-5 h-5 text-primary" />
                  )}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-medium truncate">{uploadFile.file.name}</p>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">
                        {(uploadFile.file.size / 1024 / 1024).toFixed(2)} MB
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(uploadFile.id)}
                        className="p-1 h-auto"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  
                  {uploadFile.status === 'uploading' && (
                    <div className="space-y-1">
                      <Progress value={uploadFile.progress} className="h-2" />
                      <p className="text-xs text-muted-foreground">
                        {Math.round(uploadFile.progress)}% uploaded
                      </p>
                    </div>
                  )}
                  
                  {uploadFile.status === 'completed' && (
                    <div className="flex items-center gap-2">
                      <Badge variant="default" className="bg-success text-success-foreground">
                        Completed
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        Ready for AI processing
                      </span>
                    </div>
                  )}
                  
                  {uploadFile.status === 'error' && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="destructive">Failed</Badge>
                        <span className="text-sm text-muted-foreground">
                          {uploadFile.error}
                        </span>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => retryUpload(uploadFile.id)}
                      >
                        Retry
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Success Message */}
      {completedUploads.length > 0 && (
        <Card className="border-success/50 bg-success/5">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-success/10 rounded-lg flex items-center justify-center">
                <Check className="w-6 h-6 text-success" />
              </div>
              <div>
                <h3 className="font-semibold text-success">
                  {completedUploads.length} document{completedUploads.length > 1 ? 's' : ''} uploaded successfully!
                </h3>
                <p className="text-sm text-muted-foreground">
                  Your documents are being processed and will be available for chat and quiz generation shortly.
                </p>
              </div>
            </div>
            
            <div className="flex gap-3">
              <Link to="/library">
                <Button className="button-glow">
                  View in Library
                </Button>
              </Link>
              <Link to="/chat">
                <Button variant="outline">
                  Start Chatting
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}