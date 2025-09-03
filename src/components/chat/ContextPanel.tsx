import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ChevronDown, ChevronUp, FileText } from "lucide-react"
import { Source } from "./MessageList"

interface ContextPanelProps {
  sources: Source[]
  isVisible: boolean
}

export function ContextPanel({ sources, isVisible }: ContextPanelProps) {
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set())

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedItems(newExpanded)
  }

  if (!isVisible) return null

  // Show top 3 sources
  const topSources = sources.slice(0, 3)

  return (
    <div className="w-80 border-l bg-muted/20">
      <div className="p-4 border-b">
        <h3 className="font-medium text-sm">Context</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Top {topSources.length} relevant chunks
        </p>
      </div>
      
      <div className="p-4 space-y-3">
        {topSources.map((source, index) => (
          <Card key={index} className="text-sm">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <FileText className="h-3 w-3" />
                  Page {source.page}
                </CardTitle>
                <Badge variant="outline" className="text-xs">
                  {Math.round(source.confidence * 100)}%
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">{source.section}</p>
            </CardHeader>
            
            <CardContent className="pt-0">
              <div className={`text-xs text-muted-foreground ${
                expandedItems.has(index) ? '' : 'line-clamp-3'
              }`}>
                {source.text}
              </div>
              
              {source.text.length > 150 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleExpanded(index)}
                  className="h-6 px-2 mt-2 text-xs"
                >
                  {expandedItems.has(index) ? (
                    <>
                      <ChevronUp className="h-3 w-3 mr-1" />
                      Show less
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-3 w-3 mr-1" />
                      Expand
                    </>
                  )}
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}