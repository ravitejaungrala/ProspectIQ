import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Rocket, Users, Send, MessageSquare, TrendingUp,
  Eye, MousePointerClick, Calendar, Trash2, Plus, ArrowRight
} from 'lucide-react'
import Card from '../components/Card'
import { getDashboardStats, getCampaigns, deleteCampaign } from '../api/client'
import toast from 'react-hot-toast'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const load = () => {
    Promise.all([
      getDashboardStats().catch(() => null),
      getCampaigns().catch(() => []),
    ]).then(([s, c]) => {
      setStats(s)
      setCampaigns(c)
      setLoading(false)
    })
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (e, id, name) => {
    e.stopPropagation()
    if (!window.confirm(`Delete "${name || 'Untitled'}"? This removes all leads, emails, and analytics.`)) return
    try {
      await deleteCampaign(id)
      toast.success('Campaign deleted')
      load()
    } catch (err) {
      toast.error(err.message)
    }
  }

  if (loading) return <LoadingState />

  const statCards = [
    { label: 'Total Campaigns', value: stats?.total_campaigns || 0,    icon: Rocket,          color: '#ff4500', bg: 'rgba(255,69,0,0.1)' },
    { label: 'Total Leads',     value: stats?.total_leads || 0,         icon: Users,           color: '#3b82f6', bg: 'rgba(59,130,246,0.1)' },
    { label: 'Emails Sent',     value: stats?.emails_sent || 0,         icon: Send,            color: '#ff4500', bg: 'rgba(255,69,0,0.1)' },
    { label: 'Replies',         value: stats?.replies_received || 0,    icon: MessageSquare,   color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
    { label: 'Open Rate',       value: `${stats?.open_rate || 0}%`,     icon: Eye,             color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
    { label: 'Reply Rate',      value: `${stats?.reply_rate || 0}%`,    icon: TrendingUp,      color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
    { label: 'Interested',      value: stats?.interested_replies || 0,  icon: MousePointerClick,color:'#8b5cf6',  bg: 'rgba(139,92,246,0.1)' },
    { label: 'Demos Booked',    value: stats?.demos_booked || 0,        icon: Calendar,        color: '#ff4500', bg: 'rgba(255,69,0,0.1)' },
  ]

  return (
    <div className="animate-in">
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Dashboard</h1>
          <p style={styles.subtitle}>Overview of your outreach performance</p>
        </div>
        <button onClick={() => navigate('/campaigns')} style={styles.newBtn}>
          <Plus size={15} />
          New Campaign
        </button>
      </div>

      {/* KPI grid */}
      <div style={styles.statsGrid}>
        {statCards.map((card, i) => (
          <KPICard key={card.label} {...card} delay={i * 40} />
        ))}
      </div>

      {/* Recent campaigns */}
      <div style={styles.sectionHeader}>
        <h2 style={styles.sectionTitle}>Recent Campaigns</h2>
        <button onClick={() => navigate('/campaigns')} style={styles.viewAll}>
          View all <ArrowRight size={13} />
        </button>
      </div>

      {campaigns.length === 0 ? (
        <Card>
          <div style={styles.empty}>
            <div style={styles.emptyIcon}><Rocket size={28} color="#ff4500" /></div>
            <p style={styles.emptyTitle}>No campaigns yet</p>
            <p style={styles.emptyText}>Create your first campaign to start generating leads!</p>
            <button onClick={() => navigate('/campaigns')} style={{ ...styles.newBtn, marginTop: '16px' }}>
              <Plus size={14} /> New Campaign
            </button>
          </div>
        </Card>
      ) : (
        <div style={styles.campaignList}>
          {campaigns.slice(0, 5).map((c) => (
            <Card key={c.id} onClick={() => navigate(`/campaigns/${c.id}`)}>
              <div style={styles.campaignRow}>
                <div style={styles.campaignLeft}>
                  <div style={styles.campaignIcon}>
                    <Rocket size={15} color="#ff4500" />
                  </div>
                  <div>
                    <div style={styles.campaignName}>{c.product_name || 'Processing...'}</div>
                    <div style={styles.campaignUrl}>{c.product_url}</div>
                  </div>
                </div>
                <div style={styles.campaignMeta}>
                  <span style={styles.leadsChip}>{c.lead_count} leads</span>
                  <span style={{
                    ...styles.statusChip,
                    background: c.status === 'active' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                    color: c.status === 'active' ? '#047857' : '#92400e',
                    border: `1px solid ${c.status === 'active' ? 'rgba(16,185,129,0.25)' : 'rgba(245,158,11,0.25)'}`,
                  }}>
                    <span style={{
                      width: '6px', height: '6px', borderRadius: '50%',
                      background: c.status === 'active' ? '#10b981' : '#f59e0b',
                      display: 'inline-block',
                    }} />
                    {c.status}
                  </span>
                  <button
                    onClick={(e) => handleDelete(e, c.id, c.product_name)}
                    style={styles.deleteBtn}
                    title="Delete campaign"
                    onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(239,68,68,0.1)'; e.currentTarget.style.color = '#ef4444' }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-muted)' }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

function KPICard({ label, value, icon: Icon, color, bg, delay = 0 }) {
  return (
    <div style={{ ...styles.kpiCard, animationDelay: `${delay}ms` }} className="animate-in">
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
        background: 'linear-gradient(90deg, #ff4500, #10b981)', borderRadius: '16px 16px 0 0', opacity: 0.5 }} />
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ ...styles.kpiIcon, background: bg, color }}><Icon size={19} /></div>
        <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: bg,
          display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: color }} />
        </div>
      </div>
      <div style={styles.kpiValue}>{value}</div>
      <div style={styles.kpiLabel}>{label}</div>
    </div>
  )
}

function LoadingState() {
  return (
    <div style={{ padding: '40px 0' }}>
      <div style={{ height: '32px', width: '160px', marginBottom: '8px' }} className="skeleton" />
      <div style={{ height: '18px', width: '240px', marginBottom: '32px' }} className="skeleton" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '32px' }}>
        {Array(8).fill(0).map((_, i) => (
          <div key={i} style={{ height: '110px', borderRadius: '16px' }} className="skeleton" />
        ))}
      </div>
    </div>
  )
}

const styles = {
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
    marginBottom: '28px',
  },
  title: { fontSize: '26px', fontWeight: 800, letterSpacing: '-0.4px', color: '#111111' },
  subtitle: { fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' },
  newBtn: {
    display: 'inline-flex', alignItems: 'center', gap: '7px',
    padding: '10px 20px',
    background: 'linear-gradient(135deg, #ff4500, #ff6035)',
    color: '#fff', border: 'none', borderRadius: '10px',
    fontSize: '14px', fontWeight: 600, cursor: 'pointer',
    boxShadow: '0 2px 10px rgba(255,69,0,.28)',
    transition: 'all 0.16s',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '14px',
    marginBottom: '36px',
  },
  kpiCard: {
    background: '#ffffff',
    border: '1px solid var(--border)',
    borderRadius: '16px',
    padding: '20px',
    boxShadow: 'var(--shadow-sm)',
    transition: 'var(--transition)',
    position: 'relative',
    overflow: 'hidden',
  },
  kpiIcon: {
    width: '42px', height: '42px', borderRadius: '11px',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
  },
  kpiValue: { fontSize: '28px', fontWeight: 800, letterSpacing: '-0.8px', color: '#111111' },
  kpiLabel: { fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500,
    textTransform: 'uppercase', letterSpacing: '0.6px', marginTop: '4px' },
  sectionHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: '14px',
  },
  sectionTitle: { fontSize: '17px', fontWeight: 700 },
  viewAll: {
    display: 'inline-flex', alignItems: 'center', gap: '5px',
    fontSize: '13px', fontWeight: 600, color: '#ff4500',
    background: 'none', border: 'none', cursor: 'pointer',
  },
  campaignList: { display: 'flex', flexDirection: 'column', gap: '10px' },
  campaignRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  campaignLeft: { display: 'flex', alignItems: 'center', gap: '12px' },
  campaignIcon: {
    width: '36px', height: '36px', borderRadius: '9px',
    background: 'rgba(255,69,0,0.08)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
  },
  campaignName: { fontSize: '14px', fontWeight: 600, color: '#111111' },
  campaignUrl: { fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' },
  campaignMeta: { display: 'flex', alignItems: 'center', gap: '8px' },
  leadsChip: {
    fontSize: '12px', fontWeight: 600, color: '#374151',
    background: 'var(--bg-secondary)', padding: '4px 10px',
    borderRadius: '20px', border: '1px solid var(--border)',
  },
  statusChip: {
    fontSize: '11px', fontWeight: 700, padding: '4px 10px',
    borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '5px',
    textTransform: 'capitalize',
  },
  deleteBtn: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: '30px', height: '30px', borderRadius: '7px',
    background: 'transparent', border: 'none',
    color: 'var(--text-muted)', cursor: 'pointer', transition: 'all 0.15s',
  },
  empty: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    padding: '52px 24px', textAlign: 'center',
  },
  emptyIcon: {
    width: '60px', height: '60px', borderRadius: '16px',
    background: 'rgba(255,69,0,0.08)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    marginBottom: '16px',
  },
  emptyTitle: { fontSize: '15px', fontWeight: 700, marginBottom: '6px' },
  emptyText: { fontSize: '13px', color: 'var(--text-muted)', maxWidth: '300px' },
}
