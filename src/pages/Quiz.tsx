import { useState } from "react"
import { Brain, Clock, FileText, Play, Plus, Settings, Target, TrendingUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Link } from "react-router-dom"

const mockDocuments = [
  { id: 1, title: "Advanced Chemistry Textbook", pages: 450 },
  { id: 2, title: "Machine Learning Fundamentals", pages: 320 },
  { id: 3, title: "Biology Lab Manual", pages: 280 },
]

const recentQuizzes = [
  {
    id: 1,
    title: "Organic Chemistry Basics",
    documentTitle: "Advanced Chemistry Textbook",
    questions: 20,
    score: 85,
    timeSpent: "12 min",
    date: "2024-01-15",
    difficulty: "Intermediate"
  },
  {
    id: 2,
    title: "Neural Networks Quiz",
    documentTitle: "Machine Learning Fundamentals", 
    questions: 15,
    score: 92,
    timeSpent: "8 min",
    date: "2024-01-12",
    difficulty: "Advanced"
  },
  {
    id: 3,
    title: "Cell Biology Test",
    documentTitle: "Biology Lab Manual",
    questions: 25,
    score: 78,
    timeSpent: "15 min",
    date: "2024-01-10",
    difficulty: "Beginner"
  }
]

export default function Quiz() {
  const [selectedDocument, setSelectedDocument] = useState<number | null>(null)

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'beginner': return 'text-success'
      case 'intermediate': return 'text-warning'
      case 'advanced': return 'text-destructive'
      default: return 'text-muted-foreground'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-success'
    if (score >= 70) return 'text-warning'
    return 'text-destructive'
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Quiz Center</h1>
          <p className="text-muted-foreground mt-2">
            Test your knowledge with AI-generated quizzes from your documents
          </p>
        </div>
        <Button className="button-glow">
          <Plus className="w-4 h-4 mr-2" />
          Create New Quiz
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <Brain className="w-8 h-8 text-primary" />
              <div>
                <p className="text-2xl font-bold">{recentQuizzes.length}</p>
                <p className="text-sm text-muted-foreground">Quizzes Taken</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <Target className="w-8 h-8 text-accent" />
              <div>
                <p className="text-2xl font-bold">
                  {Math.round(recentQuizzes.reduce((acc, quiz) => acc + quiz.score, 0) / recentQuizzes.length)}%
                </p>
                <p className="text-sm text-muted-foreground">Average Score</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <Clock className="w-8 h-8 text-success" />
              <div>
                <p className="text-2xl font-bold">12</p>
                <p className="text-sm text-muted-foreground">Avg. Time (min)</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-warning/10 rounded-lg flex items-center justify-center">
                <span className="text-warning font-bold">7</span>
              </div>
              <div>
                <p className="text-2xl font-bold">7</p>
                <p className="text-sm text-muted-foreground">Day Streak</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Quiz Builder */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Create New Quiz
            </CardTitle>
            <CardDescription>
              Generate a custom quiz from your documents
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Document Selection */}
            <div>
              <label className="text-sm font-medium mb-3 block">Select Document</label>
              <div className="grid gap-3">
                {mockDocuments.map((doc) => (
                  <div
                    key={doc.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedDocument === doc.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => setSelectedDocument(doc.id)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                        <FileText className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">{doc.title}</p>
                        <p className="text-sm text-muted-foreground">{doc.pages} pages</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {selectedDocument && (
              <>
                {/* Quiz Settings */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Number of Questions</label>
                    <select className="w-full p-2 border rounded-lg bg-background">
                      <option value="10">10 Questions</option>
                      <option value="15">15 Questions</option>
                      <option value="20">20 Questions</option>
                      <option value="25">25 Questions</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">Difficulty</label>
                    <select className="w-full p-2 border rounded-lg bg-background">
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">Question Types</label>
                    <select className="w-full p-2 border rounded-lg bg-background">
                      <option value="mixed">Mixed Types</option>
                      <option value="multiple-choice">Multiple Choice</option>
                      <option value="true-false">True/False</option>
                      <option value="short-answer">Short Answer</option>
                    </select>
                  </div>
                </div>

                {/* Generate Button */}
                <div className="flex gap-3">
                  <Link to={`/quiz/${selectedDocument}/build`} className="flex-1">
                    <Button className="w-full button-glow">
                      <Brain className="w-4 h-4 mr-2" />
                      Generate Quiz
                    </Button>
                  </Link>
                  <Button variant="outline">
                    <Settings className="w-4 h-4 mr-2" />
                    Advanced Options
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Recent Quizzes */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Recent Quizzes
            </CardTitle>
            <CardDescription>
              Your latest quiz attempts
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentQuizzes.slice(0, 3).map((quiz) => (
              <div key={quiz.id} className="p-3 bg-muted/50 rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-medium text-sm">{quiz.title}</p>
                    <p className="text-xs text-muted-foreground">{quiz.documentTitle}</p>
                  </div>
                  <Badge variant="outline" className={getDifficultyColor(quiz.difficulty)}>
                    {quiz.difficulty}
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-lg font-bold ${getScoreColor(quiz.score)}`}>
                    {quiz.score}%
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {quiz.questions} questions • {quiz.timeSpent}
                  </span>
                </div>
                
                <Progress value={quiz.score} className="h-2 mb-2" />
                
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">
                    {new Date(quiz.date).toLocaleDateString()}
                  </span>
                  <Button variant="ghost" size="sm">
                    <Play className="w-3 h-3 mr-1" />
                    Retake
                  </Button>
                </div>
              </div>
            ))}
            
            <Button variant="outline" className="w-full">
              View All Quizzes
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Performance Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Performance Analysis
          </CardTitle>
          <CardDescription>
            Track your learning progress across different subjects
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Chemistry</span>
                <span className="text-sm text-muted-foreground">85%</span>
              </div>
              <Progress value={85} className="h-2" />
              <p className="text-xs text-muted-foreground">5 quizzes completed</p>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Machine Learning</span>
                <span className="text-sm text-muted-foreground">92%</span>
              </div>
              <Progress value={92} className="h-2" />
              <p className="text-xs text-muted-foreground">3 quizzes completed</p>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Biology</span>
                <span className="text-sm text-muted-foreground">78%</span>
              </div>
              <Progress value={78} className="h-2" />
              <p className="text-xs text-muted-foreground">4 quizzes completed</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}