/**
 * Project Context for managing current project state across the app
 */

import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react'
import axios from 'axios'
import { Project, ProjectState } from '../types/project'

const PROJECT_STORAGE_KEY = 'kicli_current_project'

interface ProjectContextType extends ProjectState {
  openProject: (path: string) => Promise<void>
  createProject: (name: string, parentPath: string, template?: string) => Promise<void>
  closeProject: () => void
  getRecentProjects: () => Promise<Project[]>
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined)

export const ProjectProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<ProjectState>(() => {
    // Load from localStorage on init
    try {
      const stored = localStorage.getItem(PROJECT_STORAGE_KEY)
      if (stored) {
        const project = JSON.parse(stored)
        return {
          current: project,
          loading: false,
          error: null,
          isEmpty: false,
        }
      }
    } catch (e) {
      console.error('Failed to load project from storage:', e)
    }
    
    return {
      current: null,
      loading: false,
      error: null,
      isEmpty: true,
    }
  })

  // Persist to localStorage on change
  useEffect(() => {
    if (state.current) {
      localStorage.setItem(PROJECT_STORAGE_KEY, JSON.stringify(state.current))
    } else {
      localStorage.removeItem(PROJECT_STORAGE_KEY)
    }
  }, [state.current])

  const openProject = useCallback(async (path: string) => {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      const res = await axios.post('/api/projects/open', { path })
      if (res.data.success) {
        setState(s => ({
          ...s,
          current: res.data.data,
          isEmpty: false,
          loading: false,
        }))
      } else {
        throw new Error(res.data.error || 'Failed to open project')
      }
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Failed to open project'
      setState(s => ({ ...s, error, loading: false }))
      throw err
    }
  }, [])

  const createProject = useCallback(async (name: string, parentPath: string, template = 'empty') => {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      const res = await axios.post('/api/projects/create', {
        name,
        parentPath,
        template,
      })
      if (res.data.success) {
        setState(s => ({
          ...s,
          current: res.data.data,
          isEmpty: false,
          loading: false,
        }))
      } else {
        throw new Error(res.data.error || 'Failed to create project')
      }
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Failed to create project'
      setState(s => ({ ...s, error, loading: false }))
      throw err
    }
  }, [])

  const closeProject = useCallback(() => {
    setState({
      current: null,
      loading: false,
      error: null,
      isEmpty: true,
    })
  }, [])

  const getRecentProjects = useCallback(async (): Promise<Project[]> => {
    try {
      const res = await axios.get('/api/projects/recent')
      return res.data.recent || []
    } catch {
      return []
    }
  }, [])

  return (
    <ProjectContext.Provider
      value={{
        ...state,
        openProject,
        createProject,
        closeProject,
        getRecentProjects,
      }}
    >
      {children}
    </ProjectContext.Provider>
  )
}

export const useProject = () => {
  const context = useContext(ProjectContext)
  if (!context) {
    throw new Error('useProject must be used within ProjectProvider')
  }
  return context
}
