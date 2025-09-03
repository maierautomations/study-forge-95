import { Link } from "react-router-dom"
import { ArrowRight, BookOpen, Brain, FileText, MessageSquare, Star, Users, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const features = [
  {
    icon: MessageSquare,
    title: "AI-Powered Chat",
    description: "Interact with your documents through intelligent conversations. Ask questions and get precise answers with source citations."
  },
  {
    icon: Brain,
    title: "Smart Quiz Generation", 
    description: "Automatically generate quizzes from your content with customizable difficulty levels and question types."
  },
  {
    icon: FileText,
    title: "Document Analysis",
    description: "Upload PDFs, docs, and text files. Our AI extracts key information and makes it searchable and interactive."
  },
  {
    icon: Zap,
    title: "Instant Insights",
    description: "Get immediate feedback on your learning progress with detailed analytics and personalized recommendations."
  }
]

const testimonials = [
  {
    name: "Sarah Chen",
    role: "Medical Student",
    content: "StudyRAG transformed how I study. I can chat with my textbooks and generate practice quizzes instantly!",
    rating: 5
  },
  {
    name: "David Rodriguez", 
    role: "Law Student",
    content: "The citation feature is incredible. I can trace every answer back to the exact source in my documents.",
    rating: 5
  },
  {
    name: "Emily Watson",
    role: "Graduate Researcher", 
    content: "Perfect for literature review. I can quickly find relevant information across hundreds of papers.",
    rating: 5
  }
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="font-bold text-xl bg-gradient-primary bg-clip-text text-transparent">
                StudyRAG
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link to="/auth/signin">
                <Button variant="ghost">Sign In</Button>
              </Link>
              <Link to="/auth/signin">
                <Button className="button-glow">Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="hero-gradient absolute inset-0 opacity-10"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 lg:py-32">
          <div className="text-center animate-fade-in-up">
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight">
              Transform Your Documents Into
              <span className="block bg-gradient-primary bg-clip-text text-transparent">
                Interactive Learning
              </span>
            </h1>
            
            <p className="mt-6 text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              Upload your study materials and let AI create personalized learning experiences. 
              Chat with your documents, generate quizzes, and accelerate your learning journey.
            </p>
            
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/auth/signin">
                <Button size="lg" className="button-glow text-lg px-8 py-6 w-full sm:w-auto">
                  Start Learning Now
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <Button variant="outline" size="lg" className="text-lg px-8 py-6 w-full sm:w-auto">
                Watch Demo
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold mb-4">
              Everything You Need to Learn Smarter
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Powerful AI tools designed to enhance your study experience and boost retention.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="card-hover">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <feature.icon className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-muted-foreground leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold mb-4">
              Loved by Students Worldwide
            </h2>
            <p className="text-xl text-muted-foreground">
              Join thousands of learners who've transformed their study experience.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="card-hover">
                <CardContent className="pt-6">
                  <div className="flex mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <p className="text-muted-foreground mb-4 leading-relaxed">
                    "{testimonial.content}"
                  </p>
                  <div>
                    <p className="font-semibold">{testimonial.name}</p>
                    <p className="text-sm text-muted-foreground">{testimonial.role}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-hero relative overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl lg:text-5xl font-bold text-white mb-6">
            Ready to Revolutionize Your Learning?
          </h2>
          <p className="text-xl text-white/90 mb-8 leading-relaxed">
            Join StudyRAG today and experience the future of intelligent learning.
          </p>
          <Link to="/auth/signin">
            <Button size="lg" variant="secondary" className="text-lg px-8 py-6 bg-white/90 text-primary hover:bg-white">
              Get Started Free
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <div className="w-6 h-6 bg-gradient-primary rounded-lg flex items-center justify-center">
                <BookOpen className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="font-bold bg-gradient-primary bg-clip-text text-transparent">
                StudyRAG
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2024 StudyRAG. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}