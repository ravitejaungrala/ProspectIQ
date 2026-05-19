import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart3, Send, Eye, MousePointerClick, MessageSquare,
  TrendingUp, Users, CheckCircle, Clock, ArrowRight, Rocket
} from 'lucide-react'
import Card from '../components/Card'
import { getGlobalAnalytics, getCampaigns, getCampaignAnalytics } from '../api/client'

export default function Analytics() {
  const [global, setGlobal] = useState(null)
  const [campaigns, setCampaigns] = useState([])
  const [selectedCampaign, setSelectedCampaign] = useState(null)
  const [campaignData, setCampaignData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([
      getGlobalAnalytics().catch(() => null),
      getCampaigns().catch(() => []),
    ]).then(([g, c]) => {
      setGlobal(g)
      setCampaigns(c)
      setLoading(false)
    })
  }, [])

  const loadCampaignAnalytics = async (id) => {
    setSelectedCampaign(id)
    setCampaignData(null)
    try {
      const data = await getCampaignAnalytics(id)
      setCampaignData(data)
    } catch (e) {
      setCampaignData(null)
    }
  }

  if (loading) return <div style={styles.loading}>Loading analytics...</div>

  const emails = global?.emails || {}
  const replies = global?.replies || {}

  return (
    <div>
      <h1 style={styles.title}>
        <BarChart3 size={24} color="var(--accent-light)" /> Analytics
      </h1>

      {/* Global Overview Cards */}
      <div style={styles.statsGrid}>
        <StatCard icon={Send} label="Emails Sent" value={emails.sent || 0} color="#ff4500" />
        <StatCard icon={Eye} label="Open Rate" value={`${emails.open_rate || 0}%`} color="#16a34a" />
        <StatCard icon={MousePointerClick} label="Click Rate" value={`${emails.click_rate || 0}%`} color="#2563eb" />
        <StatCard icon={MessageSquare} label="Reply Rate" value={`${emails.reply_rate || 0}%`} color="#d97706" />
        <StatCard icon={CheckCircle} label="Approved" value={emails.approved || 0} color="#16a34a" />
        <StatCard icon={Clock} label="Pending" value={emails.pending || 0} color="#dc2626" />
        <StatCard icon={Users} label="Total Leads" value={global?.total_leads || 0} color="#ff4500" />
        <StatCard icon={Rocket} label="Demos Booked" value={replies.demos || 0} color="#16a34a" />
      </div>

      {/* Email Funnel */}
      <Card style={{ marginBottom: '24px' }}>
        <h3 style={styles.cardTitle}>Outreach Funnel</h3>
        <div style={styles.funnel}>
          <FunnelStep label="Total Emails" value={emails.sent + emails.pending + emails.approved || 0} width="100%" />
          <FunnelStep label="Approved" value={emails.approved || 0} width="85%" color="#16a34a" />
          <FunnelStep label="Sent" value={emails.sent || 0} width="70%" color="#ff4500" />
          <FunnelStep label="Opened" value={emails.opened || 0} width="50%" color="#16a34a" />
          <FunnelStep label="Clicked" value={emails.clicked || 0} width="30%" color="#2563eb" />
          <FunnelStep label="Replied" value={emails.replied || 0} width="20%" color="#d97706" />
        </div>
      </Card>

      {/* Reply Intent Breakdown */}
      <div style={styles.twoCol}>
        <Card>
          <h3 style={styles.cardTitle}>Reply Intent Breakdown</h3>
          <div style={styles.intentList}>
            <IntentRow label="Interested" value={replies.interested || 0} color="#16a34a" />
            <IntentRow label="Demo Request" value={replies.demos || 0} color="#ff4500" />
            <IntentRow label="Not Interested" value={replies.not_interested || 0} color="#dc2626" />
            <IntentRow label="Total Replies" value={replies.total || 0} color="#2563eb" />
          </div>
        </Card>

        {/* Campaign Selector */}
        <Card>
          <h3 style={styles.cardTitle}>Campaign Performance</h3>
          <div style={styles.campaignList}>
            {(global?.campaigns || []).map((c) => (
              <div
                key={c.id}
                style={{
                  ...styles.campaignRow,
                  ...(selectedCampaign === c.id ? styles.campaignRowActive : {}),
                }}
                onClick={() => loadCampaignAnalytics(c.id)}
              >
                <div>
                  <div style={styles.campaignName}>{c.name || 'Unnamed'}</div>
                  <div style={styles.campaignMeta}>
                    {c.leads} leads · {c.sent} sent · {c.reply_rate}% reply rate
                  </div>
                </div>
                <ArrowRight size={14} color="var(--text-muted)" />
              </div>
            ))}
            {(!global?.campaigns || global.campaigns.length === 0) && (
              <p style={styles.empty}>No campaigns yet</p>
            )}
          </div>
        </Card>
      </div>

      {/* Campaign Detail Analytics */}
      {campaignData && (
        <div style={{ marginTop: '24px' }}>
          <h2 style={styles.sectionTitle}>
            {campaignData.campaign_name} — Detailed Analytics
          </h2>

          {/* Campaign overview stats */}
          <div style={styles.statsGrid}>
            <MiniStat label="Leads" value={campaignData.overview.total_leads} />
            <MiniStat label="Emails" value={campaignData.overview.total_emails} />
            <MiniStat label="Pending" value={campaignData.overview.pending} />
            <MiniStat label="Approved" value={campaignData.overview.approved} />
            <MiniStat label="Sent" value={campaignData.overview.sent} />
            <MiniStat label="Open Rate" value={`${campaignData.overview.open_rate}%`} />
            <MiniStat label="Reply Rate" value={`${campaignData.overview.reply_rate}%`} />
            <MiniStat label="Replies" value={campaignData.total_replies} />
          </div>

          {/* By Template Type */}
          <div style={styles.twoCol}>
            <Card>
              <h3 style={styles.cardTitle}>By Email Type</h3>
              {Object.entries(campaignData.by_template_type).map(([type, data]) => (
                <div key={type} style={styles.breakdownRow}>
                  <span style={styles.breakdownLabel}>{type.replace(/_/g, ' ')}</span>
                  <div style={styles.breakdownStats}>
                    <span>Sent: {data.sent}</span>
                    <span>Opened: {data.opened}</span>
                    <span>Replied: {data.replied}</span>
                  </div>
                </div>
              ))}
              {Object.keys(campaignData.by_template_type).length === 0 && (
                <p style={styles.empty}>No data yet</p>
              )}
            </Card>

            <Card>
              <h3 style={styles.cardTitle}>By Role</h3>
              {Object.entries(campaignData.by_role).map(([role, data]) => (
                <div key={role} style={styles.breakdownRow}>
                  <span style={styles.breakdownLabel}>{role.toUpperCase()}</span>
                  <div style={styles.breakdownStats}>
                    <span>Sent: {data.sent}</span>
                    <span>Opened: {data.opened}</span>
                    <span>Replied: {data.replied}</span>
                  </div>
                </div>
              ))}
              {Object.keys(campaignData.by_role).length === 0 && (
                <p style={styles.empty}>No data yet</p>
              )}
            </Card>
          </div>

          {/* Sequence Progress */}
          <Card style={{ marginTop: '16px' }}>
            <h3 style={styles.cardTitle}>Sequence Progress</h3>
            <div style={styles.sequenceGrid}>
              {Object.entries(campaignData.sequence_progress).map(([step, data]) => (
                <div key={step} style={styles.sequenceCard}>
                  <div style={styles.sequenceLabel}>{step.replace(/_/g, ' ')}</div>
                  <div style={styles.sequenceStats}>
                    <div style={styles.seqStat}><span style={{ color: '#dc2626' }}>{data.pending}</span> pending</div>
                    <div style={styles.seqStat}><span style={{ color: '#16a34a' }}>{data.approved}</span> approved</div>
                    <div style={styles.seqStat}><span style={{ color: '#ff4500' }}>{data.sent}</span> sent</div>
                    <div style={styles.seqStat}><span style={{ color: '#d97706' }}>{data.replied}</span> replied</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Lead Status Breakdown */}
          <Card style={{ marginTop: '16px' }}>
            <h3 style={styles.cardTitle}>Lead Statuses</h3>
            <div style={styles.statusRow}>
              {Object.entries(campaignData.lead_statuses).map(([status, count]) => (
                <div key={status} style={styles.statusChip}>
                  <span style={styles.statusCount}>{count}</span>
                  <span style={styles.statusLabel}>{status}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <Card>
      <div style={styles.statCard}>
        <div style={{ ...styles.statIcon, background: `${color}20`, color }}>
          <Icon size={20} />
        </div>
        <div>
          <div style={styles.statValue}>{value}</div>
          <div style={styles.statLabel}>{label}</div>
        </div>
      </div>
    </Card>
  )
}

function MiniStat({ label, value }) {
  return (
    <Card>
      <div style={{ textAlign: 'center', padding: '4px 0' }}>
        <div style={{ fontSize: '20px', fontWeight: 700 }}>{value}</div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
      </div>
    </Card>
  )
}

function FunnelStep({ label, value, width, color = 'var(--accent)' }) {
  return (
    <div style={styles.funnelStep}>
      <div style={styles.funnelLabel}>{label}</div>
      <div style={styles.funnelBarBg}>
        <div style={{ ...styles.funnelBar, width, background: color }} />
      </div>
      <div style={styles.funnelValue}>{value}</div>
    </div>
  )
}

function IntentRow({ label, value, color }) {
  return (
    <div style={styles.intentRow}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: color }} />
        <span>{label}</span>
      </div>
      <span style={{ fontWeight: 700 }}>{value}</span>
    </div>
  )
}

const styles = {
  loading: {
    display: 'flex', justifyContent: 'center', alignItems: 'center',
    height: '50vh', color: 'var(--text-secondary)',
  },
  title: {
    fontSize: '24px', fontWeight: 700, marginBottom: '24px',
    display: 'flex', alignItems: 'center', gap: '10px',
  },
  statsGrid: {
    display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: '12px', marginBottom: '24px',
  },
  statCard: { display: 'flex', alignItems: 'center', gap: '14px' },
  statIcon: {
    width: '44px', height: '44px', borderRadius: '10px',
    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
  },
  statValue: { fontSize: '22px', fontWeight: 700 },
  statLabel: { fontSize: '12px', color: 'var(--text-muted)' },
  cardTitle: { fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '16px' },
  twoCol: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' },
  funnel: { display: 'flex', flexDirection: 'column', gap: '8px' },
  funnelStep: { display: 'grid', gridTemplateColumns: '100px 1fr 60px', alignItems: 'center', gap: '12px' },
  funnelLabel: { fontSize: '13px', color: 'var(--text-secondary)' },
  funnelBarBg: { height: '24px', background: 'var(--bg-primary)', borderRadius: '4px', overflow: 'hidden' },
  funnelBar: { height: '100%', borderRadius: '4px', transition: 'width 0.5s ease' },
  funnelValue: { fontSize: '14px', fontWeight: 600, textAlign: 'right' },
  intentList: { display: 'flex', flexDirection: 'column', gap: '12px' },
  intentRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '14px' },
  campaignList: { display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '300px', overflowY: 'auto' },
  campaignRow: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '10px 12px', borderRadius: '8px', cursor: 'pointer',
    border: '1px solid transparent',
  },
  campaignRowActive: {
    background: 'rgba(108, 92, 231, 0.1)', border: '1px solid var(--accent-light)',
  },
  campaignName: { fontSize: '14px', fontWeight: 600 },
  campaignMeta: { fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' },
  sectionTitle: { fontSize: '18px', fontWeight: 600, marginBottom: '16px' },
  breakdownRow: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '8px 0', borderBottom: '1px solid var(--border)',
  },
  breakdownLabel: { fontSize: '13px', fontWeight: 600, textTransform: 'capitalize' },
  breakdownStats: { display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--text-secondary)' },
  sequenceGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' },
  sequenceCard: {
    background: 'var(--bg-primary)', borderRadius: '8px', padding: '12px',
    border: '1px solid var(--border)',
  },
  sequenceLabel: { fontSize: '13px', fontWeight: 600, textTransform: 'capitalize', marginBottom: '8px' },
  sequenceStats: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' },
  seqStat: { fontSize: '12px', color: 'var(--text-secondary)' },
  statusRow: { display: 'flex', flexWrap: 'wrap', gap: '8px' },
  statusChip: {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '8px 14px', borderRadius: '8px',
    background: 'var(--bg-primary)', border: '1px solid var(--border)',
  },
  statusCount: { fontSize: '16px', fontWeight: 700 },
  statusLabel: { fontSize: '12px', color: 'var(--text-muted)', textTransform: 'capitalize' },
  empty: { fontSize: '13px', color: 'var(--text-muted)' },
}
