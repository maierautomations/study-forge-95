import { useState } from "react"
import { 
  Download, 
  Edit, 
  Trash2, 
  Copy, 
  Share,
  MoreHorizontal,
  Eye,
  ExternalLink
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast"

interface DocumentActionsProps {
  document: {
    id: string
    title: string
    filename: string
  }
  onRename?: (id: string, newTitle: string) => void
  onDelete?: (id: string) => void
  onDownload?: (id: string) => void
  onShare?: (id: string) => void
}

export function DocumentActions({ 
  document, 
  onRename, 
  onDelete, 
  onDownload,
  onShare 
}: DocumentActionsProps) {
  const [showRenameDialog, setShowRenameDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [newTitle, setNewTitle] = useState(document.title)
  const { toast } = useToast()

  const handleRename = () => {
    if (newTitle.trim() === document.title) {
      setShowRenameDialog(false)
      return
    }
    
    if (newTitle.trim()) {
      onRename?.(document.id, newTitle.trim())
      setShowRenameDialog(false)
    } else {
      toast({
        title: "Invalid title",
        description: "Document title cannot be empty.",
        variant: "destructive"
      })
    }
  }

  const handleDelete = () => {
    onDelete?.(document.id)
    setShowDeleteDialog(false)
  }

  const handleDownload = () => {
    onDownload?.(document.id)
  }

  const handleShare = () => {
    // UI stub - implement sharing functionality
    onShare?.(document.id)
    toast({
      title: "Share functionality",
      description: "Document sharing will be implemented soon."
    })
  }

  const handleCopyLink = () => {
    // UI stub - copy document link
    navigator.clipboard.writeText(`${window.location.origin}/chat/${document.id}`)
    toast({
      title: "Link copied",
      description: "Document link copied to clipboard."
    })
  }

  const handleViewDetails = () => {
    // UI stub - show document details
    toast({
      title: "Document details",
      description: "Document details view will be implemented soon."
    })
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
            <span className="sr-only">Open menu</span>
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuItem onClick={handleViewDetails}>
            <Eye className="mr-2 h-4 w-4" />
            View Details
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleDownload}>
            <Download className="mr-2 h-4 w-4" />
            Download
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setShowRenameDialog(true)}>
            <Edit className="mr-2 h-4 w-4" />
            Rename
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleCopyLink}>
            <Copy className="mr-2 h-4 w-4" />
            Copy Link
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleShare}>
            <Share className="mr-2 h-4 w-4" />
            Share
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem 
            onClick={() => setShowDeleteDialog(true)}
            className="text-destructive focus:text-destructive"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Rename Dialog */}
      <Dialog open={showRenameDialog} onOpenChange={setShowRenameDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Rename Document</DialogTitle>
            <DialogDescription>
              Choose a new title for "{document.title}"
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Enter new title..."
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleRename()
                  }
                }}
              />
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowRenameDialog(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleRename}>
              Rename
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Delete Document</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{document.title}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowDeleteDialog(false)}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDelete}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}