import { FileText, Image, Video, Music, Archive, Code, File } from "lucide-react"
import { cn } from "@/lib/utils"

interface FileThumbnailProps {
  filename: string
  className?: string
  size?: "sm" | "md" | "lg"
}

const getFileIcon = (filename: string) => {
  const extension = filename.split('.').pop()?.toLowerCase()
  
  switch (extension) {
    case 'pdf':
      return <FileText className="w-full h-full text-red-500" />
    case 'doc':
    case 'docx':
      return <FileText className="w-full h-full text-blue-500" />
    case 'txt':
    case 'md':
      return <FileText className="w-full h-full text-gray-500" />
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'webp':
      return <Image className="w-full h-full text-green-500" />
    case 'mp4':
    case 'avi':
    case 'mov':
    case 'wmv':
      return <Video className="w-full h-full text-purple-500" />
    case 'mp3':
    case 'wav':
    case 'flac':
      return <Music className="w-full h-full text-orange-500" />
    case 'zip':
    case 'rar':
    case '7z':
      return <Archive className="w-full h-full text-yellow-500" />
    case 'js':
    case 'ts':
    case 'jsx':
    case 'tsx':
    case 'py':
    case 'java':
    case 'cpp':
    case 'c':
      return <Code className="w-full h-full text-cyan-500" />
    default:
      return <File className="w-full h-full text-muted-foreground" />
  }
}

const sizeClasses = {
  sm: "w-6 h-6",
  md: "w-8 h-8", 
  lg: "w-12 h-12"
}

export function FileThumbnail({ filename, className, size = "md" }: FileThumbnailProps) {
  return (
    <div className={cn(
      "flex items-center justify-center bg-muted/30 rounded-lg flex-shrink-0",
      sizeClasses[size],
      className
    )}>
      {getFileIcon(filename)}
    </div>
  )
}