import type { Metadata } from 'next'
import './globals.css'
import { MobileNav } from './components/mobile-nav'

export const metadata: Metadata = {
  title: 'SkyBridge Jets — Lead Generation',
  description: 'AI-powered lead generation platform for UHNW private aviation',
}

const navItems = [
  { href: '/', label: 'New Search', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
  { href: '/prospects', label: 'Prospects', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z' },
  { href: '/outreach', label: 'Outreach', icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
  { href: '/export', label: 'Export', icon: 'M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
]

function DesktopSidebar() {
  return (
    <aside className="hidden lg:flex w-64 bg-navy-950 border-r border-navy-800 min-h-screen flex-col">
      <div className="p-6 border-b border-navy-800">
        <h1 className="text-xl font-bold text-gold-400 tracking-tight">SkyBridge Jets</h1>
        <p className="text-xs text-navy-400 mt-1">Lead Generation Platform</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <a
            key={item.href}
            href={item.href}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-navy-300 hover:text-white hover:bg-navy-800 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
            </svg>
            {item.label}
          </a>
        ))}
      </nav>
      <div className="p-4 border-t border-navy-800">
        <p className="text-xs text-navy-500 text-center">Private Aviation Brokerage</p>
      </div>
    </aside>
  )
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-navy-950 text-white antialiased">
        <div className="flex min-h-screen">
          <DesktopSidebar />
          <div className="flex-1 flex flex-col min-h-screen">
            <MobileNav navItems={navItems} />
            <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  )
}
