import { useState } from "react"
import { NavLink, useLocation } from "react-router-dom"
import { 
  BookOpen, 
  Brain, 
  FileText, 
  Home, 
  MessageSquare, 
  Settings, 
  Upload,
  GraduationCap,
  Menu,
  X
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Library", href: "/library", icon: BookOpen },
  { name: "Upload", href: "/upload", icon: Upload },
  { name: "Chat", href: "/chat", icon: MessageSquare },
  { name: "Quiz", href: "/quiz", icon: Brain },
  { name: "Settings", href: "/settings", icon: Settings },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <>
      {/* Mobile backdrop */}
      {!collapsed && (
        <div 
          className="fixed inset-0 bg-black/50 lg:hidden z-40"
          onClick={() => setCollapsed(true)}
        />
      )}
      
      {/* Sidebar */}
      <div className={cn(
        "fixed left-0 top-0 z-50 h-screen bg-card border-r border-border transition-all duration-300 lg:relative lg:translate-x-0",
        collapsed ? "-translate-x-full lg:w-16" : "w-64 translate-x-0"
      )}>
        {/* Header */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-border">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <GraduationCap className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="font-bold text-lg bg-gradient-primary bg-clip-text text-transparent">
                StudyRAG
              </span>
            </div>
          )}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="p-2"
          >
            {collapsed ? <Menu className="w-4 h-4" /> : <X className="w-4 h-4" />}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || 
                           (item.href !== '/dashboard' && location.pathname.startsWith(item.href))
            
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={cn(
                  "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                  "hover:bg-muted/50 hover:text-foreground",
                  isActive 
                    ? "bg-primary text-primary-foreground shadow-primary" 
                    : "text-muted-foreground",
                  collapsed && "justify-center"
                )}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!collapsed && <span>{item.name}</span>}
              </NavLink>
            )
          })}
        </nav>

        {/* User info */}
        {!collapsed && (
          <div className="absolute bottom-4 left-4 right-4">
            <div className="p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-primary rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-primary-foreground">U</span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground truncate">
                    Demo User
                  </p>
                  <p className="text-xs text-muted-foreground truncate">
                    Level 1 • 0 XP
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}