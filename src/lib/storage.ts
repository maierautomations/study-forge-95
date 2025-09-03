import { supabase } from '@/integrations/supabase/client'

export interface StorageUploadResult {
  path: string
  fullPath: string
  publicUrl?: string
}

export interface FileMetadata {
  name: string
  size: number
  type: string
  lastModified: number
}

// Upload file to Supabase Storage with user folder structure
export const uploadToStorage = async (
  file: File,
  bucket: string = 'documents',
  folder?: string
): Promise<StorageUploadResult> => {
  const user = await supabase.auth.getUser()
  if (!user.data.user) {
    throw new Error('User not authenticated')
  }

  // Create file path with user folder structure
  const fileExt = file.name.split('.').pop()
  const fileName = `${Date.now()}-${Math.random().toString(36).substring(2)}.${fileExt}`
  const userFolder = user.data.user.id
  const filePath = folder 
    ? `${userFolder}/${folder}/${fileName}`
    : `${userFolder}/${fileName}`

  // Upload file to storage
  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(filePath, file, {
      cacheControl: '3600',
      upsert: false
    })

  if (error) {
    console.error('Storage upload error:', error)
    throw new Error(`Upload failed: ${error.message}`)
  }

  const fullPath = data.path

  return {
    path: filePath,
    fullPath,
  }
}

// Generate signed URL for secure file access (valid for 60 minutes)
export const getSignedUrl = async (
  filePath: string,
  bucket: string = 'documents',
  expiresIn: number = 3600 // 60 minutes in seconds
): Promise<string> => {
  const { data, error } = await supabase.storage
    .from(bucket)
    .createSignedUrl(filePath, expiresIn)

  if (error) {
    console.error('Error creating signed URL:', error)
    throw new Error(`Failed to create download URL: ${error.message}`)
  }

  if (!data?.signedUrl) {
    throw new Error('No signed URL returned')
  }

  return data.signedUrl
}

// Get public URL for file (if bucket is public)
export const getPublicUrl = (
  filePath: string,
  bucket: string = 'documents'
): string => {
  const { data } = supabase.storage
    .from(bucket)
    .getPublicUrl(filePath)

  return data.publicUrl
}

// Delete file from storage
export const deleteFromStorage = async (
  filePath: string,
  bucket: string = 'documents'
): Promise<void> => {
  const { error } = await supabase.storage
    .from(bucket)
    .remove([filePath])

  if (error) {
    console.error('Storage delete error:', error)
    throw new Error(`Delete failed: ${error.message}`)
  }
}

// List files in user's folder
export const listUserFiles = async (
  bucket: string = 'documents',
  folder?: string
): Promise<any[]> => {
  const user = await supabase.auth.getUser()
  if (!user.data.user) {
    throw new Error('User not authenticated')
  }

  const userFolder = user.data.user.id
  const searchPath = folder ? `${userFolder}/${folder}` : userFolder

  const { data, error } = await supabase.storage
    .from(bucket)
    .list(searchPath)

  if (error) {
    console.error('Storage list error:', error)
    throw new Error(`Failed to list files: ${error.message}`)
  }

  return data || []
}

// Get file metadata
export const getFileMetadata = async (
  filePath: string,
  bucket: string = 'documents'
): Promise<any> => {
  const { data, error } = await supabase.storage
    .from(bucket)
    .list('', {
      search: filePath
    })

  if (error) {
    console.error('Error getting file metadata:', error)
    throw new Error(`Failed to get file metadata: ${error.message}`)
  }

  return data?.[0] || null
}

// Helper function to get file icon based on mime type
export const getFileIcon = (mimeType: string): string => {
  if (mimeType.includes('pdf')) return '📄'
  if (mimeType.includes('word') || mimeType.includes('document')) return '📝'
  if (mimeType.includes('text')) return '📃'
  if (mimeType.includes('image')) return '🖼️'
  if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return '📊'
  if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) return '📊'
  return '📁'
}

// Helper function to format file size
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}