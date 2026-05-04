'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface AgentRun {
  id: string
  agent_name: string
  status: string
  started_at: string | null
  completed_at: string | null
  output_summary: string | null
  error_message: string | null
}

interface SearchData {
  id: string
  query: string
  location: string | null
  persona: string | null
  industry: string | null
  status: string
  actual_prospects: number
}

const AGENT_LABELS: Record<string, string> = {
  source_finder: 'Source Finder',
  prospect_discovery: 'Prospect Discovery',
  data_extraction: 'Data Extraction',
  enrichment: 'Enrichment',
  deduplication: 'Deduplication',
  scoring: 'Scoring',
  outreach: 'Outreach',
  compliance: 'Compliance',
}

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-navy-800 text-navy-400 border-navy-600',
  running: 'bg-blue-900/50 text-blue-400 border-blue-700 animate-pulse',
  complete: 'bg-emerald-900/50 text-emerald-400 border-emerald-700',
  failed: 'bg-red-900/50 text-red-400 border-red-700',
}

export default function RunStatus() {
  const params = useParams()
  const searchId = params.id as string
  const [search, setSearch] = useState<SearchData | null>(null)
  const [runs, setRuns] = useState<AgentRun[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [searchRes, runsRes] = await Promise.all([
          fetch(`${API_URL}/api/searches/${searchId}`),
          fetch(`${API_URL}/api/searches/${searchId}/runs`),
        ])
        if (searchRes.ok) setSearch(await searchRes.json())
        if (runsRes.ok) setRuns(await runsRes.json())
      } catch {
        setError('Failed to fetch run status')
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [searchId])

  const isComplete = search?.status === 'complete' || search?.status === 'failed'

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Agent Run Status</h1>
        {search && (
          <p className="text-navy-400 mt-2 truncate">Query: {search.query}</p>
        )}
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 text-red-400 px-4 py-3 rounded-lg text-sm mb-6">
          {error}
        </div>
      )}

      {search && (
        <div className="card mb-6 flex items-center justify-between">
          <div>
            <span className="text-sm text-navy-400">Pipeline Status</span>
            <div className="flex items-center gap-3 mt-1">
              <span className={`badge ${
                search.status === 'complete' ? 'badge-success' :
                search.status === 'failed' ? 'badge-danger' :
                search.status === 'running' ? 'badge-info' : 'badge-neutral'
              }`}>
                {search.status}
              </span>
              {search.actual_prospects > 0 && (
                <span className="text-sm text-navy-300">
                  {search.actual_prospects} prospects found
                </span>
              )}
            </div>
          </div>
          {isComplete && search.actual_prospects > 0 && (
            <a href={`/prospects?search_id=${searchId}`} className="btn-primary text-sm">
              View Prospects
            </a>
          )}
        </div>
      )}

      <div className="space-y-3">
        {runs.length > 0 ? (
          runs.map((run) => (
            <div key={run.id} className="card flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-3 h-3 rounded-full ${
                  run.status === 'complete' ? 'bg-emerald-400' :
                  run.status === 'failed' ? 'bg-red-400' :
                  run.status === 'running' ? 'bg-blue-400 animate-pulse' :
                  'bg-navy-600'
                }`} />
                <div>
                  <p className="font-medium text-white">
                    {AGENT_LABELS[run.agent_name] || run.agent_name}
                  </p>
                  {run.output_summary && (
                    <p className="text-xs text-navy-400 mt-0.5">{run.output_summary}</p>
                  )}
                  {run.error_message && (
                    <p className="text-xs text-red-400 mt-0.5">{run.error_message}</p>
                  )}
                </div>
              </div>
              <span className={`badge border ${STATUS_STYLES[run.status] || STATUS_STYLES.pending}`}>
                {run.status}
              </span>
            </div>
          ))
        ) : (
          <div className="card text-center text-navy-400 py-12">
            {search?.status === 'pending' ? 'Pipeline starting...' : 'Waiting for agent runs...'}
          </div>
        )}
      </div>

      {!isComplete && (
        <p className="text-center text-navy-500 text-sm mt-6">Auto-refreshing every 5 seconds</p>
      )}
    </div>
  )
}
