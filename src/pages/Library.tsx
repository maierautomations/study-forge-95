import { useState } from "react"
import { FileText, Filter, Grid, List, Plus, Search, Upload } from "lucide-react"
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

const documents = [
  {
    id: 1,
    title: "Advanced Chemistry Textbook",
    size: "15.2 MB",
    pages: 450,
    uploadDate: "2024-01-15",
    type: "pdf",
    tags: ["chemistry", "textbook", "advanced"],
    chatCount: 12,
    quizCount: 3
  },
  {
    id: 2,
    title: "Machine Learning Fundamentals",
    size: "8.7 MB", 
    pages: 320,
    uploadDate: "2024-01-12",
    type: "pdf",
    tags: ["ml", "ai", "fundamentals"],
    chatCount: 8,
    quizCount: 2
  },
  {
    id: 3,
    title: "History Research Notes",
    size: "2.1 MB",
    pages: 85,
    uploadDate: "2024-01-10",
    type: "doc",
    tags: ["history", "research", "notes"],
    chatCount: 5,
    quizCount: 1
  },
  {
    id: 4,
    title: "Biology Lab Manual",
    size: "22.4 MB",
    pages: 280,
    uploadDate: "2024-01-08",
    type: "pdf", 
    tags: ["biology", "lab", "manual"],
    chatCount: 15,
    quizCount: 4
  },
  {
    id: 5,
    title: "Economics Study Guide",
    size: "5.3 MB",
    pages: 120,
    uploadDate: "2024-01-05",
    type: "pdf",
    tags: ["economics", "study guide"],
    chatCount: 7,
    quizCount: 2
  },
  {
    id: 6,
    title: "Programming Concepts",
    size: "12.8 MB",
    pages: 380,
    uploadDate: "2024-01-03",
    type: "pdf",
    tags: ["programming", "concepts", "cs"],
    chatCount: 20,
    quizCount: 5
  }
]

export default function Library() {
  const [searchQuery, setSearchQuery] = useState("")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [sortBy, setSortBy] = useState("recent")

  const filteredDocuments = documents.filter(doc =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const sortedDocuments = [...filteredDocuments].sort((a, b) => {
    switch (sortBy) {
      case "name":
        return a.title.localeCompare(b.title)
      case "size":
        return parseFloat(b.size) - parseFloat(a.size)
      case "recent":
      default:
        return new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime()
    }
  })

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
                  {documents.reduce((acc, doc) => acc + parseFloat(doc.size), 0).toFixed(1)} MB
                </p>
                <p className="text-sm text-muted-foreground">Total Size</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-success/10 rounded-lg flex items-center justify-center">
                <span className="text-success font-bold text-lg">?</span>
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {documents.reduce((acc, doc) => acc + doc.chatCount, 0)}
                </p>
                <p className="text-sm text-muted-foreground">Chat Sessions</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-warning/10 rounded-lg flex items-center justify-center">
                <span className="text-warning font-bold text-lg">Q</span>
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {documents.reduce((acc, doc) => acc + doc.quizCount, 0)}
                </p>
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
                <div className="flex items-start gap-3">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FileText className="w-6 h-6 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <CardTitle className="text-lg truncate">{doc.title}</CardTitle>
                    <CardDescription className="mt-1">
                      {doc.size} • {doc.pages} pages • {new Date(doc.uploadDate).toLocaleDateString()}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className={viewMode === "list" ? "pt-2" : ""}>
                <div className="space-y-3">
                  <div className="flex flex-wrap gap-1">
                    {doc.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>{doc.chatCount} chats</span>
                    <span>{doc.quizCount} quizzes</span>
                  </div>
                  
                  <div className="flex gap-2">
                    <Link to={`/chat/${doc.id}`} className="flex-1">
                      <Button variant="outline" size="sm" className="w-full">
                        Chat
                      </Button>
                    </Link>
                    <Link to={`/quiz/${doc.id}/build`} className="flex-1">
                      <Button variant="outline" size="sm" className="w-full">
                        Quiz
                      </Button>
                    </Link>
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