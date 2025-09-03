import { supabase } from '@/lib/supabase/client'
import { Database } from '@/integrations/supabase/types'
import { uploadToStorage, getSignedUrl, deleteFromStorage } from '@/lib/storage'

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

  async upload(file: File) {
    const user = await supabase.auth.getUser()
    if (!user.data.user) throw new Error('Not authenticated')

    try {
      // Upload file to storage
      const uploadResult = await uploadToStorage(file, 'documents')
      
      // Create document record with storage information
      const documentData: DocumentInsert = {
        user_id: user.data.user.id,
        title: file.name.replace(/\.[^/.]+$/, ''), // Remove file extension
        filename: file.name,
        file_size: file.size,
        file_path: uploadResult.fullPath,
        status: 'uploaded'
      }

      const document = await this.create(documentData)
      
      return {
        document,
        uploadResult
      }
    } catch (error) {
      console.error('Document upload error:', error)
      throw error
    }
  },

  async delete(id: string) {
    // First get the document to get the file path
    const document = await this.get(id)
    
    // Delete from database
    const { error: dbError } = await supabase
      .from('documents')
      .delete()
      .eq('id', id)
    
    if (dbError) throw dbError

    // Delete from storage
    try {
      await deleteFromStorage(document.file_path, 'documents')
    } catch (storageError) {
      console.warn('Failed to delete file from storage:', storageError)
      // Don't throw here as database deletion was successful
    }
  },

  async getDownloadUrl(id: string) {
    const document = await this.get(id)
    const signedUrl = await getSignedUrl(document.file_path, 'documents', 3600) // 60 minutes
    return signedUrl
  },

  async rename(id: string, newTitle: string) {
    const { data, error } = await supabase
      .from('documents')
      .update({ title: newTitle })
      .eq('id', id)
      .select()
      .single()
    
    if (error) throw error
    return data
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

// RAG API
export const ragApi = {
  async *query(documentId: string, question: string): AsyncGenerator<{
    type: 'chunk' | 'sources' | 'done'
    content?: string
    sources?: Array<{ page: number; section: string; text: string; confidence: number }>
  }> {
    // Mock streaming implementation
    const chunks = [
      "This is a comprehensive analysis of your document...",
      " The key findings indicate several important patterns...",
      " Based on the evidence, we can conclude that..."
    ];
    
    const sources = [
      { page: 1, section: "Introduction", text: "Lorem ipsum dolor sit amet, consectetur adipiscing elit...", confidence: 0.95 },
      { page: 3, section: "Methodology", text: "Sed do eiusmod tempor incididunt ut labore et dolore magna...", confidence: 0.87 }
    ];
    
    // Simulate streaming chunks
    for (const chunk of chunks) {
      await new Promise(resolve => setTimeout(resolve, 800));
      yield { type: 'chunk', content: chunk };
    }
    
    // Send sources
    yield { type: 'sources', sources };
    
    // Signal completion
    yield { type: 'done' };
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