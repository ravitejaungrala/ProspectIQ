import { NavLink } from 'react-router-dom'
import {
<<<<<<< HEAD
  LayoutDashboard, Rocket, Users, Send, MessageSquare, Zap, BarChart3, Bot, Sparkles
=======
  LayoutDashboard, Rocket, MessageSquare, BarChart3, Bot, Zap
>>>>>>> e1b1ab5fd342c1204855fe7b165408539da5ce35
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
      {/* Logo */}
      <div style={styles.logoArea}>
        <div style={styles.logoTile}>
          <Zap size={20} color="#fff" fill="#fff" />
        </div>
        <div>
          <div style={styles.logoText}>ProspectIQ</div>
          <div style={styles.logoBadge}>AI Outreach</div>
        </div>
      </div>

      {/* Nav */}
      <nav style={styles.nav}>
        <div style={styles.navLabel}>MAIN MENU</div>
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
            {({ isActive }) => (
              <>
                {isActive && <span style={styles.activeBar} />}
                <span style={{
                  ...styles.iconWrap,
                  ...(isActive ? styles.iconWrapActive : {}),
                }}>
                  <Icon size={17} />
                </span>
                <span>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={styles.footer}>
        <div style={styles.footerInner}>
          <div style={styles.footerDot} />
          <div>
            <div style={styles.footerName}>Powered by</div>
            <div style={styles.footerBrand}>Dhanadurga</div>
          </div>
        </div>
      </div>
    </aside>
  )
}

const styles = {
  sidebar: {
    width: 'var(--sidebar-width)',
    height: '100vh',
    background: '#ffffff',
    borderRight: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    position: 'fixed',
    left: 0,
    top: 0,
    zIndex: 100,
    boxShadow: '2px 0 12px rgba(17,24,39,.04)',
  },
  logoArea: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '22px 20px 20px',
    borderBottom: '1px solid var(--border)',
  },
  logoTile: {
    width: '38px',
    height: '38px',
    borderRadius: '10px',
    background: 'linear-gradient(135deg, #ff4500, #ff6b35)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 4px 14px rgba(255,69,0,.35)',
    flexShrink: 0,
  },
  logoText: {
    fontSize: '16px',
    fontWeight: 800,
    color: '#111111',
    letterSpacing: '-0.3px',
  },
  logoBadge: {
    fontSize: '10px',
    fontWeight: 600,
    color: '#ff4500',
    textTransform: 'uppercase',
    letterSpacing: '0.6px',
    marginTop: '1px',
  },
  nav: {
    flex: 1,
    padding: '20px 12px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
    overflowY: 'auto',
  },
  navLabel: {
    fontSize: '10px',
    fontWeight: 700,
    color: '#d1d5db',
    letterSpacing: '0.8px',
    padding: '0 8px',
    marginBottom: '8px',
    marginTop: '2px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '11px',
    padding: '10px 12px',
    borderRadius: '10px',
    color: '#6b7280',
    fontSize: '14px',
    fontWeight: 500,
    textDecoration: 'none',
    transition: 'all 0.15s',
    position: 'relative',
    overflow: 'hidden',
  },
  navItemActive: {
    background: 'rgba(255,69,0,0.07)',
    color: '#ff4500',
    fontWeight: 700,
  },
  activeBar: {
    position: 'absolute',
    left: 0,
    top: '50%',
    transform: 'translateY(-50%)',
    width: '3px',
    height: '20px',
    borderRadius: '0 4px 4px 0',
    background: '#ff4500',
  },
  iconWrap: {
    width: '32px',
    height: '32px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'transparent',
    transition: 'all 0.15s',
    flexShrink: 0,
  },
  iconWrapActive: {
    background: 'rgba(255,69,0,0.12)',
    color: '#ff4500',
  },
  footer: {
    padding: '14px 16px 18px',
    borderTop: '1px solid var(--border)',
  },
  footerInner: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '10px 12px',
    borderRadius: '10px',
    background: 'var(--bg-secondary)',
  },
  footerDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#10b981',
    boxShadow: '0 0 6px rgba(16,185,129,.6)',
    flexShrink: 0,
  },
  footerName: {
    fontSize: '10px',
    color: '#9ca3af',
    fontWeight: 500,
  },
  footerBrand: {
    fontSize: '12px',
    fontWeight: 700,
    color: '#374151',
  },
}
