/**
 * Project Management Types
 */

export interface Project {
  id: string
  name: string
  path: string
  rootPath: string
  createdAt: string
  lastOpened: string
  type?: 'node' | 'python' | 'rust' | 'mixed'
  isGitRepo?: boolean
}

export interface ProjectResponse {
  success: boolean
  data?: Project
  error?: string
}

export interface ProjectsListResponse {
  success: boolean
  recent?: Project[]
  error?: string
}

export interface ProjectState {
  current: Project | null
  loading: boolean
  error: string | null
  isEmpty: boolean
}

export interface CreateProjectRequest {
  name: string
  parentPath: string
  template?: 'empty' | 'node' | 'python'
}

export interface OpenProjectRequest {
  path: string
}
