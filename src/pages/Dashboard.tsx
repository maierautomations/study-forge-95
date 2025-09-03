import { BookOpen, Brain, Clock, FileText, MessageSquare, TrendingUp, Trophy, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Link } from "react-router-dom"

const recentDocuments = [
  { id: 1, title: "Advanced Chemistry Textbook", lastAccessed: "2 hours ago", type: "pdf" },
  { id: 2, title: "Machine Learning Notes", lastAccessed: "1 day ago", type: "doc" },
  { id: 3, title: "History of Art Research", lastAccessed: "3 days ago", type: "pdf" },
]

const recentQuizzes = [
  { id: 1, title: "Organic Chemistry Basics", score: 85, totalQuestions: 20 },
  { id: 2, title: "Neural Networks Quiz", score: 92, totalQuestions: 15 },
  { id: 3, title: "Renaissance Art Period", score: 78, totalQuestions: 25 },
]

const stats = [
  { 
    icon: FileText, 
    label: "Documents", 
    value: "12", 
    change: "+2 this week",
    color: "text-primary"
  },
  { 
    icon: MessageSquare, 
    label: "Chat Sessions", 
    value: "47", 
    change: "+8 this week",
    color: "text-accent"
  },
  { 
    icon: Brain, 
    label: "Quizzes Taken", 
    value: "23", 
    change: "+5 this week",
    color: "text-success"
  },
  { 
    icon: Trophy, 
    label: "Average Score", 
    value: "85%", 
    change: "+3% this week",
    color: "text-warning"
  },
]

export default function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Welcome back, Demo User!</h1>
          <p className="text-muted-foreground mt-2">
            Continue your learning journey. You have 3 new chat responses and 2 quiz recommendations.
          </p>
        </div>
        <div className="flex gap-3">
          <Link to="/upload">
            <Button className="button-glow">
              <FileText className="w-4 h-4 mr-2" />
              Upload Document
            </Button>
          </Link>
          <Link to="/quiz">
            <Button variant="outline">
              <Brain className="w-4 h-4 mr-2" />
              Take Quiz
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <Card key={index} className="card-hover">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <stat.icon className={`w-8 h-8 ${stat.color}`} />
                <span className="text-2xl font-bold">{stat.value}</span>
              </div>
              <div>
                <p className="text-sm font-medium">{stat.label}</p>
                <p className="text-xs text-muted-foreground mt-1">{stat.change}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Learning Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Learning Progress
          </CardTitle>
          <CardDescription>
            Track your study streak and XP growth
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Study Streak</p>
              <p className="text-2xl font-bold text-primary">7 days</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium">Total XP</p>
              <p className="text-2xl font-bold text-accent">1,247</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progress to next level</span>
              <span>1,247 / 2,000 XP</span>
            </div>
            <Progress value={62.35} className="h-2" />
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Documents */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              Recent Documents
            </CardTitle>
            <CardDescription>
              Continue where you left off
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentDocuments.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{doc.title}</p>
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {doc.lastAccessed}
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="sm">
                  Open
                </Button>
              </div>
            ))}
            <Link to="/library">
              <Button variant="outline" className="w-full">
                View All Documents
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Recent Quiz Results */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5" />
              Recent Quiz Results
            </CardTitle>
            <CardDescription>
              Your latest performance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentQuizzes.map((quiz) => (
              <div key={quiz.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center">
                    <Brain className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <p className="font-medium">{quiz.title}</p>
                    <p className="text-sm text-muted-foreground">
                      {quiz.score}% ({quiz.score}/{quiz.totalQuestions})
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`text-sm font-medium ${
                    quiz.score >= 90 ? 'text-success' : 
                    quiz.score >= 70 ? 'text-warning' : 'text-destructive'
                  }`}>
                    {quiz.score >= 90 ? 'Excellent' : 
                     quiz.score >= 70 ? 'Good' : 'Needs Improvement'}
                  </span>
                </div>
              </div>
            ))}
            <Link to="/quiz">
              <Button variant="outline" className="w-full">
                Take New Quiz
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Quick Actions
          </CardTitle>
          <CardDescription>
            Jump right into your learning activities
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link to="/upload">
              <Button variant="outline" className="w-full h-auto p-6 flex-col gap-2">
                <FileText className="w-8 h-8 text-primary" />
                <span className="font-medium">Upload New Document</span>
                <span className="text-sm text-muted-foreground">Add study materials</span>
              </Button>
            </Link>
            
            <Link to="/chat">
              <Button variant="outline" className="w-full h-auto p-6 flex-col gap-2">
                <MessageSquare className="w-8 h-8 text-accent" />
                <span className="font-medium">Start Chat Session</span>
                <span className="text-sm text-muted-foreground">Ask questions</span>
              </Button>
            </Link>
            
            <Link to="/quiz">
              <Button variant="outline" className="w-full h-auto p-6 flex-col gap-2">
                <Brain className="w-8 h-8 text-success" />
                <span className="font-medium">Generate Quiz</span>
                <span className="text-sm text-muted-foreground">Test your knowledge</span>
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}