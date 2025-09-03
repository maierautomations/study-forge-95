import { useState } from "react"
import { FileText, Filter, Grid, List, Plus, Search, Upload, MessageSquare, Brain, Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu"
import { Link } from "react-router-dom"
import { useDocuments, useDeleteDocument, useRenameDocument, useDocumentDownloadUrl } from "@/hooks/useQueries"
import { useToast } from "@/hooks/use-toast"
import { FileThumbnail } from "@/components/ui/file-thumbnail"
import { DocumentActions } from "@/components/ui/context-menu-actions"
import { formatFileSize } from "@/lib/storage"


export default function Library() {
  const [searchQuery, setSearchQuery] = useState("")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [sortBy, setSortBy] = useState("recent")
  
  const { data: documents = [], isLoading, error } = useDocuments()
  const { toast } = useToast()

  const deleteDocument = useDeleteDocument()
  const renameDocument = useRenameDocument()

  const handleDelete = (id: string) => {
    deleteDocument.mutate(id)
  }

  const handleRename = (id: string, newTitle: string) => {
    renameDocument.mutate({ id, newTitle })
  }

  const handleDownload = async (id: string) => {
    try {
      const document = documents.find(doc => doc.id === id)
      if (!document) return

      // This would typically use the signed URL
      toast({
        title: "Download started",
        description: `Downloading "${document.title}"...`
      })
      
      // UI stub - actual download implementation would use signed URLs
      // const downloadUrl = await documentApi.getDownloadUrl(id)
      // window.open(downloadUrl, '_blank')
    } catch (error) {
      toast({
        title: "Download failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive"
      })
    }
  }

  const handleShare = (id: string) => {
    // UI stub for sharing functionality
    const document = documents.find(doc => doc.id === id)
    toast({
      title: "Share feature",
      description: `Sharing functionality for "${document?.title}" will be implemented soon.`
    })
  }

  const filteredDocuments = documents.filter(doc =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const sortedDocuments = [...filteredDocuments].sort((a, b) => {
    switch (sortBy) {
      case "name":
        return a.title.localeCompare(b.title)
      case "size":
        return b.file_size - a.file_size
      case "recent":
      default:
        return new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime()
    }
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-destructive">Failed to load documents. Please try again.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Document Library</h1>
          <p className="text-muted-foreground mt-2">
            Manage your study materials and access your learning content
          </p>
        </div>
        <Link to="/upload">
          <Button className="button-glow">
            <Plus className="w-4 h-4 mr-2" />
            Upload Document
          </Button>
        </Link>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search documents and tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Sort */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Filter className="w-4 h-4 mr-2" />
                  Sort by {sortBy}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setSortBy("recent")}>
                  Most Recent
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSortBy("name")}>
                  Name
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSortBy("size")}>
                  Size
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* View Mode */}
            <div className="flex border rounded-lg">
              <Button
                variant={viewMode === "grid" ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode("grid")}
                className="rounded-r-none"
              >
                <Grid className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode("list")}
                className="rounded-l-none"
              >
                <List className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-primary" />
              <div>
                <p className="text-2xl font-bold">{documents.length}</p>
                <p className="text-sm text-muted-foreground">Total Documents</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Upload className="w-8 h-8 text-accent" />
                <div>
                  <p className="text-2xl font-bold">
                    {formatFileSize(documents.reduce((acc, doc) => acc + doc.file_size, 0))}
                  </p>
                  <p className="text-sm text-muted-foreground">Total Size</p>
                </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <MessageSquare className="w-8 h-8 text-success" />
                <div>
                  <p className="text-2xl font-bold">-</p>
                  <p className="text-sm text-muted-foreground">Chat Sessions</p>
                </div>
              </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Brain className="w-8 h-8 text-warning" />
                <div>
                  <p className="text-2xl font-bold">-</p>
                  <p className="text-sm text-muted-foreground">Quizzes Created</p>
                </div>
              </div>
          </CardContent>
        </Card>
      </div>

      {/* Documents */}
      {sortedDocuments.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <FileText className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No documents found</h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery ? "Try adjusting your search terms" : "Upload your first document to get started"}
            </p>
            <Link to="/upload">
              <Button>
                <Upload className="w-4 h-4 mr-2" />
                Upload Document
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className={
          viewMode === "grid" 
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            : "space-y-4"
        }>
          {sortedDocuments.map((doc) => (
            <Card key={doc.id} className={`card-hover ${viewMode === "list" ? "flex-row" : ""}`}>
              <CardHeader className={viewMode === "list" ? "flex-row space-y-0 pb-2" : ""}>
                <div className="flex items-start gap-3 w-full">
                  <FileThumbnail 
                    filename={doc.filename} 
                    size="lg"
                    className="flex-shrink-0"
                  />
                  <div className="min-w-0 flex-1">
                    <CardTitle className="text-lg truncate">{doc.title}</CardTitle>
                    <CardDescription className="mt-1">
                      {formatFileSize(doc.file_size)} • {new Date(doc.upload_date).toLocaleDateString()}
                    </CardDescription>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge 
                        variant={doc.status === 'ready' ? 'default' : doc.status === 'error' ? 'destructive' : 'secondary'}
                        className="text-xs"
                      >
                        {doc.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{doc.filename}</span>
                    </div>
                  </div>
                  <DocumentActions
                    document={{
                      id: doc.id,
                      title: doc.title,
                      filename: doc.filename
                    }}
                    onRename={handleRename}
                    onDelete={handleDelete}
                    onDownload={handleDownload}
                    onShare={handleShare}
                  />
                </div>
              </CardHeader>
              <CardContent className={viewMode === "list" ? "pt-2" : ""}>
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <Link to={`/chat/${doc.id}`} className="flex-1">
                      <Button variant="outline" size="sm" className="w-full">
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Chat
                      </Button>
                    </Link>
                    <Link to={`/quiz/${doc.id}/build`} className="flex-1">
                      <Button variant="outline" size="sm" className="w-full">
                        <Brain className="w-4 h-4 mr-2" />
                        Quiz
                      </Button>
                    </Link>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleDownload(doc.id)}
                      className="px-3"
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}