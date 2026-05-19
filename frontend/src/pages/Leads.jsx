import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Search } from 'lucide-react'
import Card from '../components/Card'
import StatusBadge from '../components/StatusBadge'
import { getCampaignLeads, getCampaign } from '../api/client'

export default function Leads() {
  const { campaignId } = useParams()
  const navigate = useNavigate()
  const [leads, setLeads] = useState([])
  const [campaign, setCampaign] = useState(null)
  const [filter, setFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getCampaign(campaignId),
      getCampaignLeads(campaignId),
    ]).then(([c, l]) => {
      setCampaign(c)
      setLeads(l)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [campaignId])

  const filtered = leads.filter((l) => {
    const matchesText = !filter ||
      `${l.first_name} ${l.last_name} ${l.company} ${l.email}`.toLowerCase().includes(filter.toLowerCase())
    const matchesStatus = !statusFilter || l.status === statusFilter
    return matchesText && matchesStatus
  })

  const statuses = [...new Set(leads.map(l => l.status))]

  if (loading) return <div style={styles.loading}>Loading...</div>

  return (
    <div>
      <button onClick={() => navigate(`/campaigns/${campaignId}`)} style={styles.back}>
        <ArrowLeft size={16} /> Back to Campaign
      </button>

      <h1 style={styles.title}>Leads — {campaign?.product_name}</h1>

      <div style={styles.filters}>
        <div style={styles.searchBox}>
          <Search size={16} color="var(--text-muted)" />
          <input
            placeholder="Search leads..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={styles.searchInput}
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={styles.select}
        >
          <option value="">All Statuses</option>
          {statuses.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div style={styles.count}>{filtered.length} leads</div>

      <div style={styles.table}>
        <div style={styles.tableHeader}>
          <span>Name</span>
          <span>Company</span>
          <span>Title</span>
          <span>Email</span>
          <span>Email Valid</span>
          <span>Score</span>
          <span>Status</span>
        </div>
        {filtered.map((lead) => (
          <div key={lead.id} style={styles.tableRow}>
            <span style={{ fontWeight: 500 }}>{lead.first_name} {lead.last_name}</span>
            <span style={{ color: 'var(--text-secondary)' }}>{lead.company}</span>
            <span style={{ color: 'var(--text-secondary)' }}>{lead.title}</span>
            <span style={{ color: 'var(--accent-light)', fontSize: '12px' }}>{lead.email}</span>
            <span><StatusBadge status={lead.email_status} /></span>
            <span>
              <span style={{
                padding: '2px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600,
                background: lead.profile_score >= 70 ? 'rgba(22,163,74,0.1)' :
                  lead.profile_score >= 40 ? 'rgba(217,119,6,0.1)' : 'rgba(220,38,38,0.1)',
                color: lead.profile_score >= 70 ? '#16a34a' :
                  lead.profile_score >= 40 ? '#d97706' : '#dc2626',
              }}>
                {lead.profile_score}
              </span>
            </span>
            <span><StatusBadge status={lead.status} /></span>
          </div>
        ))}
      </div>
    </div>
  )
}

const styles = {
  loading: {
    display: 'flex', justifyContent: 'center', alignItems: 'center',
    height: '50vh', color: 'var(--text-secondary)',
  },
  back: {
    display: 'flex', alignItems: 'center', gap: '6px',
    background: 'none', border: 'none', color: 'var(--text-secondary)',
    fontSize: '14px', cursor: 'pointer', marginBottom: '16px', padding: 0,
  },
  title: { fontSize: '24px', fontWeight: 700, marginBottom: '20px' },
  filters: {
    display: 'flex', gap: '12px', marginBottom: '16px',
  },
  searchBox: {
    flex: 1, display: 'flex', alignItems: 'center', gap: '8px',
    padding: '8px 14px', borderRadius: '8px',
    border: '1px solid var(--border)', background: 'var(--bg-card)',
  },
  searchInput: {
    flex: 1, border: 'none', background: 'none', color: 'var(--text-primary)',
    fontSize: '14px', outline: 'none',
  },
  select: {
    padding: '8px 14px', borderRadius: '8px',
    border: '1px solid var(--border)', background: 'var(--bg-card)',
    color: 'var(--text-primary)', fontSize: '14px', outline: 'none',
  },
  count: { fontSize: '13px', color: 'var(--text-muted)', marginBottom: '12px' },
  table: {
    background: 'var(--bg-card)', border: '1px solid var(--border)',
    borderRadius: '12px', overflow: 'hidden',
  },
  tableHeader: {
    display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr 1.5fr 0.7fr 0.5fr 0.8fr',
    padding: '12px 20px', background: 'var(--bg-secondary)',
    borderBottom: '1px solid var(--border)',
    fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.05em',
  },
  tableRow: {
    display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr 1.5fr 0.7fr 0.5fr 0.8fr',
    padding: '12px 20px', borderBottom: '1px solid var(--border)',
    fontSize: '13px', alignItems: 'center',
  },
}
