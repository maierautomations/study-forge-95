import { useState } from "react"
import { Bell, Key, Shield, User, Moon, Sun, Globe, Download, Trash2, Save } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"

export default function Settings() {
  const [profile, setProfile] = useState({
    displayName: "Demo User",
    email: "demo@studyrag.com",
    avatar: ""
  })

  const [preferences, setPreferences] = useState({
    darkMode: false,
    emailNotifications: true,
    pushNotifications: true,
    weeklyDigest: true,
    studyReminders: true,
    language: "en"
  })

  const [privacy, setPrivacy] = useState({
    shareProgress: false,
    publicProfile: false,
    dataCollection: true
  })

  const { toast } = useToast()

  const handleSaveProfile = () => {
    toast({
      title: "Profile updated",
      description: "Your profile changes have been saved successfully."
    })
  }

  const handleSavePreferences = () => {
    toast({
      title: "Preferences updated", 
      description: "Your preferences have been saved successfully."
    })
  }

  const handleExportData = () => {
    toast({
      title: "Data export started",
      description: "We'll email you a download link when your data is ready."
    })
  }

  const handleDeleteAccount = () => {
    toast({
      title: "Account deletion requested",
      description: "Please check your email to confirm account deletion.",
      variant: "destructive"
    })
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account, preferences, and privacy settings
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Navigation */}
        <div className="space-y-2">
          <Card>
            <CardContent className="p-4">
              <nav className="space-y-1">
                <a href="#profile" className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary text-primary-foreground">
                  <User className="w-4 h-4" />
                  Profile
                </a>
                <a href="#notifications" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted">
                  <Bell className="w-4 h-4" />
                  Notifications
                </a>
                <a href="#privacy" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted">
                  <Shield className="w-4 h-4" />
                  Privacy
                </a>
                <a href="#account" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted">
                  <Key className="w-4 h-4" />
                  Account
                </a>
              </nav>
            </CardContent>
          </Card>
        </div>

        {/* Settings Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* Profile Settings */}
          <Card id="profile">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                Profile Information
              </CardTitle>
              <CardDescription>
                Update your personal information and profile settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 bg-gradient-primary rounded-full flex items-center justify-center">
                  <User className="w-10 h-10 text-primary-foreground" />
                </div>
                <div>
                  <Button variant="outline" size="sm">Change Avatar</Button>
                  <p className="text-sm text-muted-foreground mt-1">
                    Upload a profile picture
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="displayName">Display Name</Label>
                  <Input
                    id="displayName"
                    value={profile.displayName}
                    onChange={(e) => setProfile(prev => ({ ...prev, displayName: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile(prev => ({ ...prev, email: e.target.value }))}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Account Status</Label>
                    <p className="text-sm text-muted-foreground">Your current subscription plan</p>
                  </div>
                  <Badge variant="default">Free Plan</Badge>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Member Since</Label>
                    <p className="text-sm text-muted-foreground">January 2024</p>
                  </div>
                </div>
              </div>

              <Button onClick={handleSaveProfile} className="button-glow">
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </Button>
            </CardContent>
          </Card>

          {/* Notification Settings */}
          <Card id="notifications">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5" />
                Notification Preferences
              </CardTitle>
              <CardDescription>
                Choose how you want to be notified about your learning progress
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">
                      Receive updates via email
                    </p>
                  </div>
                  <Switch
                    checked={preferences.emailNotifications}
                    onCheckedChange={(checked) => 
                      setPreferences(prev => ({ ...prev, emailNotifications: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Push Notifications</Label>
                    <p className="text-sm text-muted-foreground">
                      Browser notifications for important updates
                    </p>
                  </div>
                  <Switch
                    checked={preferences.pushNotifications}
                    onCheckedChange={(checked) => 
                      setPreferences(prev => ({ ...prev, pushNotifications: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Weekly Digest</Label>
                    <p className="text-sm text-muted-foreground">
                      Summary of your learning progress
                    </p>
                  </div>
                  <Switch
                    checked={preferences.weeklyDigest}
                    onCheckedChange={(checked) => 
                      setPreferences(prev => ({ ...prev, weeklyDigest: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Study Reminders</Label>
                    <p className="text-sm text-muted-foreground">
                      Reminders to maintain your study streak
                    </p>
                  </div>
                  <Switch
                    checked={preferences.studyReminders}
                    onCheckedChange={(checked) => 
                      setPreferences(prev => ({ ...prev, studyReminders: checked }))
                    }
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Language</Label>
                  <select 
                    className="w-full p-2 border rounded-lg bg-background"
                    value={preferences.language}
                    onChange={(e) => setPreferences(prev => ({ ...prev, language: e.target.value }))}
                  >
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                    <option value="de">Deutsch</option>
                  </select>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Dark Mode</Label>
                    <p className="text-sm text-muted-foreground">
                      Use dark theme for better studying at night
                    </p>
                  </div>
                  <Switch
                    checked={preferences.darkMode}
                    onCheckedChange={(checked) => 
                      setPreferences(prev => ({ ...prev, darkMode: checked }))
                    }
                  />
                </div>
              </div>

              <Button onClick={handleSavePreferences}>
                <Save className="w-4 h-4 mr-2" />
                Save Preferences
              </Button>
            </CardContent>
          </Card>

          {/* Privacy Settings */}
          <Card id="privacy">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Privacy & Data
              </CardTitle>
              <CardDescription>
                Control your privacy settings and data usage
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Share Learning Progress</Label>
                    <p className="text-sm text-muted-foreground">
                      Allow others to see your study achievements
                    </p>
                  </div>
                  <Switch
                    checked={privacy.shareProgress}
                    onCheckedChange={(checked) => 
                      setPrivacy(prev => ({ ...prev, shareProgress: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Public Profile</Label>
                    <p className="text-sm text-muted-foreground">
                      Make your profile visible to other users
                    </p>
                  </div>
                  <Switch
                    checked={privacy.publicProfile}
                    onCheckedChange={(checked) => 
                      setPrivacy(prev => ({ ...prev, publicProfile: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Anonymous Usage Data</Label>
                    <p className="text-sm text-muted-foreground">
                      Help improve StudyRAG by sharing anonymous usage data
                    </p>
                  </div>
                  <Switch
                    checked={privacy.dataCollection}
                    onCheckedChange={(checked) => 
                      setPrivacy(prev => ({ ...prev, dataCollection: checked }))
                    }
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Account Management */}
          <Card id="account">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="w-5 h-5" />
                Account Management
              </CardTitle>
              <CardDescription>
                Manage your account settings and data
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <Label>Export Your Data</Label>
                    <p className="text-sm text-muted-foreground">
                      Download all your study data and progress
                    </p>
                  </div>
                  <Button variant="outline" onClick={handleExportData}>
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <Label>Change Password</Label>
                    <p className="text-sm text-muted-foreground">
                      Update your account password
                    </p>
                  </div>
                  <Button variant="outline">
                    <Key className="w-4 h-4 mr-2" />
                    Change
                  </Button>
                </div>

                <div className="flex items-center justify-between p-4 border border-destructive/50 rounded-lg bg-destructive/5">
                  <div>
                    <Label className="text-destructive">Delete Account</Label>
                    <p className="text-sm text-muted-foreground">
                      Permanently delete your account and all data
                    </p>
                  </div>
                  <Button variant="destructive" onClick={handleDeleteAccount}>
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}