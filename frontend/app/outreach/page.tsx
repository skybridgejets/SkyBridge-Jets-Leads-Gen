'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ProspectOutreach {
  id: string
  full_name: string
  job_title: string
  company: string
  score: number | null
}

interface OutreachDetail {
  linkedin_connection: string
  linkedin_followup: string
  email_subject: string
  email_body: string
  whatsapp_message: string
  personalisation_note: string
}

type MessageType = 'linkedin' | 'email' | 'whatsapp'

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button
      onClick={handleCopy}
      className="text-xs px-2 py-1 rounded bg-navy-800 text-navy-300 hover:text-white border border-navy-600 hover:border-navy-400 transition-colors"
    >
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

export default function OutreachPage() {
  const [prospects, setProspects] = useState<ProspectOutreach[]>([])
  const [selectedProspect, setSelectedProspect] = useState<string | null>(null)
  const [outreach, setOutreach] = useState<OutreachDetail | null>(null)
  const [messageType, setMessageType] = useState<MessageType>('linkedin')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchProspects = async () => {
      try {
        const res = await fetch(`${API_URL}/api/prospects`)
        if (res.ok) {
          const data = await res.json()
          setProspects(data)
        }
      } catch {
        console.error('Failed to fetch prospects')
      } finally {
        setLoading(false)
      }
    }
    fetchProspects()
  }, [])

  const fetchOutreach = async (prospectId: string) => {
    setSelectedProspect(prospectId)
    try {
      const res = await fetch(`${API_URL}/api/outreach/${prospectId}`)
      if (res.ok) setOutreach(await res.json())
    } catch {
      console.error('Failed to fetch outreach')
    }
  }

  const getCurrentMessage = (): { label: string; text: string } => {
    if (!outreach) return { label: '', text: '' }
    switch (messageType) {
      case 'linkedin':
        return {
          label: 'LinkedIn Connection Request',
          text: outreach.linkedin_connection || '',
        }
      case 'email':
        return {
          label: `Email — ${outreach.email_subject || 'Subject'}`,
          text: outreach.email_body || '',
        }
      case 'whatsapp':
        return {
          label: 'WhatsApp Message',
          text: outreach.whatsapp_message || '',
        }
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Outreach Messages</h1>
        <p className="text-navy-400 mt-1">View and copy outreach messages for each prospect</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Prospect List */}
        <div className="col-span-1">
          <div className="card p-0 max-h-[70vh] overflow-y-auto">
            {loading ? (
              <div className="text-center py-8 text-navy-400">Loading...</div>
            ) : prospects.length === 0 ? (
              <div className="text-center py-8 text-navy-400">No prospects</div>
            ) : (
              prospects.map((p) => (
                <button
                  key={p.id}
                  onClick={() => fetchOutreach(p.id)}
                  className={`w-full text-left px-4 py-3 border-b border-navy-800 hover:bg-navy-800/50 transition-colors ${
                    selectedProspect === p.id ? 'bg-navy-800' : ''
                  }`}
                >
                  <p className="text-sm font-medium text-white truncate">{p.full_name || '—'}</p>
                  <p className="text-xs text-navy-400 truncate">{p.job_title} {p.company ? `at ${p.company}` : ''}</p>
                  {p.score !== null && (
                    <span className={`text-xs font-semibold ${
                      p.score >= 70 ? 'text-emerald-400' :
                      p.score >= 40 ? 'text-gold-400' : 'text-red-400'
                    }`}>
                      Score: {p.score}
                    </span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Message View */}
        <div className="col-span-2">
          {!selectedProspect ? (
            <div className="card text-center py-16 text-navy-400">
              Select a prospect to view outreach messages
            </div>
          ) : !outreach ? (
            <div className="card text-center py-16 text-navy-400">Loading messages...</div>
          ) : (
            <div className="space-y-4">
              {/* Message Type Toggle */}
              <div className="flex gap-2">
                {(['linkedin', 'email', 'whatsapp'] as MessageType[]).map((type) => (
                  <button
                    key={type}
                    onClick={() => setMessageType(type)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      messageType === type
                        ? 'bg-gold-500 text-navy-950'
                        : 'bg-navy-800 text-navy-300 hover:text-white border border-navy-600'
                    }`}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </button>
                ))}
              </div>

              {/* Current Message */}
              <div className="card">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-navy-400">{getCurrentMessage().label}</h3>
                  <CopyButton text={getCurrentMessage().text} />
                </div>
                <p className="text-sm text-navy-200 whitespace-pre-wrap">{getCurrentMessage().text || '—'}</p>
              </div>

              {/* LinkedIn Follow-up (shown when LinkedIn selected) */}
              {messageType === 'linkedin' && outreach.linkedin_followup && (
                <div className="card">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-navy-400">LinkedIn Follow-up</h3>
                    <CopyButton text={outreach.linkedin_followup} />
                  </div>
                  <p className="text-sm text-navy-200 whitespace-pre-wrap">{outreach.linkedin_followup}</p>
                </div>
              )}

              {/* Personalisation Note */}
              {outreach.personalisation_note && (
                <div className="bg-gold-500/10 border border-gold-700/30 rounded-lg p-4">
                  <h3 className="text-xs font-medium text-gold-400 mb-1">Personalisation Note</h3>
                  <p className="text-sm text-navy-200">{outreach.personalisation_note}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
