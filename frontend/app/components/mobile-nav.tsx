'use client'

import { useState } from 'react'

interface NavItem {
  href: string
  label: string
  icon: string
}

export function MobileNav({ navItems }: { navItems: NavItem[] }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="lg:hidden">
      <header className="flex items-center justify-between px-4 py-3 border-b border-navy-800 bg-navy-950">
        <h1 className="text-lg font-bold text-gold-400 tracking-tight">SkyBridge Jets</h1>
        <button
          onClick={() => setOpen(!open)}
          className="p-2 rounded-lg text-navy-300 hover:text-white hover:bg-navy-800 transition-colors"
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            {open ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </header>

      {open && (
        <nav className="px-4 py-3 border-b border-navy-800 bg-navy-950 space-y-1">
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-navy-300 hover:text-white hover:bg-navy-800 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
              </svg>
              {item.label}
            </a>
          ))}
        </nav>
      )}
    </div>
  )
}
