'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Prospect {
  id: string
  full_name: string
  job_title: string
  company: string
  location: string
  email: string
  email_verified: boolean
  source_type: string
  score: number | null
}

function ProspectsContent() {
  const searchParams = useSearchParams()
  const searchId = searchParams.get('search_id')
  const [prospects, setProspects] = useState<Prospect[]>([])
  const [loading, setLoading] = useState(true)
  const [scoreMin, setScoreMin] = useState('')
  const [locationFilter, setLocationFilter] = useState('')
  const [personaFilter, setPersonaFilter] = useState('')

  const fetchProspects = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (searchId) params.set('search_id', searchId)
      if (scoreMin) params.set('score_min', scoreMin)
      if (locationFilter) params.set('location', locationFilter)
      if (personaFilter) params.set('persona', personaFilter)

      const res = await fetch(`${API_URL}/api/prospects?${params}`)
      if (res.ok) setProspects(await res.json())
    } catch {
      console.error('Failed to fetch prospects')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchProspects() }, [searchId])

  const getScoreColor = (score: number | null) => {
    if (!score) return 'text-navy-500'
    if (score >= 70) return 'text-emerald-400'
    if (score >= 40) return 'text-gold-400'
    return 'text-red-400'
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Ranked Prospects</h1>
          <p className="text-navy-400 mt-1">{prospects.length} prospects found</p>
        </div>
      </div>

      <div className="card mb-6">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-navy-400 mb-1">Min Score</label>
            <input
              type="number"
              value={scoreMin}
              onChange={(e) => setScoreMin(e.target.value)}
              placeholder="0"
              className="w-full text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-navy-400 mb-1">Location</label>
            <input
              type="text"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              placeholder="e.g., London"
              className="w-full text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-navy-400 mb-1">Persona</label>
            <input
              type="text"
              value={personaFilter}
              onChange={(e) => setPersonaFilter(e.target.value)}
              placeholder="e.g., Chief of Staff"
              className="w-full text-sm"
            />
          </div>
          <div className="flex items-end">
            <button onClick={fetchProspects} className="btn-primary w-full text-sm">
              Apply Filters
            </button>
          </div>
        </div>
      </div>

      <div className="card overflow-hidden p-0">
        <table className="w-full">
          <thead>
            <tr className="border-b border-navy-700 bg-navy-900/50">
              <th className="text-left px-4 py-3 text-xs font-medium text-navy-400 uppercase tracking-wider">Name</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-navy-400 uppercase tracking-wider">Title</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-navy-400 uppercase tracking-wider">Company</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-navy-400 uppercase tracking-wider">Location</th>
              <th className="text-center px-4 py-3 text-xs font-medium text-navy-400 uppercase tracking-wider">Score</th>
              <th className="text-center px-4 py-3 text-xs font-medium text-navy-400 uppercase tracking-wider">Email</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-navy-400 uppercase tracking-wider">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-800">
            {loading ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-navy-400">Loading...</td>
              </tr>
            ) : prospects.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-navy-400">No prospects found</td>
              </tr>
            ) : (
              prospects.map((p) => (
                <tr
                  key={p.id}
                  className="hover:bg-navy-800/50 cursor-pointer transition-colors"
                  onClick={() => window.location.href = `/prospects/${p.id}`}
                >
                  <td className="px-4 py-3 text-sm font-medium text-white">{p.full_name || '—'}</td>
                  <td className="px-4 py-3 text-sm text-navy-300">{p.job_title || '—'}</td>
                  <td className="px-4 py-3 text-sm text-navy-300">{p.company || '—'}</td>
                  <td className="px-4 py-3 text-sm text-navy-300">{p.location || '—'}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-sm font-bold ${getScoreColor(p.score)}`}>
                      {p.score ?? '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {p.email ? (
                      <span className={p.email_verified ? 'badge-success' : 'badge-warning'}>
                        {p.email_verified ? 'Verified' : 'Unverified'}
                      </span>
                    ) : (
                      <span className="badge-neutral">None</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-navy-400">{p.source_type || '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function Prospects() {
  return (
    <Suspense fallback={<div className="text-center py-12 text-navy-400">Loading...</div>}>
      <ProspectsContent />
    </Suspense>
  )
}
