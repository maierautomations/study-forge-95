// FastAPI Backend API Client
import type { components } from './api/generated'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Type aliases for cleaner usage
export type Document = components['schemas']['DocumentListItem']
export type DocumentUploadResponse = components['schemas']['IngestResponse']
export type DocumentStatusResponse = components['schemas']['DocumentStatusResponse']
export type DocumentListResponse = components['schemas']['DocumentListResponse']
export type ChatSession = components['schemas']['ChatSession']
export type ChatMessage = components['schemas']['ChatMessage']
export type QuizConfig = components['schemas']['QuizConfig']
export type QuizAttempt = components['schemas']['QuizAttempt'] // Will be defined in backend
export type Profile = components['schemas']['ProfileResponse']
export type ProfileUpdateRequest = components['schemas']['ProfileUpdateRequest']
export type RagQuery = components['schemas']['RagQuery']
export type RagResponse = components['schemas']['RagResponse']
export type SearchQuery = components['schemas']['SearchQuery']
export type SearchResponse = components['schemas']['SearchResponse']

// API Client with authentication
class ApiClient {
  private async getHeaders() {
    // Get JWT token from Supabase Auth
    const { supabase } = await import('@/integrations/supabase/client')
    const { data: { session } } = await supabase.auth.getSession()

    return {
      'Content-Type': 'application/json',
      'Authorization': session?.access_token ? `Bearer ${session.access_token}` : '',
    }
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    const headers = await this.getHeaders()

    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }
}

const apiClient = new ApiClient()

// Document API - Now calls FastAPI backend
export const documentApi = {
  async list(): Promise<Document[]> {
    const response = await apiClient.request<DocumentListResponse>('/api/v1/docs')
    return response.documents
  },

  async get(id: string): Promise<Document> {
    return apiClient.request<Document>(`/api/v1/docs/${id}`)
  },

  async getStatus(id: string): Promise<DocumentStatusResponse> {
    return apiClient.request<DocumentStatusResponse>(`/api/v1/docs/status?documentId=${id}`)
  },

  async upload(file: File): Promise<DocumentUploadResponse> {
    // First upload to Supabase Storage
    const { supabase } = await import('@/integrations/supabase/client')
    const user = await supabase.auth.getUser()
    if (!user.data.user) throw new Error('Not authenticated')

    const fileExt = file.name.split('.').pop()
    const fileName = `${Math.random().toString(36).substring(2)}.${fileExt}`
    const filePath = `${user.data.user.id}/${fileName}`

    const { error: uploadError } = await supabase.storage
      .from('documents')
      .upload(filePath, file)

    if (uploadError) throw uploadError

    // Then call FastAPI to start ingestion
    const requestBody = {
      documentId: crypto.randomUUID(),
      storagePath: filePath,
      mime: file.type || 'application/octet-stream'
    }

    return apiClient.request<DocumentUploadResponse>('/api/v1/docs/ingest', {
      method: 'POST',
      body: JSON.stringify(requestBody)
    })
  },

  async delete(id: string): Promise<void> {
    await apiClient.request(`/api/v1/docs/${id}`, {
      method: 'DELETE'
    })
  }
}

// Chat API - Now calls FastAPI backend
export const chatApi = {
  async getSessions(documentId: string): Promise<ChatSession[]> {
    return apiClient.request<ChatSession[]>(`/api/v1/rag/sessions?documentId=${documentId}`)
  },

  async createSession(documentId: string, title?: string): Promise<ChatSession> {
    return apiClient.request<ChatSession>('/api/v1/rag/sessions', {
      method: 'POST',
      body: JSON.stringify({ documentId, title })
    })
  },

  async getMessages(sessionId: string): Promise<ChatMessage[]> {
    return apiClient.request<ChatMessage[]>(`/api/v1/rag/messages?sessionId=${sessionId}`)
  },

  async sendMessage(sessionId: string, content: string, role: 'user' | 'assistant', sources?: any): Promise<ChatMessage> {
    return apiClient.request<ChatMessage>('/api/v1/rag/messages', {
      method: 'POST',
      body: JSON.stringify({ sessionId, content, role, sources })
    })
  }
}

// Quiz API - Now calls FastAPI backend
export const quizApi = {
  async getConfigs(documentId: string): Promise<QuizConfig[]> {
    return apiClient.request<QuizConfig[]>(`/api/v1/quiz/configs?documentId=${documentId}`)
  },

  async createConfig(config: any): Promise<QuizConfig> {
    return apiClient.request<QuizConfig>('/api/v1/quiz/configs', {
      method: 'POST',
      body: JSON.stringify(config)
    })
  },

  async getAttempts(): Promise<QuizAttempt[]> {
    return apiClient.request<QuizAttempt[]>('/api/v1/quiz/attempts')
  },

  async createAttempt(quizConfigId: string): Promise<QuizAttempt> {
    return apiClient.request<QuizAttempt>('/api/v1/quiz/attempts', {
      method: 'POST',
      body: JSON.stringify({ quizConfigId })
    })
  },

  async generateQuiz(documentId: string, config: any) {
    return apiClient.request('/api/v1/quiz/generate', {
      method: 'POST',
      body: JSON.stringify({ documentId, config })
    })
  },

  async submitQuiz(quizId: string, answers: any) {
    return apiClient.request('/api/v1/quiz/submit', {
      method: 'POST',
      body: JSON.stringify({ quizId, answers })
    })
  }
}

// Profile API - Now calls FastAPI backend
export const profileApi = {
  async get(): Promise<Profile> {
    return apiClient.request<Profile>('/api/v1/profile')
  },

  async update(updates: Partial<Profile>): Promise<Profile> {
    return apiClient.request<Profile>('/api/v1/profile', {
      method: 'PUT',
      body: JSON.stringify(updates)
    })
  }
}