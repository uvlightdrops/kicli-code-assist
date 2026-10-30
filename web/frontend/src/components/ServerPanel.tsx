import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { useProject } from '../hooks/useProject'

interface StackService {
  name: string
  kind: string
  status: 'running' | 'unhealthy' | 'stopped' | 'foreign'
  pid?: number
  host?: string
  port?: number
  url?: string
  managed?: boolean
  log_file?: string | null
}

interface KnownProject {
  name: string
  path: string
}

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) return error.response?.data?.error || error.message
  return error instanceof Error ? error.message : 'Server request failed'
}

function ProjectServices({ project }: { project: string }) {
  const [services, setServices] = useState<StackService[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [logs, setLogs] = useState('')
  const active = useRef(true)

  const refresh = async (signal?: AbortSignal) => {
    const response = await axios.get('/api/server/status', {
      params: { project }, timeout: 20000, signal,
    })
    if (active.current) setServices(response.data.services)
  }

  useEffect(() => {
    active.current = true
    const controller = new AbortController()
    setBusy(true)
    refresh(controller.signal)
      .catch(error => { if (!controller.signal.aborted) setError(errorMessage(error)) })
      .finally(() => { if (active.current) setBusy(false) })
    return () => { active.current = false; controller.abort() }
  }, [project])

  const perform = async (action: 'start' | 'stop' | 'restart' | 'logs' | 'status', service?: string) => {
    setBusy(true)
    setError('')
    try {
      if (action === 'logs') {
        const response = await axios.get('/api/server/logs', {
          params: { project, ...(service ? { service } : {}) }, timeout: 40000,
        })
        if (active.current) setLogs(JSON.stringify(response.data, null, 2))
      } else {
        if (action !== 'status') {
          await axios.post(`/api/server/${action}`, {
            project, services: service ? [service] : [],
          }, { timeout: 110000 })
        }
        if (active.current) await refresh()
      }
    } catch (error) {
      if (active.current) setError(errorMessage(error))
    } finally {
      if (active.current) setBusy(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {(['status', 'start', 'stop', 'restart', 'logs'] as const).map(action => (
          <button key={action} disabled={busy} onClick={() => perform(action)}
            className="px-2 py-1 bg-gray-700 rounded disabled:opacity-40">
            {action === 'status' ? 'Refresh' : `${action} all`}
          </button>
        ))}
      </div>
      {busy && <p role="status">Waiting for stackctl…</p>}
      {error && <p role="alert" className="text-red-400 whitespace-pre-wrap">{error}</p>}
      {!busy && !services.length && <p>No stackctl services available.</p>}
      {services.map(service => (
        <div key={service.name} className="border border-gray-700 rounded p-3 space-y-2">
          <p><strong>{service.name}</strong> — {service.status} ({service.kind})</p>
          <p className="text-xs text-gray-400">
            PID: {service.pid ?? '—'} · {service.host || '—'}:{service.port ?? '—'}
            {' · '}{service.managed ? 'managed' : 'not managed'}
          </p>
          {service.url && /^https?:\/\//.test(service.url) && (
            <a className="text-blue-400" href={service.url} target="_blank" rel="noreferrer">{service.url}</a>
          )}
          {service.log_file && <p className="text-xs break-all">{service.log_file}</p>}
          <div className="flex gap-2">
            {(['start', 'stop', 'restart', 'logs'] as const).map(action => (
              <button key={action} disabled={busy || (service.status === 'foreign' && action !== 'logs') || (!service.managed && action !== 'start')}
                onClick={() => perform(action, service.name)}
                className="px-2 py-1 bg-gray-700 rounded disabled:opacity-40">{action}</button>
            ))}
          </div>
        </div>
      ))}
      {logs && <pre className="text-xs overflow-auto max-h-80 whitespace-pre-wrap" aria-label="Project logs">{logs}</pre>}
    </div>
  )
}

export function ServerPanel() {
  const { current } = useProject()
  const [projects, setProjects] = useState<KnownProject[]>([])
  const [selected, setSelected] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    axios.get('/api/server/projects', { signal: controller.signal, timeout: 20000 })
      .then(response => {
        const known: KnownProject[] = response.data.projects
        setProjects(known)
        setSelected(known.some(project => project.path === current?.path) ? current!.path : '')
      })
      .catch(error => { if (!controller.signal.aborted) setError(errorMessage(error)) })
    return () => controller.abort()
  }, [current?.path])

  return (
    <section className="space-y-3 text-sm text-gray-200">
      <h3 className="font-semibold">Project services (stackctl)</h3>
      <p className="text-xs text-gray-400">Live status and lifecycle belong to each project's stackctl, not the legacy PID registry.</p>
      {error && <p role="alert">{error}</p>}
      <label className="block">
        Registered project
        <select value={selected} onChange={event => setSelected(event.target.value)}
          className="block w-full bg-gray-800 p-2 rounded mt-1">
          <option value="">Select a project</option>
          {projects.map(project => <option key={project.path} value={project.path}>{project.name} — {project.path}</option>)}
        </select>
      </label>
      {selected && <ProjectServices key={selected} project={selected} />}
    </section>
  )
}
