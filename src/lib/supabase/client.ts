import { createBrowserClient } from '@supabase/ssr'
import { Database } from '@/integrations/supabase/types'

const SUPABASE_URL = "https://hnygdegntzuzwewcraye.supabase.co"
const SUPABASE_PUBLISHABLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhueWdkZWdudHp1endld2NyYXllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5MjgyMTUsImV4cCI6MjA3MjUwNDIxNX0.V-EwIDn-WcL9VA1BSIGwEOgMBtgFVch-GDjpIzA9SsU"

// Browser client for client-side operations
export const createClient = () =>
  createBrowserClient<Database>(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)

// Default client instance
export const supabase = createClient()

// Helper function to get current session on the client
export const getSession = async () => {
  const { data: { session }, error } = await supabase.auth.getSession()
  return { session, error }
}

// Helper function to get current user
export const getUser = async () => {
  const { data: { user }, error } = await supabase.auth.getUser()
  return { user, error }
}