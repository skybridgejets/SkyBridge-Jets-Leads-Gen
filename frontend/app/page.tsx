'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const LOCATIONS = [
  'London', 'Dubai', 'Monaco', 'Geneva', 'Riyadh', 'New York',
  'Paris', 'Zurich', 'Singapore', 'Hong Kong',
]

const PERSONAS = [
  'PA', 'EA', 'Chief of Staff', 'Estate Manager', 'Family Office',
  'Founder', 'CEO', 'Concierge Manager', 'Lifestyle Manager',
  'Yacht Broker', 'Luxury Travel Advisor', 'Real Estate Agent',
]

export default function NewSearch() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [selectedLocations, setSelectedLocations] = useState<string[]>([])
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>([])
  const [industry, setIndustry] = useState('')
  const [count, setCount] = useState(20)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const toggleItem = (item: string, list: string[], setter: (v: string[]) => void) => {
    if (list.includes(item)) {
      setter(list.filter((i) => i !== item))
    } else {
      setter([...list, item])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }
    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API_URL}/api/searches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          location: selectedLocations.join(', ') || null,
          persona: selectedPersonas.join(', ') || null,
          industry: industry || null,
          prospect_count: count,
        }),
      })

      if (!res.ok) throw new Error('Search creation failed')
      const data = await res.json()
      router.push(`/runs/${data.id}`)
    } catch (err) {
      setError('Failed to start search. Check that the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">New Search</h1>
        <p className="text-navy-400 mt-2">
          Enter a natural language query or use the structured fields below to find UHNW prospects.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <label className="block text-sm font-medium text-navy-300 mb-2">Search Query</label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Find 50 chiefs of staff, estate managers and luxury concierge contacts in London and Dubai who may manage UHNW travel"
            className="w-full h-28 resize-none"
          />
        </div>

        <div className="card">
          <label className="block text-sm font-medium text-navy-300 mb-3">Target Locations</label>
          <div className="flex flex-wrap gap-2">
            {LOCATIONS.map((loc) => (
              <button
                key={loc}
                type="button"
                onClick={() => toggleItem(loc, selectedLocations, setSelectedLocations)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                  selectedLocations.includes(loc)
                    ? 'bg-gold-500 text-navy-950 border-gold-500 font-medium'
                    : 'bg-navy-800 text-navy-300 border-navy-600 hover:border-navy-400'
                }`}
              >
                {loc}
              </button>
            ))}
          </div>
        </div>

        <div className="card">
          <label className="block text-sm font-medium text-navy-300 mb-3">Target Personas</label>
          <div className="flex flex-wrap gap-2">
            {PERSONAS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => toggleItem(p, selectedPersonas, setSelectedPersonas)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                  selectedPersonas.includes(p)
                    ? 'bg-gold-500 text-navy-950 border-gold-500 font-medium'
                    : 'bg-navy-800 text-navy-300 border-navy-600 hover:border-navy-400'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="card">
            <label className="block text-sm font-medium text-navy-300 mb-2">Industry Focus</label>
            <input
              type="text"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              placeholder="e.g., Luxury Travel, Aviation"
              className="w-full"
            />
          </div>
          <div className="card">
            <label className="block text-sm font-medium text-navy-300 mb-2">Number of Prospects</label>
            <input
              type="number"
              value={count}
              onChange={(e) => setCount(parseInt(e.target.value) || 20)}
              min={1}
              max={200}
              className="w-full"
            />
          </div>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-400 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <button type="submit" disabled={loading} className="btn-primary w-full text-lg py-3">
          {loading ? 'Starting Pipeline...' : 'Start Search'}
        </button>
      </form>
    </div>
  )
}
