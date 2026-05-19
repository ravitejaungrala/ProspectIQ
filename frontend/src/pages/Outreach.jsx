import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Send, Mail, Linkedin, ChevronDown, ChevronRight,
  CheckCircle, Eye, Layout, User, ShieldCheck, CheckCheck
} from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import StatusBadge from '../components/StatusBadge'
import {
  getCampaign, getCampaignOutreach, markStepSent, sendCampaignEmails,
  getTemplateTypes, getStepPreviewUrl, getTemplatePreviewUrl,
  approveStep, approveAllSteps
} from '../api/client'
import toast from 'react-hot-toast'

const GROUP_CONFIG = {
  cold_email: { label: 'Cold Emails', icon: Mail, color: '#ff4500', desc: 'Day 0 — First touch, branded HTML, role-specific personalization' },
  follow_up:  { label: 'Follow-Up Emails', icon: Mail, color: '#16a34a', desc: 'Day 3, 7 & 10 — Fresh angle, new data, case study' },
  breakup:    { label: 'Breakup Emails', icon: Mail, color: '#dc2626', desc: 'Day 15 — Final call, short & direct — highest reply rate' },
  linkedin:   { label: 'LinkedIn Messages', icon: Linkedin, color: '#2563eb', desc: 'Day 16 — Short connection message' },
}

export default function Outreach() {
  const { campaignId } = useParams()
  const navigate = useNavigate()
  const [campaign, setCampaign] = useState(null)
  const [steps, setSteps] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedGroups, setExpandedGroups] = useState({})
  const [expandedStep, setExpandedStep] = useState(null)
  const [viewMode, setViewMode] = useState('html')
  const [showTemplates, setShowTemplates] = useState(false)
  const [templateTypes, setTemplateTypes] = useState(null)
  const [selectedType, setSelectedType] = useState('cold_email')
  const [selectedRole, setSelectedRole] = useState('ceo')
  const [sendingAll, setSendingAll] = useState(false)

  useEffect(() => {
    Promise.all([
      getCampaign(campaignId),
      getCampaignOutreach(campaignId),
    ]).then(([c, s]) => {
      setCampaign(c)
      setSteps(s)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [campaignId])

  const loadTemplateTypes = async () => {
    if (!templateTypes) {
      try {
        const data = await getTemplateTypes()
        setTemplateTypes(data)
      } catch (err) { toast.error('Failed to load templates') }
    }
    setShowTemplates(!showTemplates)
  }

  const handleSend = async (stepId) => {
    try {
      await markStepSent(stepId)
      toast.success('Marked as sent!')
      setSteps(steps.map(s => s.id === stepId ? { ...s, status: 'sent', sent_at: new Date().toISOString() } : s))
    } catch (err) { toast.error(err.message) }
  }

  const handleApprove = async (stepId) => {
    try {
      await approveStep(stepId)
      toast.success('Email approved!')
      setSteps(steps.map(s => s.id === stepId ? { ...s, status: 'approved', approved: true } : s))
    } catch (err) { toast.error(err.message) }
  }

  const handleApproveAll = async () => {
    try {
      const result = await approveAllSteps(campaignId)
      toast.success(result.message)
      setSteps(steps.map(s => s.status === 'pending' ? { ...s, status: 'approved', approved: true } : s))
    } catch (err) { toast.error(err.message) }
  }

  const handleSendAll = async () => {
    setSendingAll(true)
    try {
      const result = await sendCampaignEmails(campaignId)
      toast.success(`${result.sent} emails sent, ${result.failed} failed`)
      // Reload steps to reflect new statuses
      const updated = await getCampaignOutreach(campaignId)
      setSteps(updated)
    } catch (err) { toast.error(err.message) }
    finally { setSendingAll(false) }
  }

  const toggleGroup = (type) => {
    setExpandedGroups(prev => ({ ...prev, [type]: !prev[type] }))
  }

  if (loading) return <div style={styles.loading}>Loading...</div>

  // Group steps by template type
  const groupOrder = ['cold_email', 'follow_up', 'breakup', 'linkedin']
  const groupedByType = {}
  steps.forEach(step => {
    const type = step.template_type || step.step_type || 'cold_email'
    const key = groupOrder.includes(type) ? type : 'cold_email'
    if (!groupedByType[key]) groupedByType[key] = []
    groupedByType[key].push(step)
  })

  const pendingCount = steps.filter(s => s.status === 'pending').length
  const approvedCount = steps.filter(s => s.status === 'approved').length
  const sentCount = steps.filter(s => s.status === 'sent').length

  return (
    <div>
      <button onClick={() => navigate(`/campaigns/${campaignId}`)} style={styles.back}>
        <ArrowLeft size={16} /> Back to Campaign
      </button>

      <div style={styles.headerRow}>
        <div>
          <h1 style={styles.title}>Stage 4 — Outreach Sequence</h1>
          <p style={styles.subtitle}>
            {campaign?.product_name} — {steps.length} steps · {pendingCount} pending · {approvedCount} approved · {sentCount} sent
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {pendingCount > 0 && (
            <Button variant="success" onClick={handleApproveAll}>
              <CheckCheck size={14} /> Approve All ({pendingCount})
            </Button>
          )}
          {approvedCount > 0 && (
            <Button variant="primary" onClick={handleSendAll} disabled={sendingAll}>
              <Send size={14} /> {sendingAll ? 'Sending...' : `Send All Approved (${approvedCount})`}
            </Button>
          )}
          <Button variant="secondary" onClick={loadTemplateTypes}>
            <Layout size={14} /> {showTemplates ? 'Hide' : 'Browse'} Templates
          </Button>
        </div>
      </div>

      {/* Template Browser */}
      {showTemplates && templateTypes && (
        <Card style={{ marginBottom: '24px' }}>
          <h3 style={styles.cardTitle}>Template Preview</h3>
          <div style={styles.templateControls}>
            <div style={styles.controlGroup}>
              <label style={styles.controlLabel}>Email Type</label>
              <div style={styles.chipRow}>
                {templateTypes.template_types.map(t => (
                  <button key={t.id}
                    style={{ ...styles.chip, ...(selectedType === t.id ? styles.chipActive : {}) }}
                    onClick={() => setSelectedType(t.id)} title={t.description}
                  ><Mail size={12} /> {t.label}</button>
                ))}
              </div>
            </div>
            <div style={styles.controlGroup}>
              <label style={styles.controlLabel}>Recipient Role</label>
              <div style={styles.chipRow}>
                {templateTypes.role_categories.map(r => (
                  <button key={r.id}
                    style={{ ...styles.chip, ...(selectedRole === r.id ? styles.chipActive : {}) }}
                    onClick={() => setSelectedRole(r.id)} title={r.description}
                  ><User size={12} /> {r.label}</button>
                ))}
              </div>
            </div>
          </div>
          <div style={styles.previewFrame}>
            <iframe key={`${selectedType}-${selectedRole}`}
              src={getTemplatePreviewUrl(selectedType, selectedRole, campaignId)}
              style={styles.iframe} title="Template Preview"
            />
          </div>
        </Card>
      )}

      {/* Grouped Step Boxes */}
      {groupOrder.map(type => {
        const groupSteps = groupedByType[type]
        if (!groupSteps || groupSteps.length === 0) return null
        const config = GROUP_CONFIG[type] || GROUP_CONFIG.cold_email
        const Icon = config.icon
        const isOpen = expandedGroups[type]
        const gPending = groupSteps.filter(s => s.status === 'pending').length
        const gApproved = groupSteps.filter(s => s.status === 'approved').length
        const gSent = groupSteps.filter(s => s.status === 'sent').length

        return (
          <div key={type} style={styles.groupBox}>
            {/* Group Header */}
            <div style={styles.groupHeader} onClick={() => toggleGroup(type)}>
              <div style={styles.groupLeft}>
                <div style={{ ...styles.groupIcon, background: `${config.color}20`, color: config.color }}>
                  <Icon size={18} />
                </div>
                <div>
                  <div style={styles.groupTitle}>{config.label}</div>
                  <div style={styles.groupDesc}>{config.desc}</div>
                </div>
              </div>
              <div style={styles.groupRight}>
                <div style={styles.groupStats}>
                  <span style={styles.groupCount}>{groupSteps.length} emails</span>
                  {gPending > 0 && <span style={{ ...styles.miniTag, background: 'rgba(220,38,38,0.08)', color: '#dc2626' }}>{gPending} pending</span>}
                  {gApproved > 0 && <span style={{ ...styles.miniTag, background: 'rgba(22,163,74,0.08)', color: '#16a34a' }}>{gApproved} approved</span>}
                  {gSent > 0 && <span style={{ ...styles.miniTag, background: 'rgba(255,69,0,0.08)', color: '#ff4500' }}>{gSent} sent</span>}
                </div>
                {isOpen ? <ChevronDown size={18} color="var(--text-muted)" /> : <ChevronRight size={18} color="var(--text-muted)" />}
              </div>
            </div>

            {/* Expanded: individual emails */}
            {isOpen && (
              <div style={styles.groupBody}>
                {groupSteps.map(step => (
                  <div key={step.id} style={styles.stepCard}>
                    <div style={styles.stepHeader} onClick={() => setExpandedStep(expandedStep === step.id ? null : step.id)}>
                      <div style={styles.stepLeft}>
                        <div style={styles.stepDay}>Day {step.step_number}</div>
                        <div style={styles.stepInfo}>
                          <div style={styles.stepSubject}>{step.subject || '(LinkedIn message)'}</div>
                          <div style={styles.stepMeta}>
                            {step.role_category && step.role_category !== 'general' && (
                              <span style={styles.roleBadge}>{step.role_category.toUpperCase()}</span>
                            )}
                            <StatusBadge status={step.status} />
                          </div>
                        </div>
                      </div>
                      <div style={styles.stepActions}>
                        {step.html_body && (
                          <Button size="sm" variant="secondary"
                            onClick={(e) => { e.stopPropagation(); setExpandedStep(expandedStep === step.id ? null : step.id); setViewMode('html') }}
                          ><Eye size={12} /> Preview</Button>
                        )}
                        {step.status === 'pending' && (
                          <Button size="sm" variant="success"
                            onClick={(e) => { e.stopPropagation(); handleApprove(step.id) }}
                          ><ShieldCheck size={12} /> Approve</Button>
                        )}
                        {(step.status === 'approved' || step.approved) && step.status !== 'sent' && (
                          <Button size="sm" variant="primary"
                            onClick={(e) => { e.stopPropagation(); handleSend(step.id) }}
                          ><Send size={12} /> Send</Button>
                        )}
                        {step.status === 'sent' && <CheckCircle size={16} color="var(--success)" />}
                        {expandedStep === step.id ? <ChevronDown size={16} color="var(--text-muted)" /> : <ChevronRight size={16} color="var(--text-muted)" />}
                      </div>
                    </div>

                    {/* Expanded step content */}
                    {expandedStep === step.id && (
                      <div style={styles.stepExpanded}>
                        <div style={styles.viewToggle}>
                          <button style={{ ...styles.toggleBtn, ...(viewMode === 'text' ? styles.toggleActive : {}) }}
                            onClick={() => setViewMode('text')}>Plain Text</button>
                          {step.html_body && (
                            <button style={{ ...styles.toggleBtn, ...(viewMode === 'html' ? styles.toggleActive : {}) }}
                              onClick={() => setViewMode('html')}>HTML Preview</button>
                          )}
                        </div>
                        {viewMode === 'text' ? (
                          <div style={styles.emailPreview}>
                            {step.subject && <div style={styles.emailSubject}>Subject: {step.subject}</div>}
                            <div style={styles.emailBody}>{step.body}</div>
                          </div>
                        ) : step.html_body ? (
                          <div style={styles.previewFrame}>
                            <iframe src={getStepPreviewUrl(step.id)} style={styles.iframe} title={`Preview ${step.id}`} />
                          </div>
                        ) : (
                          <div style={styles.emailPreview}>
                            <div style={styles.emailBody}>{step.body}</div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
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
  headerRow: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px',
  },
  title: { fontSize: '24px', fontWeight: 700 },
  subtitle: { fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' },
  cardTitle: { fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '16px' },
  templateControls: { marginBottom: '16px' },
  controlGroup: { marginBottom: '12px' },
  controlLabel: { fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', display: 'block' },
  chipRow: { display: 'flex', flexWrap: 'wrap', gap: '6px' },
  chip: {
    display: 'flex', alignItems: 'center', gap: '4px',
    padding: '6px 12px', borderRadius: '16px', fontSize: '12px',
    background: 'var(--bg-secondary)', border: '1px solid var(--border)',
    color: 'var(--text-secondary)', cursor: 'pointer', whiteSpace: 'nowrap',
  },
  chipActive: {
    background: 'rgba(255, 69, 0, 0.08)', borderColor: 'var(--accent-light)', color: 'var(--accent-light)',
  },
  previewFrame: {
    background: '#fff', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border)',
  },
  iframe: { width: '100%', height: '600px', border: 'none' },

  // ─── Group box ────────────────────────────────
  groupBox: {
    background: 'var(--bg-card)', border: '1px solid var(--border)',
    borderRadius: '12px', marginBottom: '16px', overflow: 'hidden',
  },
  groupHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '16px 20px', cursor: 'pointer', userSelect: 'none',
  },
  groupLeft: { display: 'flex', alignItems: 'center', gap: '14px' },
  groupIcon: {
    width: '40px', height: '40px', borderRadius: '10px',
    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
  },
  groupTitle: { fontSize: '16px', fontWeight: 700 },
  groupDesc: { fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' },
  groupRight: { display: 'flex', alignItems: 'center', gap: '12px' },
  groupStats: { display: 'flex', gap: '6px', alignItems: 'center' },
  groupCount: { fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 },
  miniTag: {
    padding: '2px 8px', borderRadius: '10px', fontSize: '11px', fontWeight: 600,
  },
  groupBody: {
    borderTop: '1px solid var(--border)', padding: '8px 12px 12px',
  },

  // ─── Individual step card ────────────────────
  stepCard: {
    background: 'var(--bg-primary)', border: '1px solid var(--border)',
    borderRadius: '8px', marginBottom: '8px', overflow: 'hidden',
  },
  stepHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '12px 16px', cursor: 'pointer',
  },
  stepLeft: { display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 },
  stepDay: {
    fontSize: '12px', fontWeight: 700, color: 'var(--accent-light)',
    background: 'rgba(255, 69, 0, 0.08)', padding: '4px 10px', borderRadius: '6px',
    whiteSpace: 'nowrap',
  },
  stepInfo: { flex: 1, minWidth: 0 },
  stepSubject: {
    fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)',
    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
  },
  stepMeta: { display: 'flex', gap: '8px', marginTop: '4px', alignItems: 'center' },
  stepActions: { display: 'flex', gap: '6px', alignItems: 'center', flexShrink: 0, marginLeft: '12px' },
  roleBadge: {
    display: 'inline-block', padding: '2px 8px', borderRadius: '4px',
    fontSize: '10px', fontWeight: 700, letterSpacing: '0.05em',
    background: 'rgba(255, 69, 0, 0.08)', color: '#ff4500',
  },
  stepExpanded: {
    padding: '12px 16px 16px', borderTop: '1px solid var(--border)',
    background: 'var(--bg-secondary)',
  },
  viewToggle: { display: 'flex', gap: '4px', marginBottom: '12px' },
  toggleBtn: {
    padding: '6px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 500,
    background: 'var(--bg-primary)', border: '1px solid var(--border)',
    color: 'var(--text-secondary)', cursor: 'pointer',
  },
  toggleActive: {
    background: 'rgba(255, 69, 0, 0.08)', borderColor: 'var(--accent-light)', color: 'var(--accent-light)',
  },
  emailPreview: {
    background: 'var(--bg-primary)', borderRadius: '8px', padding: '16px', maxWidth: '600px',
  },
  emailSubject: {
    fontSize: '13px', fontWeight: 600, marginBottom: '8px',
    paddingBottom: '8px', borderBottom: '1px solid var(--border)',
  },
  emailBody: {
    fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap',
  },
}
