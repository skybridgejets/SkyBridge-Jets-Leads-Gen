'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface SearchRun {
  id: string
  query: string
  status: string
  actual_prospects: number
  created_at: string | null
}

export default function ExportPage() {
  const [searches, setSearches] = useState<SearchRun[]>([])
  const [selectedSearch, setSelectedSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    const fetchSearches = async () => {
      try {
        const res = await fetch(`${API_URL}/api/searches`)
        if (res.ok) {
          const allSearches = await res.json()
          setSearches(allSearches.filter((s: SearchRun) => s.status === 'complete'))
        }
      } catch {
        console.error('Failed to fetch searches')
      } finally {
        setLoading(false)
      }
    }
    fetchSearches()
  }, [])

  const handleDownload = async () => {
    if (!selectedSearch) return
    setDownloading(true)
    try {
      const res = await fetch(`${API_URL}/api/export/${selectedSearch}`)
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `skybridge_prospects_${selectedSearch}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      console.error('Download failed')
    } finally {
      setDownloading(false)
    }
  }

  const selected = searches.find((s) => s.id === selectedSearch)

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Export Results</h1>
        <p className="text-navy-400 mt-1">Download prospect data as CSV</p>
      </div>

      <div className="card space-y-6">
        <div>
          <label className="block text-sm font-medium text-navy-300 mb-2">Select Search Run</label>
          {loading ? (
            <p className="text-navy-400 text-sm">Loading searches...</p>
          ) : searches.length === 0 ? (
            <p className="text-navy-400 text-sm">No completed searches found. Run a search first.</p>
          ) : (
            <select
              value={selectedSearch}
              onChange={(e) => setSelectedSearch(e.target.value)}
              className="w-full"
            >
              <option value="">Choose a search run...</option>
              {searches.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.query?.slice(0, 60) || 'Untitled'} — {s.actual_prospects} prospects
                  {s.created_at ? ` (${new Date(s.created_at).toLocaleDateString()})` : ''}
                </option>
              ))}
            </select>
          )}
        </div>

        {selected && (
          <div className="bg-navy-800/50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-white mb-2">Export Preview</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-navy-400">Query:</span>
                <p className="text-navy-200 truncate">{selected.query}</p>
              </div>
              <div>
                <span className="text-navy-400">Status:</span>
                <p className="text-navy-200">{selected.status}</p>
              </div>
              <div>
                <span className="text-navy-400">Prospects:</span>
                <p className="text-navy-200">{selected.actual_prospects}</p>
              </div>
              <div>
                <span className="text-navy-400">Created:</span>
                <p className="text-navy-200">
                  {selected.created_at ? new Date(selected.created_at).toLocaleString() : '—'}
                </p>
              </div>
            </div>
            <p className="text-xs text-navy-500 mt-3">
              CSV includes: Name, Title, Company, Location, Email, LinkedIn URL, Score,
              Score Breakdown, Personalisation Note, All Messages, Compliance Flags
            </p>
          </div>
        )}

        <button
          onClick={handleDownload}
          disabled={!selectedSearch || downloading}
          className="btn-primary w-full"
        >
          {downloading ? 'Downloading...' : 'Download CSV'}
        </button>
      </div>
    </div>
  )
}
