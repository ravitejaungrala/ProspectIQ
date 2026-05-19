import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Users, Send, CheckCircle, Play, RefreshCw, BarChart3, ExternalLink, Phone, Mail, Calendar, Video
} from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import StatusBadge from '../components/StatusBadge'
import StageIndicator from '../components/StageIndicator'
import {
  getCampaign, getCampaignLeads, findLeads, verifyLeads, enrollLeads
} from '../api/client'
import toast from 'react-hot-toast'

export default function CampaignDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [campaign, setCampaign] = useState(null)
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState('')
  const [targetDomains, setTargetDomains] = useState('')
  const [manualDomains, setManualDomains] = useState('')
  const [targetRoles, setTargetRoles] = useState('')

  const load = async () => {
    try {
      const [c, l] = await Promise.all([
        getCampaign(id),
        getCampaignLeads(id).catch(() => []),
      ])
      setCampaign(c)
      setLeads(l)
    } catch (err) {
      toast.error('Failed to load campaign')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  // Auto-refresh while campaign is processing (setup status)
  useEffect(() => {
    if (!campaign || campaign.status !== 'setup') return
    const interval = setInterval(() => { load() }, 3000)
    return () => clearInterval(interval)
  }, [campaign?.status])

  // Auto-populate target domains and roles from AI analysis
  useEffect(() => {
    if (campaign?.target_domains?.length > 0 && !targetDomains) {
      setTargetDomains(campaign.target_domains.join(', '))
    }
  }, [campaign?.target_domains])

  useEffect(() => {
    if (campaign?.roles?.length > 0 && !targetRoles) {
      setTargetRoles(campaign.roles.join(', '))
    }
  }, [campaign?.roles])

  const handleFindLeads = async () => {
    // Merge AI-suggested domains + manually added domains
    const aiDomains = targetDomains.split(/[,\n]+/).map(d => d.trim()).filter(Boolean)
    const userDomains = manualDomains.split(/[,\n]+/).map(d => d.trim()).filter(Boolean)
    const domains = [...new Set([...aiDomains, ...userDomains])]
    if (domains.length === 0) {
      toast.error('Please enter at least one target company domain (e.g. google.com)')
      return
    }
    const roles = targetRoles.split(/[,\n]+/).map(r => r.trim()).filter(Boolean)
    setActionLoading('find')
    try {
      const newLeads = await findLeads(id, {
        domains,
        roles: roles.length > 0 ? roles : campaign.roles,
        limit: 50,
      })
      toast.success(`Found ${newLeads.length} new leads!`)
      await load()
    } catch (err) {
      toast.error(err.message)
    } finally {
      setActionLoading('')
    }
  }

  const handleVerify = async () => {
    setActionLoading('verify')
    try {
      await verifyLeads(id)
      toast.success('Verification started! Leads are being processed...')
      // Poll for updates
      setTimeout(load, 3000)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setActionLoading('')
    }
  }

  const handleEnroll = async () => {
    setActionLoading('enroll')
    try {
      const result = await enrollLeads(id)
      toast.success(result.message)
      await load()
    } catch (err) {
      toast.error(err.message)
    } finally {
      setActionLoading('')
    }
  }

  if (loading) return <div style={styles.loading}>Loading...</div>
  if (!campaign) return <div style={styles.loading}>Campaign not found</div>

  const cleanLeads = leads.filter(l => l.status === 'clean').length
  const droppedLeads = leads.filter(l => l.status === 'dropped').length
  const enrolledLeads = leads.filter(l => ['enrolled', 'contacted'].includes(l.status)).length

  return (
    <div>
      <button onClick={() => navigate('/campaigns')} style={styles.back}>
        <ArrowLeft size={16} /> Back to Campaigns
      </button>

      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>{campaign.product_name || 'Processing...'}</h1>
          <p style={styles.url}>{campaign.product_url}</p>
        </div>
        <StatusBadge status={campaign.status} size="lg" />
      </div>

      <StageIndicator currentStage={campaign.status} />

      {/* Product Info */}
      <div style={styles.grid}>
        <Card>
          <h3 style={styles.cardTitle}>Product Summary</h3>
          <p style={styles.cardText}>{campaign.product_summary || 'AI is analyzing your product...'}</p>
        </Card>

        <Card>
          <h3 style={styles.cardTitle}>Ideal Customer Profile</h3>
          {campaign.ideal_customer_profile && Object.keys(campaign.ideal_customer_profile).length > 0 ? (
            <div style={styles.icpGrid}>
              {Object.entries(campaign.ideal_customer_profile).map(([key, value]) => (
                <div key={key}>
                  <div style={styles.icpLabel}>{key.replace(/_/g, ' ')}</div>
                  <div style={styles.icpValue}>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</div>
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.cardText}>Analyzing...</p>
          )}
        </Card>
      </div>

      <div style={styles.grid}>
        <Card>
          <h3 style={styles.cardTitle}>Target Industries</h3>
          <div style={styles.tags}>
            {(campaign.industries || []).map((ind) => (
              <span key={ind} style={styles.tag}>{ind}</span>
            ))}
            {(!campaign.industries || campaign.industries.length === 0) && (
              <span style={styles.cardText}>Analyzing...</span>
            )}
          </div>
        </Card>
        <Card>
          <h3 style={styles.cardTitle}>Target Roles</h3>
          {campaign.roles?.length > 0 ? (
            <div>
              <div style={styles.tags}>
                {campaign.roles.map((role) => (
                  <span key={role} style={styles.tag}>{role}</span>
                ))}
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>AI-generated from your product · Editable below in Pipeline Actions</p>
            </div>
          ) : (
            <span style={styles.cardText}>Analyzing...</span>
          )}
        </Card>
      </div>

      <Card style={{ marginBottom: '16px' }}>
        <h3 style={styles.cardTitle}>Pain Points</h3>
        <div style={styles.tags}>
          {(campaign.pain_points || []).map((pp, i) => (
            <span key={i} style={{ ...styles.tag, background: 'rgba(220, 38, 38, 0.08)', color: '#dc2626' }}>
              {pp}
            </span>
          ))}
        </div>
      </Card>

      {/* AI-Suggested Target Companies */}
      {campaign.target_domains && campaign.target_domains.length > 0 && (
        <Card style={{ marginBottom: '16px' }}>
          <h3 style={styles.cardTitle}>AI-Suggested Target Companies</h3>
          <div style={styles.tags}>
            {campaign.target_domains.map((d, i) => (
              <span key={i} style={{ ...styles.tag, background: 'rgba(22, 163, 74, 0.08)', color: '#16a34a' }}>
                {d}
              </span>
            ))}
          </div>
        </Card>
      )}

      {/* Scraped Data — Demo, Calendly, Contact, Social */}
      {(campaign.demo_video_url || campaign.calendly_url || campaign.demo_booking_url || (campaign.contact_emails && campaign.contact_emails.length) || campaign.product_phone) && (
        <Card style={{ marginBottom: '16px' }}>
          <h3 style={styles.cardTitle}>Scraped Data</h3>
          <div style={styles.scrapedGrid}>
            {campaign.demo_video_url && (
              <div style={styles.scrapedItem}>
                <Video size={14} color="#ff4500" />
                <a href={campaign.demo_video_url} target="_blank" rel="noopener noreferrer" style={styles.scrapedLink}>
                  Demo Video
                </a>
              </div>
            )}
            {campaign.calendly_url && (
              <div style={styles.scrapedItem}>
                <Calendar size={14} color="#ff4500" />
                <a href={campaign.calendly_url} target="_blank" rel="noopener noreferrer" style={styles.scrapedLink}>
                  Calendly / Book Demo
                </a>
              </div>
            )}
            {campaign.demo_booking_url && campaign.demo_booking_url !== campaign.calendly_url && (
              <div style={styles.scrapedItem}>
                <ExternalLink size={14} color="#16a34a" />
                <a href={campaign.demo_booking_url} target="_blank" rel="noopener noreferrer" style={styles.scrapedLink}>
                  Demo Booking Page
                </a>
              </div>
            )}
            {campaign.product_phone && (
              <div style={styles.scrapedItem}>
                <Phone size={14} color="#16a34a" />
                <span style={styles.scrapedText}>{campaign.product_phone}</span>
              </div>
            )}
            {(campaign.contact_emails || []).map((email, i) => (
              <div key={i} style={styles.scrapedItem}>
                <Mail size={14} color="#2563eb" />
                <span style={styles.scrapedText}>{email}</span>
              </div>
            ))}
            {campaign.social_links && Object.entries(campaign.social_links).map(([name, url]) => (
              <div key={name} style={styles.scrapedItem}>
                <ExternalLink size={14} color="#ff4500" />
                <a href={url} target="_blank" rel="noopener noreferrer" style={styles.scrapedLink}>
                  {name}
                </a>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Actions */}
      <Card style={{ marginBottom: '16px' }}>
        <h3 style={styles.cardTitle}>Pipeline Actions</h3>

        {/* Target Roles Input */}
        <div style={{ marginBottom: '20px' }}>
          <label style={styles.inputLabel}>
            Target Roles
            {campaign?.roles?.length > 0 && (
              <span style={{ color: 'var(--success)', fontWeight: 400, textTransform: 'none', letterSpacing: 0, marginLeft: '8px' }}>
                ✓ AI suggested {campaign.roles.length} roles based on your product
              </span>
            )}
          </label>
          <textarea
            value={targetRoles}
            onChange={(e) => setTargetRoles(e.target.value)}
            placeholder="Enter target job roles separated by commas&#10;e.g. VP of Sales, CTO, Head of Marketing"
            style={styles.domainInput}
            rows={2}
          />
          <p style={styles.inputHint}>AI-generated roles from your product analysis — edit or add more to refine your search</p>
        </div>

        {/* Target Company Domains Input */}
        <div style={{ marginBottom: '16px' }}>
          <label style={styles.inputLabel}>
            AI-Suggested Company Domains
            {campaign?.target_domains?.length > 0 && (
              <span style={{ color: 'var(--success)', fontWeight: 400, textTransform: 'none', letterSpacing: 0, marginLeft: '8px' }}>
                ✓ AI suggested {campaign.target_domains.length} companies
              </span>
            )}
          </label>
          <textarea
            value={targetDomains}
            onChange={(e) => setTargetDomains(e.target.value)}
            placeholder="AI-suggested domains will appear here..."
            style={styles.domainInput}
            rows={3}
          />
        </div>

        {/* Manual Domain Input */}
        <div style={{ marginBottom: '16px' }}>
          <label style={styles.inputLabel}>
            Add Your Own Companies
          </label>
          <textarea
            value={manualDomains}
            onChange={(e) => setManualDomains(e.target.value)}
            placeholder="Add company domains manually, separated by commas or new lines&#10;e.g. freshworks.com, zoho.com, razorpay.com"
            style={{ ...styles.domainInput, borderColor: '#ff4500', borderStyle: 'dashed' }}
            rows={2}
          />
          <p style={styles.inputHint}>These will be merged with AI suggestions — Hunter.io will find real contacts at all listed companies</p>
        </div>

        <div style={styles.actions}>
          <Button
            onClick={handleFindLeads}
            disabled={actionLoading === 'find' || campaign.status === 'setup'}
            variant="primary"
          >
            <Users size={16} />
            {actionLoading === 'find' ? 'Finding...' : `Find Leads (Stage 2)`}
          </Button>

          <Button
            onClick={handleVerify}
            disabled={actionLoading === 'verify' || leads.length === 0}
            variant="secondary"
          >
            <CheckCircle size={16} />
            {actionLoading === 'verify' ? 'Verifying...' : 'Verify & Score (Stage 3)'}
          </Button>

          <Button
            onClick={handleEnroll}
            disabled={actionLoading === 'enroll' || cleanLeads === 0}
            variant="success"
          >
            <Send size={16} />
            {actionLoading === 'enroll' ? 'Enrolling...' : `Enroll ${cleanLeads} Leads (Stage 4)`}
          </Button>

          <Button onClick={load} variant="ghost">
            <RefreshCw size={16} /> Refresh
          </Button>
        </div>
      </Card>

      {/* Lead Summary */}
      <div style={styles.header}>
        <h2 style={styles.sectionTitle}>
          Leads ({leads.length})
        </h2>
        {leads.length > 0 && (
          <div style={styles.leadStats}>
            <span style={styles.leadStat}>Clean: {cleanLeads}</span>
            <span style={styles.leadStat}>Enrolled: {enrolledLeads}</span>
            <span style={styles.leadStat}>Dropped: {droppedLeads}</span>
          </div>
        )}
      </div>

      {leads.length > 0 ? (
        <div style={styles.table}>
          <div style={styles.tableHeader}>
            <span style={styles.thName}>Name</span>
            <span style={styles.thCompany}>Company</span>
            <span style={styles.thTitle}>Title</span>
            <span style={styles.thEmail}>Email</span>
            <span style={styles.thScore}>Score</span>
            <span style={styles.thStatus}>Status</span>
          </div>
          {leads.map((lead) => (
            <div key={lead.id} style={styles.tableRow}>
              <span style={styles.tdName}>{lead.first_name} {lead.last_name}</span>
              <span style={styles.tdCompany}>{lead.company}</span>
              <span style={styles.tdTitle}>{lead.title}</span>
              <span style={styles.tdEmail}>{lead.email}</span>
              <span style={styles.tdScore}>
                <span style={{
                  ...styles.scoreBadge,
                  background: lead.profile_score >= 70 ? 'rgba(22,163,74,0.1)' :
                    lead.profile_score >= 40 ? 'rgba(217,119,6,0.1)' : 'rgba(220,38,38,0.1)',
                  color: lead.profile_score >= 70 ? '#16a34a' :
                    lead.profile_score >= 40 ? '#d97706' : '#dc2626',
                }}>
                  {lead.profile_score}
                </span>
              </span>
              <span style={styles.tdStatus}>
                <StatusBadge status={lead.status} />
              </span>
            </div>
          ))}
        </div>
      ) : (
        <Card>
          <div style={styles.empty}>
            <p style={{ color: 'var(--text-secondary)' }}>
              No leads yet. Click "Find Leads" to search for prospects.
            </p>
          </div>
        </Card>
      )}

      {/* View outreach button */}
      {enrolledLeads > 0 && (
        <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
          <Button onClick={() => navigate(`/outreach/${id}`)} variant="primary" size="lg">
            <Send size={16} /> View Outreach Sequence
          </Button>
          <Button onClick={() => navigate('/analytics')} variant="secondary" size="lg">
            <BarChart3 size={16} /> View Analytics
          </Button>
        </div>
      )}
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
    fontSize: '14px', cursor: 'pointer', marginBottom: '16px',
    padding: 0,
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
    marginBottom: '8px',
  },
  title: { fontSize: '24px', fontWeight: 700 },
  url: { fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' },
  grid: {
    display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px',
  },
  cardTitle: { fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-secondary)' },
  cardText: { fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.7 },
  icpGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' },
  icpLabel: { fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' },
  icpValue: { fontSize: '14px', color: 'var(--text-primary)', marginTop: '2px' },
  tags: { display: 'flex', flexWrap: 'wrap', gap: '8px' },
  tag: {
    padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 500,
    background: 'rgba(255, 69, 0, 0.08)', color: 'var(--accent-light)',
  },
  scrapedGrid: { display: 'flex', flexWrap: 'wrap', gap: '16px' },
  scrapedItem: { display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' },
  scrapedLink: { color: 'var(--accent-light)', textDecoration: 'none' },
  scrapedText: { color: 'var(--text-secondary)' },
  actions: { display: 'flex', gap: '12px', flexWrap: 'wrap' },
  sectionTitle: { fontSize: '18px', fontWeight: 600 },
  leadStats: { display: 'flex', gap: '12px' },
  leadStat: { fontSize: '13px', color: 'var(--text-secondary)' },
  table: {
    background: 'var(--bg-card)', border: '1px solid var(--border)',
    borderRadius: '12px', overflow: 'hidden',
  },
  tableHeader: {
    display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr 1.5fr 0.5fr 0.8fr',
    padding: '12px 20px', background: 'var(--bg-secondary)',
    borderBottom: '1px solid var(--border)',
    fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.05em',
  },
  tableRow: {
    display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr 1.5fr 0.5fr 0.8fr',
    padding: '12px 20px', borderBottom: '1px solid var(--border)',
    fontSize: '13px', alignItems: 'center',
  },
  thName: {}, thCompany: {}, thTitle: {}, thEmail: {}, thScore: {}, thStatus: {},
  tdName: { fontWeight: 500 },
  tdCompany: { color: 'var(--text-secondary)' },
  tdTitle: { color: 'var(--text-secondary)' },
  tdEmail: { color: 'var(--accent-light)', fontSize: '12px' },
  tdScore: {},
  tdStatus: {},
  scoreBadge: {
    padding: '2px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600,
  },
  empty: {
    display: 'flex', justifyContent: 'center', padding: '32px',
  },
  inputLabel: {
    fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px', display: 'block',
  },
  domainInput: {
    width: '100%', padding: '10px 14px', borderRadius: '8px', fontSize: '13px',
    background: 'var(--bg-primary)', border: '1px solid var(--border)',
    color: 'var(--text-primary)', resize: 'vertical', fontFamily: 'inherit',
    lineHeight: 1.6, boxSizing: 'border-box',
  },
  inputHint: {
    fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px',
  },
}
