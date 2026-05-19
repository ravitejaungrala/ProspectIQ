import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Rocket, Users, Send, MessageSquare, TrendingUp,
  Eye, MousePointerClick, Calendar, Trash2
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
    if (!window.confirm(`Delete campaign "${name || 'Untitled'}"? This will remove all leads, emails, and analytics.`)) return
    try {
      await deleteCampaign(id)
      toast.success('Campaign deleted')
      load()
    } catch (err) {
      toast.error(err.message)
    }
  }

  if (loading) return <div style={styles.loading}>Loading...</div>

  const statCards = [
    { label: 'Total Campaigns', value: stats?.total_campaigns || 0, icon: Rocket, color: '#ff4500' },
    { label: 'Total Leads', value: stats?.total_leads || 0, icon: Users, color: '#2563eb' },
    { label: 'Emails Sent', value: stats?.emails_sent || 0, icon: Send, color: '#ff4500' },
    { label: 'Replies', value: stats?.replies_received || 0, icon: MessageSquare, color: '#d97706' },
    { label: 'Open Rate', value: `${stats?.open_rate || 0}%`, icon: Eye, color: '#16a34a' },
    { label: 'Reply Rate', value: `${stats?.reply_rate || 0}%`, icon: TrendingUp, color: '#16a34a' },
    { label: 'Interested', value: stats?.interested_replies || 0, icon: MousePointerClick, color: '#16a34a' },
    { label: 'Demos Booked', value: stats?.demos_booked || 0, icon: Calendar, color: '#ff4500' },
  ]

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Dashboard</h1>
        <button
          onClick={() => navigate('/campaigns')}
          style={styles.newBtn}
        >
          <Rocket size={16} /> New Campaign
        </button>
      </div>

      <div style={styles.statsGrid}>
        {statCards.map((card) => (
          <Card key={card.label}>
            <div style={styles.statCard}>
              <div style={{
                ...styles.statIcon,
                background: `${card.color}20`,
                color: card.color,
              }}>
                <card.icon size={20} />
              </div>
              <div>
                <div style={styles.statValue}>{card.value}</div>
                <div style={styles.statLabel}>{card.label}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <h2 style={styles.sectionTitle}>Recent Campaigns</h2>
      {campaigns.length === 0 ? (
        <Card>
          <div style={styles.empty}>
            <Rocket size={48} color="var(--text-muted)" />
            <p style={{ color: 'var(--text-secondary)', marginTop: '12px' }}>
              No campaigns yet. Create your first campaign to get started!
            </p>
          </div>
        </Card>
      ) : (
        <div style={styles.campaignList}>
          {campaigns.slice(0, 5).map((c) => (
            <Card key={c.id} onClick={() => navigate(`/campaigns/${c.id}`)}>
              <div style={styles.campaignRow}>
                <div>
                  <div style={styles.campaignName}>{c.product_name || 'Processing...'}</div>
                  <div style={styles.campaignUrl}>{c.product_url}</div>
                </div>
                <div style={styles.campaignMeta}>
                  <span style={styles.campaignLeads}>{c.lead_count} leads</span>
                  <span style={{
                    ...styles.statusDot,
                    background: c.status === 'active' ? 'var(--success)' : 'var(--warning)',
                  }} />
                  <span style={styles.statusText}>{c.status}</span>
                  <button
                    onClick={(e) => handleDelete(e, c.id, c.product_name)}
                    style={styles.deleteBtn}
                    title="Delete campaign"
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

const styles = {
  loading: {
    display: 'flex', justifyContent: 'center', alignItems: 'center',
    height: '50vh', color: 'var(--text-secondary)', fontSize: '16px',
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: '32px',
  },
  title: { fontSize: '28px', fontWeight: 700 },
  newBtn: {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '10px 20px', background: 'var(--accent)', color: '#fff',
    border: 'none', borderRadius: '8px', fontSize: '14px', fontWeight: 600,
    cursor: 'pointer',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
    gap: '16px',
    marginBottom: '40px',
  },
  statCard: {
    display: 'flex', alignItems: 'center', gap: '16px',
  },
  statIcon: {
    width: '48px', height: '48px', borderRadius: '12px',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
  },
  statValue: { fontSize: '24px', fontWeight: 700 },
  statLabel: { fontSize: '13px', color: 'var(--text-secondary)' },
  sectionTitle: {
    fontSize: '18px', fontWeight: 600, marginBottom: '16px',
    color: 'var(--text-primary)',
  },
  campaignList: {
    display: 'flex', flexDirection: 'column', gap: '12px',
  },
  campaignRow: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  },
  campaignName: { fontSize: '15px', fontWeight: 600 },
  campaignUrl: { fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' },
  campaignMeta: {
    display: 'flex', alignItems: 'center', gap: '8px',
  },
  campaignLeads: {
    fontSize: '13px', color: 'var(--text-secondary)',
    background: 'var(--bg-primary)', padding: '4px 10px', borderRadius: '20px',
  },
  statusDot: {
    width: '8px', height: '8px', borderRadius: '50%',
  },
  statusText: {
    fontSize: '13px', color: 'var(--text-secondary)', textTransform: 'capitalize',
  },
  deleteBtn: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: '30px', height: '30px', borderRadius: '6px',
    background: 'none', border: '1px solid transparent',
    color: 'var(--text-muted)', cursor: 'pointer',
  },
  empty: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', padding: '48px', textAlign: 'center',
  },
}
