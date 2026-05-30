import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Rocket, Users, Send, MessageSquare, Zap, BarChart3, Bot, Sparkles
} from 'lucide-react'

const navItems = [
  { to: '/', icon: Sparkles, label: 'Assistant' },
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/campaigns', icon: Rocket, label: 'Campaigns' },
  { to: '/replies', icon: MessageSquare, label: 'Replies' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/agents', icon: Bot, label: 'AI Agents' },
]

export default function Sidebar() {
  return (
    <aside style={styles.sidebar}>
      <div style={styles.logo}>
        <Zap size={24} color="#ff4500" />
        <span style={styles.logoText}>ProspectIQ</span>
      </div>

      <nav style={styles.nav}>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              ...styles.navItem,
              ...(isActive ? styles.navItemActive : {}),
            })}
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div style={styles.footer}>
        <div style={styles.footerText}>
          Powered by Dhanadurga
        </div>
      </div>
    </aside>
  )
}

const styles = {
  sidebar: {
    width: 'var(--sidebar-width)',
    height: '100vh',
    background: 'var(--bg-secondary)',
    borderRight: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    position: 'fixed',
    left: 0,
    top: 0,
    zIndex: 100,
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '24px 20px',
    borderBottom: '1px solid var(--border)',
  },
  logoText: {
    fontSize: '20px',
    fontWeight: 700,
    color: 'var(--text-primary)',
  },
  nav: {
    flex: 1,
    padding: '16px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px 14px',
    borderRadius: '8px',
    color: 'var(--text-secondary)',
    fontSize: '14px',
    fontWeight: 500,
    textDecoration: 'none',
    transition: 'all 0.15s',
  },
  navItemActive: {
    background: 'rgba(255, 69, 0, 0.1)',
    color: '#ff4500',
  },
  footer: {
    padding: '16px 20px',
    borderTop: '1px solid var(--border)',
  },
  footerText: {
    fontSize: '12px',
    color: 'var(--text-muted)',
  },
}
