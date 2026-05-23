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

  if (loading) return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'50vh', gap:'12px' }}>
      <div style={{ width:8, height:8, borderRadius:'50%', background:'#ff4500', animation:'pulse-ring 1.2s infinite' }} />
      <span style={{ color: 'var(--text-muted)', fontSize:'14px' }}>Loading analytics...</span>
    </div>
  )

  const emails = global?.emails || {}
  const replies = global?.replies || {}
  const funnelTotal = (emails.sent || 0) + (emails.pending || 0) + (emails.approved || 0)

  const funnelSteps = [
    { label: 'Total',    value: funnelTotal,           pct: 100, color: '#6b7280' },
    { label: 'Approved', value: emails.approved || 0,  pct: funnelTotal ? Math.round((emails.approved || 0)/funnelTotal*100) : 0, color: '#10b981' },
    { label: 'Sent',     value: emails.sent || 0,      pct: funnelTotal ? Math.round((emails.sent || 0)/funnelTotal*100) : 0,     color: '#ff4500' },
    { label: 'Opened',   value: emails.opened || 0,    pct: funnelTotal ? Math.round((emails.opened || 0)/funnelTotal*100) : 0,   color: '#10b981' },
    { label: 'Clicked',  value: emails.clicked || 0,   pct: funnelTotal ? Math.round((emails.clicked || 0)/funnelTotal*100) : 0,  color: '#3b82f6' },
    { label: 'Replied',  value: emails.replied || 0,   pct: funnelTotal ? Math.round((emails.replied || 0)/funnelTotal*100) : 0,  color: '#f59e0b' },
  ]

  const intentData = [
    { label: 'Interested',    value: replies.interested || 0,    color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
    { label: 'Demo Request',  value: replies.demos || 0,         color: '#ff4500', bg: 'rgba(255,69,0,0.1)' },
    { label: 'Not Interested',value: replies.not_interested || 0,color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
    { label: 'Total Replies', value: replies.total || 0,         color: '#3b82f6', bg: 'rgba(59,130,246,0.1)' },
  ]
  const maxIntent = Math.max(...intentData.map(d => d.value), 1)

  return (
    <div className="animate-in">
      {/* Page header */}
      <div style={styles.pageHeader}>
        <div style={styles.pageIconWrap}><BarChart3 size={20} color="#ff4500" /></div>
        <div>
          <h1 style={styles.title}>Analytics</h1>
          <p style={styles.subtitle}>Performance across all campaigns</p>
        </div>
      </div>

      {/* Stat cards */}
      <div style={styles.statsGrid}>
        <StatCard icon={Send}           label="Emails Sent"  value={emails.sent || 0}                 color="#ff4500" bg="rgba(255,69,0,0.08)" />
        <StatCard icon={Eye}            label="Open Rate"    value={`${emails.open_rate || 0}%`}      color="#10b981" bg="rgba(16,185,129,0.08)" />
        <StatCard icon={MousePointerClick} label="Click Rate" value={`${emails.click_rate || 0}%`}   color="#3b82f6" bg="rgba(59,130,246,0.08)" />
        <StatCard icon={MessageSquare}  label="Reply Rate"   value={`${emails.reply_rate || 0}%`}    color="#f59e0b" bg="rgba(245,158,11,0.08)" />
        <StatCard icon={CheckCircle}    label="Approved"     value={emails.approved || 0}             color="#10b981" bg="rgba(16,185,129,0.08)" />
        <StatCard icon={Clock}          label="Pending"      value={emails.pending || 0}              color="#ef4444" bg="rgba(239,68,68,0.08)" />
        <StatCard icon={Users}          label="Total Leads"  value={global?.total_leads || 0}         color="#ff4500" bg="rgba(255,69,0,0.08)" />
        <StatCard icon={Rocket}         label="Demos Booked" value={replies.demos || 0}               color="#10b981" bg="rgba(16,185,129,0.08)" />
      </div>

      {/* Funnel */}
      <Card style={{ marginBottom: '20px' }} accent>
        <h3 style={styles.cardTitle}>
          <span style={styles.cardTitleDot} />
          Outreach Funnel
        </h3>
        <p style={styles.cardSub}>Conversion at each stage of your email sequence</p>
        <div style={styles.funnel}>
          {funnelSteps.map((step) => (
            <div key={step.label} style={styles.funnelRow}>
              <div style={styles.funnelLabelWrap}>
                <span style={styles.funnelLabel}>{step.label}</span>
              </div>
              <div style={styles.funnelBarWrap}>
                <div style={{
                  ...styles.funnelBar,
                  width: `${step.pct}%`,
                  background: step.color,
                  opacity: 0.85,
                }} />
                <div style={{ ...styles.funnelBarBg }} />
              </div>
              <div style={{ ...styles.funnelPct, color: step.color }}>{step.pct}%</div>
              <div style={styles.funnelVal}>{step.value.toLocaleString()}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Intent + Campaign performance */}
      <div style={styles.twoCol}>
        {/* Intent bars */}
        <Card>
          <h3 style={styles.cardTitle}><span style={styles.cardTitleDot} />Reply Intent</h3>
          <p style={styles.cardSub}>How leads are responding</p>
          <div style={styles.intentList}>
            {intentData.map((d) => (
              <div key={d.label} style={styles.intentRow}>
                <div style={styles.intentLeft}>
                  <div style={{ ...styles.intentDot, background: d.color }} />
                  <span style={styles.intentLabel}>{d.label}</span>
                </div>
                <div style={styles.intentBarWrap}>
                  <div style={{
                    height: '100%', borderRadius: '4px',
                    background: d.color,
                    width: `${(d.value / maxIntent) * 100}%`,
                    minWidth: d.value > 0 ? '4px' : '0',
                    transition: 'width 0.6s ease',
                    opacity: 0.85,
                  }} />
                </div>
                <span style={{ ...styles.intentVal, color: d.color }}>{d.value}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Campaign list */}
        <Card>
          <h3 style={styles.cardTitle}><span style={styles.cardTitleDot} />Campaign Performance</h3>
          <p style={styles.cardSub}>Click to drill into a campaign</p>
          <div style={styles.campaignList}>
            {(global?.campaigns || []).map((c) => (
              <div
                key={c.id}
                style={{
                  ...styles.campaignRow,
                  ...(selectedCampaign === c.id ? styles.campaignRowActive : {}),
                }}
                onClick={() => loadCampaignAnalytics(c.id)}
                onMouseEnter={(e) => { if (selectedCampaign !== c.id) e.currentTarget.style.background = 'var(--bg-secondary)' }}
                onMouseLeave={(e) => { if (selectedCampaign !== c.id) e.currentTarget.style.background = 'transparent' }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={styles.cName}>{c.name || 'Unnamed'}</div>
                  <div style={styles.cMeta}>
                    <span style={styles.cMetaChip}>{c.leads} leads</span>
                    <span style={styles.cMetaChip}>{c.sent} sent</span>
                    <span style={{ ...styles.cMetaChip, color: '#10b981', background: 'rgba(16,185,129,0.1)' }}>
                      {c.reply_rate}% reply
                    </span>
                  </div>
                </div>
                <ArrowRight size={14} color={selectedCampaign === c.id ? '#ff4500' : '#d1d5db'} />
              </div>
            ))}
            {(!global?.campaigns || global.campaigns.length === 0) && (
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', padding: '20px 0', textAlign: 'center' }}>
                No campaigns yet
              </p>
            )}
          </div>
        </Card>
      </div>

      {/* Campaign drill-down */}
      {campaignData && (
        <div style={{ marginTop: '24px' }} className="animate-in">
          <div style={styles.drillHeader}>
            <h2 style={styles.drillTitle}>{campaignData.campaign_name}</h2>
            <span style={styles.drillBadge}>Detailed Analytics</span>
          </div>

          <div style={styles.miniGrid}>
            {[
              { label: 'Leads', value: campaignData.overview.total_leads },
              { label: 'Emails', value: campaignData.overview.total_emails },
              { label: 'Pending', value: campaignData.overview.pending },
              { label: 'Approved', value: campaignData.overview.approved },
              { label: 'Sent', value: campaignData.overview.sent },
              { label: 'Open Rate', value: `${campaignData.overview.open_rate}%` },
              { label: 'Reply Rate', value: `${campaignData.overview.reply_rate}%` },
              { label: 'Replies', value: campaignData.total_replies },
            ].map((s) => (
              <div key={s.label} style={styles.miniStat}>
                <div style={styles.miniVal}>{s.value}</div>
                <div style={styles.miniLabel}>{s.label}</div>
              </div>
            ))}
          </div>

          <div style={styles.twoCol}>
            <Card>
              <h3 style={styles.cardTitle}><span style={styles.cardTitleDot} />By Email Type</h3>
              {Object.entries(campaignData.by_template_type).map(([type, data]) => (
                <BreakdownRow key={type} label={type.replace(/_/g,' ')} data={data} />
              ))}
              {Object.keys(campaignData.by_template_type).length === 0 && <EmptyNote />}
            </Card>
            <Card>
              <h3 style={styles.cardTitle}><span style={styles.cardTitleDot} />By Role</h3>
              {Object.entries(campaignData.by_role).map(([role, data]) => (
                <BreakdownRow key={role} label={role.toUpperCase()} data={data} />
              ))}
              {Object.keys(campaignData.by_role).length === 0 && <EmptyNote />}
            </Card>
          </div>

          <Card style={{ marginTop: '14px' }}>
            <h3 style={styles.cardTitle}><span style={styles.cardTitleDot} />Sequence Progress</h3>
            <div style={styles.seqGrid}>
              {Object.entries(campaignData.sequence_progress).map(([step, data]) => (
                <div key={step} style={styles.seqCard}>
                  <div style={styles.seqLabel}>{step.replace(/_/g,' ')}</div>
                  <div style={styles.seqStats}>
                    <SeqPill label="pending"  val={data.pending}  color="#ef4444" />
                    <SeqPill label="approved" val={data.approved} color="#10b981" />
                    <SeqPill label="sent"     val={data.sent}     color="#ff4500" />
                    <SeqPill label="replied"  val={data.replied}  color="#f59e0b" />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card style={{ marginTop: '14px' }}>
            <h3 style={styles.cardTitle}><span style={styles.cardTitleDot} />Lead Statuses</h3>
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

function StatCard({ icon: Icon, label, value, color, bg }) {
  return (
    <div style={{ ...styles.statCard, position: 'relative', overflow: 'hidden' }}>
      <span style={{ position:'absolute', top:0, left:0, right:0, height:'3px',
        background: `linear-gradient(90deg, ${color}, ${color}88)`,
        borderRadius:'16px 16px 0 0', opacity:0.7 }} />
      <div style={{ ...styles.statIcon, background: bg, color }}><Icon size={19} /></div>
      <div style={styles.statValue}>{value}</div>
      <div style={styles.statLabel}>{label}</div>
    </div>
  )
}

function BreakdownRow({ label, data }) {
  return (
    <div style={styles.breakdownRow}>
      <span style={styles.breakdownLabel}>{label}</span>
      <div style={styles.breakdownStats}>
        <span style={styles.bChip}>✉ {data.sent}</span>
        <span style={{ ...styles.bChip, color: '#10b981', background: 'rgba(16,185,129,0.08)' }}>👁 {data.opened}</span>
        <span style={{ ...styles.bChip, color: '#ff4500', background: 'rgba(255,69,0,0.08)' }}>↩ {data.replied}</span>
      </div>
    </div>
  )
}

function SeqPill({ label, val, color }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:'5px', fontSize:'11px' }}>
      <span style={{ fontWeight:700, color }}>{val}</span>
      <span style={{ color:'var(--text-muted)' }}>{label}</span>
    </div>
  )
}

function EmptyNote() {
  return <p style={{ fontSize:'13px', color:'var(--text-muted)', padding:'12px 0' }}>No data yet</p>
}

const styles = {
  pageHeader: { display:'flex', alignItems:'center', gap:'14px', marginBottom:'26px' },
  pageIconWrap: {
    width:'44px', height:'44px', borderRadius:'12px',
    background:'rgba(255,69,0,0.08)',
    display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0,
  },
  title: { fontSize:'24px', fontWeight:800, letterSpacing:'-0.3px' },
  subtitle: { fontSize:'13px', color:'var(--text-muted)', marginTop:'3px' },
  statsGrid: {
    display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(170px,1fr))',
    gap:'12px', marginBottom:'22px',
  },
  statCard: {
    background:'#fff', border:'1px solid var(--border)', borderRadius:'14px',
    padding:'18px', boxShadow:'var(--shadow-sm)',
  },
  statIcon: { width:'40px', height:'40px', borderRadius:'10px', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:'12px' },
  statValue: { fontSize:'22px', fontWeight:800, letterSpacing:'-0.5px' },
  statLabel: { fontSize:'11px', color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.6px', fontWeight:500, marginTop:'3px' },
  cardTitle: {
    fontSize:'14px', fontWeight:700, marginBottom:'4px', color:'#111',
    display:'flex', alignItems:'center', gap:'8px',
  },
  cardTitleDot: {
    width:'8px', height:'8px', borderRadius:'50%',
    background:'#ff4500', display:'inline-block', flexShrink:0,
  },
  cardSub: { fontSize:'12px', color:'var(--text-muted)', marginBottom:'18px' },
  funnel: { display:'flex', flexDirection:'column', gap:'10px' },
  funnelRow: { display:'grid', gridTemplateColumns:'90px 1fr 44px 60px', alignItems:'center', gap:'10px' },
  funnelLabelWrap: {},
  funnelLabel: { fontSize:'12px', color:'#374151', fontWeight:600 },
  funnelBarWrap: { position:'relative', height:'20px', background:'var(--bg-secondary)', borderRadius:'6px', overflow:'hidden' },
  funnelBar: { position:'absolute', left:0, top:0, bottom:0, borderRadius:'6px', transition:'width 0.6s ease' },
  funnelBarBg: {},
  funnelPct: { fontSize:'12px', fontWeight:700, textAlign:'right' },
  funnelVal: { fontSize:'12px', color:'var(--text-muted)', textAlign:'right' },
  twoCol: { display:'grid', gridTemplateColumns:'1fr 1fr', gap:'14px', marginBottom:'14px' },
  intentList: { display:'flex', flexDirection:'column', gap:'14px' },
  intentRow: { display:'flex', alignItems:'center', gap:'10px' },
  intentLeft: { width:'130px', display:'flex', alignItems:'center', gap:'8px', flexShrink:0 },
  intentDot: { width:'9px', height:'9px', borderRadius:'50%', flexShrink:0 },
  intentLabel: { fontSize:'13px', color:'#374151', fontWeight:500 },
  intentBarWrap: { flex:1, height:'10px', background:'var(--bg-secondary)', borderRadius:'6px', overflow:'hidden' },
  intentVal: { fontSize:'14px', fontWeight:800, width:'28px', textAlign:'right', flexShrink:0 },
  campaignList: { display:'flex', flexDirection:'column', gap:'2px', maxHeight:'260px', overflowY:'auto' },
  campaignRow: {
    display:'flex', alignItems:'center', gap:'10px', padding:'10px 10px',
    borderRadius:'10px', cursor:'pointer', transition:'background 0.15s',
  },
  campaignRowActive: { background:'rgba(255,69,0,0.06)', border:'1px solid rgba(255,69,0,0.15)' },
  cName: { fontSize:'13px', fontWeight:600, marginBottom:'4px', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' },
  cMeta: { display:'flex', gap:'5px', flexWrap:'wrap' },
  cMetaChip: {
    fontSize:'11px', fontWeight:600, padding:'2px 8px', borderRadius:'20px',
    background:'var(--bg-secondary)', color:'#6b7280',
  },
  drillHeader: { display:'flex', alignItems:'center', gap:'12px', marginBottom:'16px' },
  drillTitle: { fontSize:'18px', fontWeight:700 },
  drillBadge: {
    fontSize:'11px', fontWeight:700, padding:'4px 12px', borderRadius:'20px',
    background:'rgba(255,69,0,0.1)', color:'#ff4500',
  },
  miniGrid: {
    display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(130px,1fr))',
    gap:'10px', marginBottom:'16px',
  },
  miniStat: {
    background:'#fff', border:'1px solid var(--border)', borderRadius:'12px',
    padding:'14px 16px', textAlign:'center', boxShadow:'var(--shadow-sm)',
  },
  miniVal: { fontSize:'20px', fontWeight:800, letterSpacing:'-0.5px' },
  miniLabel: { fontSize:'10px', color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.6px', marginTop:'4px' },
  breakdownRow: {
    display:'flex', justifyContent:'space-between', alignItems:'center',
    padding:'10px 0', borderBottom:'1px solid var(--border)',
  },
  breakdownLabel: { fontSize:'13px', fontWeight:600, textTransform:'capitalize', color:'#374151' },
  breakdownStats: { display:'flex', gap:'8px', flexWrap:'wrap' },
  bChip: {
    fontSize:'11px', fontWeight:600, padding:'3px 9px', borderRadius:'6px',
    background:'var(--bg-secondary)', color:'#6b7280',
  },
  seqGrid: { display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(180px,1fr))', gap:'12px', marginTop:'4px' },
  seqCard: {
    background:'var(--bg-secondary)', borderRadius:'10px', padding:'14px',
    border:'1px solid var(--border)',
  },
  seqLabel: { fontSize:'12px', fontWeight:700, textTransform:'capitalize', marginBottom:'10px', color:'#374151' },
  seqStats: { display:'flex', flexDirection:'column', gap:'5px' },
  statusRow: { display:'flex', flexWrap:'wrap', gap:'8px', marginTop:'4px' },
  statusChip: {
    display:'flex', flexDirection:'column', alignItems:'center',
    padding:'10px 16px', borderRadius:'10px',
    background:'var(--bg-secondary)', border:'1px solid var(--border)',
    minWidth:'70px',
  },
  statusCount: { fontSize:'18px', fontWeight:800 },
  statusLabel: { fontSize:'10px', color:'var(--text-muted)', textTransform:'capitalize', marginTop:'2px', fontWeight:500 },
}
