import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { User, Bot, FileText } from "lucide-react"

export interface Source {
  page: number
  section: string
  text: string
  confidence: number
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Source[]
}

interface MessageListProps {
  messages: Message[]
  onSourceClick?: (source: Source) => void
}

export function MessageList({ messages, onSourceClick }: MessageListProps) {
  return (
    <ScrollArea className="flex-1 p-4">
      <div className="space-y-6">
        {messages.map((message) => (
          <div key={message.id} className="flex gap-3">
            <Avatar className="h-8 w-8">
              <AvatarFallback>
                {message.role === 'user' ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </AvatarFallback>
            </Avatar>
            
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">
                  {message.role === 'user' ? 'You' : 'AI Assistant'}
                </span>
                <span className="text-xs text-muted-foreground">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
              
              <div className="prose prose-sm max-w-none">
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>
              </div>
              
              {message.sources && message.sources.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-medium text-muted-foreground">
                    Sources:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {message.sources.map((source, index) => (
                      <Badge
                        key={index}
                        variant="secondary"
                        className="cursor-pointer hover:bg-secondary/80 transition-colors"
                        onClick={() => onSourceClick?.(source)}
                      >
                        <FileText className="h-3 w-3 mr-1" />
                        Page {source.page} • {source.section}
                        <span className="ml-1 text-xs opacity-70">
                          ({Math.round(source.confidence * 100)}%)
                        </span>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}