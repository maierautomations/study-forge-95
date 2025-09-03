import { supabase } from '@/integrations/supabase/client'
import { Database } from '@/integrations/supabase/types'

export type Document = Database['public']['Tables']['documents']['Row']
export type DocumentInsert = Database['public']['Tables']['documents']['Insert']
export type ChatSession = Database['public']['Tables']['chat_sessions']['Row']
export type ChatMessage = Database['public']['Tables']['chat_messages']['Row']
export type QuizConfig = Database['public']['Tables']['quiz_configs']['Row']
export type QuizAttempt = Database['public']['Tables']['quiz_attempts']['Row']
export type Profile = Database['public']['Tables']['profiles']['Row']

// Document API
export const documentApi = {
  async list() {
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .order('upload_date', { ascending: false })
    
    if (error) throw error
    return data
  },

  async get(id: string) {
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .eq('id', id)
      .single()
    
    if (error) throw error
    return data
  },

  async create(document: DocumentInsert) {
    const { data, error } = await supabase
      .from('documents')
      .insert(document)
      .select()
      .single()
    
    if (error) throw error
    return data
  },

  async delete(id: string) {
    const { error } = await supabase
      .from('documents')
      .delete()
      .eq('id', id)
    
    if (error) throw error
  },

  async upload(file: File) {
    const user = await supabase.auth.getUser()
    if (!user.data.user) throw new Error('Not authenticated')

    const fileExt = file.name.split('.').pop()
    const fileName = `${Math.random().toString(36).substring(2)}.${fileExt}`
    const filePath = `${user.data.user.id}/${fileName}`

    const { error: uploadError } = await supabase.storage
      .from('documents')
      .upload(filePath, file)

    if (uploadError) throw uploadError

    // Create document record
    const documentData: DocumentInsert = {
      user_id: user.data.user.id,
      title: file.name.replace(/\.[^/.]+$/, ''),
      filename: file.name,
      file_size: file.size,
      file_path: filePath,
      status: 'uploaded'
    }

    return this.create(documentData)
  }
}

// Chat API
export const chatApi = {
  async getSessions(documentId: string) {
    const { data, error } = await supabase
      .from('chat_sessions')
      .select('*')
      .eq('document_id', documentId)
      .order('created_at', { ascending: false })
    
    if (error) throw error
    return data
  },

  async createSession(documentId: string, title?: string) {
    const user = await supabase.auth.getUser()
    if (!user.data.user) throw new Error('Not authenticated')

    const { data, error } = await supabase
      .from('chat_sessions')
      .insert({
        user_id: user.data.user.id,
        document_id: documentId,
        title: title || 'New Chat'
      })
      .select()
      .single()
    
    if (error) throw error
    return data
  },

  async getMessages(sessionId: string) {
    const { data, error } = await supabase
      .from('chat_messages')
      .select('*')
      .eq('session_id', sessionId)
      .order('timestamp', { ascending: true })
    
    if (error) throw error
    return data
  },

  async sendMessage(sessionId: string, content: string, role: 'user' | 'assistant', sources?: any) {
    const { data, error } = await supabase
      .from('chat_messages')
      .insert({
        session_id: sessionId,
        role,
        content,
        sources
      })
      .select()
      .single()
    
    if (error) throw error
    return data
  }
}

// Quiz API
export const quizApi = {
  async getConfigs(documentId: string) {
    const { data, error } = await supabase
      .from('quiz_configs')
      .select('*')
      .eq('document_id', documentId)
      .order('created_at', { ascending: false })
    
    if (error) throw error
    return data
  },

  async createConfig(config: Omit<Database['public']['Tables']['quiz_configs']['Insert'], 'user_id'>) {
    const user = await supabase.auth.getUser()
    if (!user.data.user) throw new Error('Not authenticated')

    const { data, error } = await supabase
      .from('quiz_configs')
      .insert({
        ...config,
        user_id: user.data.user.id
      })
      .select()
      .single()
    
    if (error) throw error
    return data
  },

  async getAttempts(userId?: string) {
    const { data, error } = await supabase
      .from('quiz_attempts')
      .select(`
        *,
        quiz_configs (
          title,
          documents (title)
        )
      `)
      .order('started_at', { ascending: false })
    
    if (error) throw error
    return data
  },

  async createAttempt(quizConfigId: string) {
    const user = await supabase.auth.getUser()
    if (!user.data.user) throw new Error('Not authenticated')

    const { data, error } = await supabase
      .from('quiz_attempts')
      .insert({
        user_id: user.data.user.id,
        quiz_config_id: quizConfigId
      })
      .select()
      .single()
    
    if (error) throw error
    return data
  }
}

// Profile API
export const profileApi = {
  async get() {
    const user = await supabase.auth.getUser()
    if (!user.data.user) throw new Error('Not authenticated')

    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('user_id', user.data.user.id)
      .single()
    
    if (error) throw error
    return data
  },

  async update(updates: Partial<Database['public']['Tables']['profiles']['Update']>) {
    const user = await supabase.auth.getUser()
    if (!user.data.user) throw new Error('Not authenticated')

    const { data, error } = await supabase
      .from('profiles')
      .update(updates)
      .eq('user_id', user.data.user.id)
      .select()
      .single()
    
    if (error) throw error
    return data
  }
}