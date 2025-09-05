import { useState, useRef, useEffect } from "react"
import { Send, FileText, Quote, Copy, BookOpen, MessageSquare, Bot, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Textarea } from "@/components/ui/textarea"
import { useDocuments } from "@/hooks/useQueries"

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Source[]
}

interface Source {
  page: number
  section: string
  text: string
  confidence: number
}

// Use real documents from API instead of mock data

const mockMessages: Message[] = [
  {
    id: '1',
    type: 'assistant',
    content: 'Hello! I\'m your AI study assistant. I can help you understand your documents, answer questions, and provide detailed explanations. Which document would you like to discuss today?',
    timestamp: new Date(Date.now() - 30000),
  }
]

export default function Chat() {
  const { data: documents = [], isLoading: documentsLoading } = useDocuments()
  const [messages, setMessages] = useState<Message[]>(mockMessages)
  const [input, setInput] = useState("")
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || !selectedDocument) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Based on your question about "${input}", I found relevant information in the document. Here's a comprehensive explanation:

The concept you're asking about is covered in detail in the selected document. The key points include:

1. **Primary Definition**: The fundamental principle behind this concept involves understanding the core mechanisms that drive the process.

2. **Applications**: This concept has several practical applications in real-world scenarios, particularly in the context of the subject matter.

3. **Important Considerations**: When applying this concept, it's crucial to consider the underlying assumptions and limitations.

Would you like me to elaborate on any of these points or explain specific aspects in more detail?`,
        timestamp: new Date(),
        sources: [
          {
            page: 42,
            section: "Chapter 3: Core Concepts",
            text: "The fundamental principle behind this concept involves understanding the core mechanisms...",
            confidence: 0.95
          },
          {
            page: 78,
            section: "Chapter 5: Applications",
            text: "This concept has several practical applications in real-world scenarios...",
            confidence: 0.87
          }
        ]
      }

      setMessages(prev => [...prev, aiMessage])
      setIsLoading(false)
    }, 2000)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-6">
      {/* Document Selection Sidebar */}
      <div className="w-80 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              Select Document
            </CardTitle>
            <CardDescription>
              Choose a document to chat with
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {documentsLoading ? (
              <div className="text-center py-4 text-muted-foreground">Loading documents...</div>
            ) : documents.length === 0 ? (
              <div className="text-center py-4 text-muted-foreground">No documents found</div>
            ) : (
              documents.map((doc) => (
                <div
                  key={doc.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedDocument === doc.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                  onClick={() => setSelectedDocument(doc.id)}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                      <FileText className="w-5 h-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium text-sm leading-tight">{doc.title || doc.filename}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {doc.status === 'completed' ? `${doc.chunksCount || 0} chunks` : 'Processing...'}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {selectedDocument && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start">
                <MessageSquare className="w-4 h-4 mr-2" />
                Summarize Document
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <FileText className="w-4 h-4 mr-2" />
                Key Concepts
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Quote className="w-4 h-4 mr-2" />
                Important Quotes
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Chat Interface */}
      <div className="flex-1 flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  AI Chat Assistant
                </CardTitle>
                {selectedDocument && (
                  <CardDescription className="mt-1">
                    Chatting with: {mockDocuments.find(d => d.id === selectedDocument)?.title}
                  </CardDescription>
                )}
              </div>
              <Badge variant="secondary">
                {messages.length - 1} messages
              </Badge>
            </div>
          </CardHeader>

          {/* Messages */}
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-6">
              {messages.map((message) => (
                <div key={message.id} className="flex gap-3">
                  <Avatar className="w-8 h-8 flex-shrink-0">
                    <AvatarFallback className={
                      message.type === 'user' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'bg-accent text-accent-foreground'
                    }>
                      {message.type === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </AvatarFallback>
                  </Avatar>
                  
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">
                        {message.type === 'user' ? 'You' : 'AI Assistant'}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    
                    <div className={`p-3 rounded-lg ${
                      message.type === 'user' 
                        ? 'bg-primary text-primary-foreground ml-8' 
                        : 'bg-muted'
                    }`}>
                      <p className="whitespace-pre-wrap leading-relaxed">
                        {message.content}
                      </p>
                      
                      {message.type === 'assistant' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="mt-2 h-auto p-1 text-xs"
                          onClick={() => copyToClipboard(message.content)}
                        >
                          <Copy className="w-3 h-3 mr-1" />
                          Copy
                        </Button>
                      )}
                    </div>

                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-muted-foreground">Sources:</p>
                        {message.sources.map((source, index) => (
                          <div key={index} className="p-3 bg-card border rounded-lg">
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <Quote className="w-4 h-4 text-primary" />
                                <span className="text-sm font-medium">
                                  Page {source.page} • {source.section}
                                </span>
                              </div>
                              <Badge variant="outline" className="text-xs">
                                {Math.round(source.confidence * 100)}% match
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground italic">
                              "{source.text}"
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex gap-3">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-accent text-accent-foreground">
                      <Bot className="w-4 h-4" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium text-sm">AI Assistant</span>
                      <span className="text-xs text-muted-foreground">typing...</span>
                    </div>
                    <div className="p-3 bg-muted rounded-lg">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="border-t p-4">
            {!selectedDocument ? (
              <div className="text-center text-muted-foreground">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Select a document to start chatting</p>
              </div>
            ) : (
              <div className="flex gap-2">
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question about your document..."
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSend()
                    }
                  }}
                  className="min-h-[44px] max-h-32 resize-none"
                />
                <Button 
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className="self-end"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}