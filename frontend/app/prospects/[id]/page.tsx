'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ProspectDetail {
  id: string
  full_name: string
  job_title: string
  company: string
  company_website: string
  location: string
  linkedin_url: string
  email: string
  email_verified: boolean
  source_url: string
  source_type: string
  score: {
    total: number
    breakdown: Record<string, number>
  } | null
  outreach: {
    linkedin_connection: string
    linkedin_followup: string
    email_subject: string
    email_body: string
    whatsapp_message: string
    personalisation_note: string
  } | null
  compliance: {
    data_source: string
    confidence_level: string
    email_verified: boolean
    source_type: string
    flags: string[]
  } | null
  enrichment_logs: {
    connector: string
    fields_added: string[]
    success: boolean
  }[]
}

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

const SCORE_LABELS: Record<string, string> = {
  title_family_office: 'Family Office title',
  title_chief_estate: 'Chief of Staff / Estate Manager',
  title_pa_ea: 'PA / EA title',
  title_concierge_lifestyle: 'Luxury Concierge / Lifestyle Manager',
  title_founder_ceo: 'Founder / CEO',
  uhnw_relevance: 'UHNW relevance signals',
  industry_match: 'Industry match (yacht/luxury/real estate)',
  location_match: 'Target location match',
  verified_email: 'Verified email present',
  weak_relevance: 'Weak relevance signals',
  no_role_fit: 'No clear role fit',
}

export default function ProspectDetailPage() {
  const params = useParams()
  const prospectId = params.id as string
  const [prospect, setProspect] = useState<ProspectDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchProspect = async () => {
      try {
        const res = await fetch(`${API_URL}/api/prospects/${prospectId}`)
        if (res.ok) setProspect(await res.json())
      } catch {
        console.error('Failed to fetch prospect')
      } finally {
        setLoading(false)
      }
    }
    fetchProspect()
  }, [prospectId])

  if (loading) return <div className="text-center py-12 text-navy-400">Loading...</div>
  if (!prospect) return <div className="text-center py-12 text-red-400">Prospect not found</div>

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-emerald-400'
    if (score >= 40) return 'text-gold-400'
    return 'text-red-400'
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">{prospect.full_name || 'Unknown'}</h1>
          <p className="text-navy-400 mt-1">
            {prospect.job_title}{prospect.company ? ` at ${prospect.company}` : ''}
          </p>
        </div>
        {prospect.score && (
          <div className="text-center">
            <div className={`text-4xl font-bold ${getScoreColor(prospect.score.total)}`}>
              {prospect.score.total}
            </div>
            <div className="text-xs text-navy-400">Lead Score</div>
          </div>
        )}
      </div>

      {/* Contact Info */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Contact Information</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-xs text-navy-400">Email</span>
            <p className="text-sm text-white flex items-center gap-2">
              {prospect.email || '—'}
              {prospect.email_verified && <span className="badge-success">Verified</span>}
            </p>
          </div>
          <div>
            <span className="text-xs text-navy-400">Location</span>
            <p className="text-sm text-white">{prospect.location || '—'}</p>
          </div>
          <div>
            <span className="text-xs text-navy-400">LinkedIn</span>
            <p className="text-sm">
              {prospect.linkedin_url ? (
                <a href={prospect.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-gold-400 hover:text-gold-300">
                  {prospect.linkedin_url}
                </a>
              ) : '—'}
            </p>
          </div>
          <div>
            <span className="text-xs text-navy-400">Company Website</span>
            <p className="text-sm">
              {prospect.company_website ? (
                <a href={prospect.company_website} target="_blank" rel="noopener noreferrer" className="text-gold-400 hover:text-gold-300">
                  {prospect.company_website}
                </a>
              ) : '—'}
            </p>
          </div>
        </div>
      </div>

      {/* Score Breakdown */}
      {prospect.score && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Score Breakdown</h2>
          <div className="space-y-2">
            {Object.entries(prospect.score.breakdown)
              .filter(([key]) => key !== 'total')
              .map(([key, points]) => (
                <div key={key} className="flex items-center justify-between py-1.5 border-b border-navy-800 last:border-0">
                  <span className="text-sm text-navy-300">{SCORE_LABELS[key] || key}</span>
                  <span className={`text-sm font-semibold ${points > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {points > 0 ? '+' : ''}{points}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Outreach Messages */}
      {prospect.outreach && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Outreach Messages</h2>

          {prospect.outreach.personalisation_note && (
            <div className="bg-gold-500/10 border border-gold-700/30 rounded-lg p-4 mb-4">
              <h3 className="text-xs font-medium text-gold-400 mb-1">Personalisation Note</h3>
              <p className="text-sm text-navy-200">{prospect.outreach.personalisation_note}</p>
            </div>
          )}

          <div className="space-y-4">
            {[
              { label: 'LinkedIn Connection Request', text: prospect.outreach.linkedin_connection },
              { label: 'LinkedIn Follow-up', text: prospect.outreach.linkedin_followup },
              { label: `Email — ${prospect.outreach.email_subject || 'Subject'}`, text: prospect.outreach.email_body },
              { label: 'WhatsApp Message', text: prospect.outreach.whatsapp_message },
            ].map((msg, i) => (
              <div key={i} className="bg-navy-800/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-medium text-navy-400">{msg.label}</h3>
                  <CopyButton text={msg.text || ''} />
                </div>
                <p className="text-sm text-navy-200 whitespace-pre-wrap">{msg.text || '—'}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Compliance */}
      {prospect.compliance && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Compliance Flags</h2>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <span className="text-xs text-navy-400">Data Source</span>
              <p className="text-sm text-white">{prospect.compliance.data_source}</p>
            </div>
            <div>
              <span className="text-xs text-navy-400">Confidence Level</span>
              <span className={`badge ${
                prospect.compliance.confidence_level === 'high' ? 'badge-success' :
                prospect.compliance.confidence_level === 'medium' ? 'badge-warning' : 'badge-danger'
              }`}>
                {prospect.compliance.confidence_level}
              </span>
            </div>
          </div>
          {prospect.compliance.flags && prospect.compliance.flags.length > 0 && (
            <div>
              <span className="text-xs text-navy-400">Flags</span>
              <div className="flex flex-wrap gap-2 mt-1">
                {prospect.compliance.flags.map((flag, i) => (
                  <span key={i} className="badge-warning">{flag}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
