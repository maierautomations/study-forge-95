import { createServerClient } from '@supabase/ssr'
import { Database } from '@/integrations/supabase/types'

const SUPABASE_URL = "https://hnygdegntzuzwewcraye.supabase.co"
const SUPABASE_PUBLISHABLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhueWdkZWdudHp1endld2NyYXllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5MjgyMTUsImV4cCI6MjA3MjUwNDIxNX0.V-EwIDn-WcL9VA1BSIGwEOgMBtgFVch-GDjpIzA9SsU"

// Server client for server-side operations
export const createServerSupabaseClient = (request?: Request) => {
  // Create a server client with cookie handling
  const supabase = createServerClient<Database>(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY,
    {
      cookies: {
        get(name: string) {
          // In a real server environment, extract from request cookies
          if (typeof document !== 'undefined') {
            return document.cookie
              .split('; ')
              .find(row => row.startsWith(`${name}=`))
              ?.split('=')[1]
          }
          return undefined
        },
        set(name: string, value: string, options: any) {
          // In a real server environment, set response cookies
          if (typeof document !== 'undefined') {
            document.cookie = `${name}=${value}; ${Object.entries(options).map(([k, v]) => `${k}=${v}`).join('; ')}`
          }
        },
        remove(name: string, options: any) {
          // In a real server environment, remove cookies
          if (typeof document !== 'undefined') {
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; ${Object.entries(options).map(([k, v]) => `${k}=${v}`).join('; ')}`
          }
        },
      },
    }
  )

  return supabase
}

// Helper function to get session on server (for protected routes)
export const getServerSession = async (request?: Request) => {
  const supabase = createServerSupabaseClient(request)
  
  try {
    const { data: { session }, error } = await supabase.auth.getSession()
    return { session, error, supabase }
  } catch (error) {
    console.error('Error getting server session:', error)
    return { session: null, error, supabase }
  }
}

// Helper function to require authentication on server
export const requireAuth = async (request?: Request) => {
  const { session, error, supabase } = await getServerSession(request)
  
  if (!session || error) {
    throw new Error('Authentication required')
  }
  
  return { session, user: session.user, supabase }
}