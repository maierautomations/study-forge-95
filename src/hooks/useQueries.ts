import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentApi, chatApi, quizApi, profileApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

// Document queries
export const useDocuments = () => {
  return useQuery({
    queryKey: ['documents'],
    queryFn: documentApi.list
  })
}

export const useDocument = (id: string) => {
  return useQuery({
    queryKey: ['documents', id],
    queryFn: () => documentApi.get(id),
    enabled: !!id
  })
}

export const useUploadDocument = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: documentApi.upload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast({
        title: 'Document uploaded successfully!',
        description: 'Your document is now available in your library.'
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Upload failed',
        description: error.message,
        variant: 'destructive'
      })
    }
  })
}

// Chat queries
export const useChatSessions = (documentId: string) => {
  return useQuery({
    queryKey: ['chat-sessions', documentId],
    queryFn: () => chatApi.getSessions(documentId),
    enabled: !!documentId
  })
}

export const useChatMessages = (sessionId: string) => {
  return useQuery({
    queryKey: ['chat-messages', sessionId],
    queryFn: () => chatApi.getMessages(sessionId),
    enabled: !!sessionId
  })
}

export const useCreateChatSession = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ documentId, title }: { documentId: string; title?: string }) =>
      chatApi.createSession(documentId, title),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
    }
  })
}

export const useSendMessage = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, content, role, sources }: {
      sessionId: string
      content: string
      role: 'user' | 'assistant'
      sources?: any
    }) => chatApi.sendMessage(sessionId, content, role, sources),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['chat-messages', data.session_id] })
    }
  })
}

// Quiz queries
export const useQuizConfigs = (documentId: string) => {
  return useQuery({
    queryKey: ['quiz-configs', documentId],
    queryFn: () => quizApi.getConfigs(documentId),
    enabled: !!documentId
  })
}

export const useQuizAttempts = () => {
  return useQuery({
    queryKey: ['quiz-attempts'],
    queryFn: () => quizApi.getAttempts()
  })
}

export const useCreateQuizConfig = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: quizApi.createConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quiz-configs'] })
      toast({
        title: 'Quiz created successfully!',
        description: 'Your quiz configuration has been saved.'
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to create quiz',
        description: error.message,
        variant: 'destructive'
      })
    }
  })
}

// Profile queries
export const useProfile = () => {
  return useQuery({
    queryKey: ['profile'],
    queryFn: profileApi.get
  })
}

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: profileApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      toast({
        title: 'Profile updated successfully!',
        description: 'Your changes have been saved.'
      })
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to update profile',
        description: error.message,
        variant: 'destructive'
      })
    }
  })
}