import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { FileText } from 'lucide-react'
import { useDocument, useDocuments } from '@/hooks/useQueries'
import { ragApi } from '@/lib/api'
import { MessageList, Message, Source } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { ContextPanel } from '@/components/chat/ContextPanel'
import { useToast } from '@/hooks/use-toast'

const Chat = () => {
  const { docId } = useParams<{ docId: string }>()
  const [messages, setMessages] = useState<Message[]>([])
  const [contextSources, setContextSources] = useState<Source[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<string | null>(docId || null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  const { data: documents } = useDocuments()
  const { data: document } = useDocument(selectedDocument || '')

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async (content: string) => {
    if (!selectedDocument) {
      toast({
        title: 'No document selected',
        description: 'Please select a document first',
        variant: 'destructive'
      })
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    // Start AI response
    const aiMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      sources: []
    }

    setMessages(prev => [...prev, aiMessage])

    try {
      // Stream response
      for await (const chunk of ragApi.query(selectedDocument, content)) {
        if (chunk.type === 'chunk' && chunk.content) {
          setMessages(prev => prev.map(msg => 
            msg.id === aiMessage.id 
              ? { ...msg, content: msg.content + chunk.content }
              : msg
          ))
        } else if (chunk.type === 'sources' && chunk.sources) {
          setMessages(prev => prev.map(msg => 
            msg.id === aiMessage.id 
              ? { ...msg, sources: chunk.sources }
              : msg
          ))
          setContextSources(chunk.sources)
        }
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to get response',
        variant: 'destructive'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSourceClick = (source: Source) => {
    toast({
      title: `Page ${source.page}`,
      description: `${source.section}: ${source.text.slice(0, 100)}...`
    })
  }

  return (
    <div className="flex h-full">
      {/* Document Selection Sidebar */}
      <div className="w-64 border-r bg-muted/20 p-4">
        <h3 className="font-semibold mb-4">Select Document</h3>
        <div className="space-y-2">
          {documents?.map((doc) => (
            <Card
              key={doc.id}
              className={`cursor-pointer transition-colors ${
                selectedDocument === doc.id ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => setSelectedDocument(doc.id)}
            >
              <CardContent className="p-3">
                <h4 className="text-sm font-medium line-clamp-2">{doc.title}</h4>
                <p className="text-xs text-muted-foreground mt-1">
                  {(doc.file_size / 1024).toFixed(1)} KB
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedDocument && document ? (
          <>
            <div className="border-b p-4">
              <h2 className="font-medium">{document.title}</h2>
              <p className="text-sm text-muted-foreground">
                Chat with this document
              </p>
            </div>

            <div className="flex flex-1 overflow-hidden">
              <div className="flex-1 flex flex-col">
                <MessageList 
                  messages={messages} 
                  onSourceClick={handleSourceClick}
                />
                <ChatInput 
                  onSend={handleSend} 
                  disabled={isLoading}
                  placeholder={`Ask a question about "${document.title}"...`}
                />
                <div ref={messagesEndRef} />
              </div>

              <ContextPanel 
                sources={contextSources}
                isVisible={contextSources.length > 0}
              />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium mb-2">
                {docId ? 'Document not found' : 'Select a Document'}
              </h3>
              <p className="text-muted-foreground">
                {docId 
                  ? 'The requested document could not be found'
                  : 'Choose a document from the sidebar to start asking questions'
                }
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Chat