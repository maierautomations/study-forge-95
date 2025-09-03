import { Bell, Search, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function Header() {
  return (
    <header className="h-16 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-full items-center justify-between px-6">
        {/* Search */}
        <div className="flex items-center space-x-4 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search documents, chats, quizzes..."
              className="pl-10 bg-muted/50 border-0 focus-visible:ring-1"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <Button variant="ghost" size="sm" className="relative">
            <Bell className="w-5 h-5" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-accent rounded-full text-xs"></span>
          </Button>

          {/* User menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="space-x-2">
                <div className="w-6 h-6 bg-gradient-primary rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-primary-foreground" />
                </div>
                <span className="hidden md:inline">Demo User</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem>Profile</DropdownMenuItem>
              <DropdownMenuItem>Settings</DropdownMenuItem>
              <DropdownMenuItem>Billing</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive">
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}