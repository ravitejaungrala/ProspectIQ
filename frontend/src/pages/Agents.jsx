import { useEffect, useState } from 'react'
import {
  Bot, MessageSquare, Send, BarChart3, BookOpen, Play, RefreshCw,
  ChevronDown, ChevronRight, CheckCircle, Clock, AlertTriangle,
  Zap, ArrowRight, HelpCircle, Search, Users, Sparkles, Mail,
  PhoneCall, Calendar, Target, TrendingUp, Star, User
} from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import {
  getCampaigns, getAgentOverview, getAgentLogs,
  // Research Agent
  researchAllLeads, researchLead, researchCompany,
  // KP Agent
  scoreLeads, getKeyPersons, flagWeakLeads,
  // Personalization Agent
  batchPersonalize, previewPersonalization,
  // Outreach Agent
  getSendQueue, batchApproveAndSend, runFullPipeline, getOutreachStats,
  // Response Handling Agent
  getResponseQueue, autoRespond, handleAllUnhandled,
  // Booking Agent
  getHotLeads, sendBookingLink, confirmBooking, followUpUnbooked, getBookingPipeline,
  // Legacy
  getNoReplyLeads, autoAdvanceSequence, analyzePerformance,
  buildContext, askContextQuestion, processReply,
} from '../api/client'
import toast from 'react-hot-toast'

const AGENTS = [
  {
    key: 'research_agent',
    label: 'Research Agent',
    icon: Search,
    color: '#7c3aed',
    desc: 'Scrapes and AI-analyzes every target company — extracts tech stack, recent news, pain points, and personalization hooks for each lead',
  },
  {
    key: 'kp_agent',
    label: 'KP & Leads Identifying Agent',
    icon: Users,
    color: '#0891b2',
    desc: 'Identifies Key Decision-Makers at every company, scores each lead 0–100 against your ICP, and surfaces the best contact per domain',
  },
  {
    key: 'personalization_agent',
    label: 'Email Personalization Agent',
    icon: Sparkles,
    color: '#d97706',
    desc: 'Generates hyper-personalized opening lines and email content for every lead using research intel — no two emails are the same',
  },
  {
    key: 'outreach_agent',
    label: 'Outreach Agent',
    icon: Send,
    color: '#16a34a',
    desc: 'Orchestrates the full send pipeline — approves, queues, and sends emails with priority scoring; runs the complete pipeline in one click',
  },
  {
    key: 'response_handling_agent',
    label: 'Response Handling Agent',
    icon: MessageSquare,
    color: '#ff4500',
    desc: 'Monitors all incoming replies, classifies intent (schedule call, pricing, objections, demo), generates smart responses, and auto-handles low-risk replies',
  },
  {
    key: 'booking_agent',
    label: 'Client Booking Agent',
    icon: Calendar,
    color: '#0369a1',
    desc: 'Converts hot leads into booked meetings — surfaces buying signals, sends Calendly links, follows up unbooked prospects, and tracks the full booking funnel',
  },
]

export default function Agents() {
  const [campaigns, setCampaigns] = useState([])
  const [selectedCampaign, setSelectedCampaign] = useState('')
  const [overview, setOverview] = useState(null)
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedAgent, setExpandedAgent] = useState(null)
  const [agentData, setAgentData] = useState({})
  const [actionLoading, setActionLoading] = useState('')
  const [question, setQuestion] = useState('')
  const [testReply, setTestReply] = useState({ from_email: '', subject: '', body: '' })
  const [researchDomain, setResearchDomain] = useState('')

  useEffect(() => {
    getCampaigns().then(c => {
      setCampaigns(c)
      if (c.length > 0) setSelectedCampaign(c[0].id)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selectedCampaign) return
    loadOverview()
  }, [selectedCampaign])

  const loadOverview = async () => {
    try {
      const [ov, lg] = await Promise.all([
        getAgentOverview(selectedCampaign).catch(() => null),
        getAgentLogs(selectedCampaign).catch(() => []),
      ])
      setOverview(ov)
      setLogs(lg)
    } catch {}
  }

  // ─── Action helpers ──────────────────────────────────────
  const run = async (key, fn, successMsg) => {
    setActionLoading(key)
    try {
      const data = await fn()
      setAgentData(prev => ({ ...prev, [key]: data }))
      toast.success(successMsg(data))
      await loadOverview()
      return data
    } catch (err) {
      toast.error(err.message)
    } finally {
      setActionLoading('')
    }
  }

  // ─── Research Agent ──────────────────────────────────────
  const handleResearchAll = () => run(
    'research_all', () => researchAllLeads(selectedCampaign),
    d => `Researched ${d.researched} leads`
  )
  const handleResearchCompany = () => {
    if (!researchDomain.trim()) return
    run('research_company', () => researchCompany(researchDomain.trim()),
      () => `Company research complete for ${researchDomain}`)
  }

  // ─── KP Agent ────────────────────────────────────────────
  const handleScoreLeads = () => run(
    'score_leads', () => scoreLeads(selectedCampaign),
    d => `Scored ${d.scored} leads — avg ${d.average_score}`
  )
  const handleKeyPersons = () => run(
    'key_persons', () => getKeyPersons(selectedCampaign),
    d => `Found ${d.total_companies} key persons across ${d.total_companies} companies`
  )
  const handleFlagWeak = () => run(
    'flag_weak', () => flagWeakLeads(selectedCampaign),
    d => `Flagged ${d.flagged} weak leads`
  )

  // ─── Personalization Agent ───────────────────────────────
  const handleBatchPersonalize = () => run(
    'personalize', () => batchPersonalize(selectedCampaign),
    d => `Personalized ${d.personalized} emails`
  )

  // ─── Outreach Agent ──────────────────────────────────────
  const handleGetQueue = () => run(
    'send_queue', () => getSendQueue(selectedCampaign),
    d => `${d.total_queued} emails in queue (${d.approved} approved)`
  )
  const handleBatchSend = () => run(
    'batch_send', () => batchApproveAndSend(selectedCampaign),
    d => `Sent ${d.sent} emails, ${d.failed} failed`
  )
  const handleRunPipeline = () => run(
    'pipeline', () => runFullPipeline(selectedCampaign),
    () => 'Full pipeline complete!'
  )

  // ─── Response Handling Agent ─────────────────────────────
  const handleGetResponseQueue = () => run(
    'response_queue', () => getResponseQueue(selectedCampaign),
    d => `${d.total_unhandled} unhandled replies (${d.urgent} urgent)`
  )
  const handleHandleAll = () => run(
    'handle_all', () => handleAllUnhandled(selectedCampaign, false),
    d => `Processed ${d.processed} replies, auto-sent ${d.auto_sent}`
  )
  const handleTestReply = async () => {
    if (!testReply.body.trim()) return
    setActionLoading('test_reply')
    try {
      const data = await processReply({
        campaign_id: selectedCampaign,
        lead_id: 'test',
        from_email: testReply.from_email || 'test@example.com',
        subject: testReply.subject || 'Re: Follow up',
        body: testReply.body,
      })
      setAgentData(prev => ({ ...prev, reply_result: data }))
      toast.success(`Intent: ${data.intent_data?.intent}`)
      await loadOverview()
    } catch (err) { toast.error(err.message) }
    finally { setActionLoading('') }
  }

  // ─── Booking Agent ────────────────────────────────────────
  const handleGetHotLeads = () => run(
    'hot_leads', () => getHotLeads(selectedCampaign),
    d => `${d.total_hot} hot leads — ${d.booked} already booked`
  )
  const handleGetBookingPipeline = () => run(
    'booking_pipeline', () => getBookingPipeline(selectedCampaign),
    d => `Booking rate: ${d.booking_rate}%`
  )
  const handleFollowUpUnbooked = () => run(
    'follow_up_unbooked', () => followUpUnbooked(selectedCampaign),
    d => `Followed up with ${d.followed_up} unbooked hot leads`
  )
  const handleSendBookingLink = async (leadId) => {
    setActionLoading('send_link_' + leadId)
    try {
      const result = await sendBookingLink(leadId, selectedCampaign)
      if (result.success) toast.success(`Booking link sent!`)
      else toast.error(result.error)
    } catch (err) { toast.error(err.message) }
    finally { setActionLoading('') }
  }
  const handleConfirmBooking = async (leadId) => {
    setActionLoading('confirm_' + leadId)
    try {
      await confirmBooking(leadId, selectedCampaign, {})
      toast.success('Meeting confirmed!')
      await run('hot_leads', () => getHotLeads(selectedCampaign), () => '')
    } catch (err) { toast.error(err.message) }
    finally { setActionLoading('') }
  }

  if (loading) return <div style={s.loading}>Loading agents...</div>

  return (
    <div>
      {/* Header */}
      <div style={s.headerRow}>
        <div>
          <h1 style={s.title}>AI Agents</h1>
          <p style={s.subtitle}>6 specialized agents working end-to-end — from research to booked meetings</p>
        </div>
        <Button variant="ghost" onClick={loadOverview}><RefreshCw size={14} /> Refresh</Button>
      </div>

      {/* Campaign Selector */}
      <div style={s.selectorRow}>
        <label style={s.selectorLabel}>Campaign</label>
        <select value={selectedCampaign} onChange={e => setSelectedCampaign(e.target.value)} style={s.select}>
          {campaigns.map(c => (
            <option key={c.id} value={c.id}>{c.product_name || c.product_url}</option>
          ))}
        </select>
        {/* Pipeline overview pills */}
        {overview && (
          <div style={s.pillsRow}>
            <Pill label="Researched" value={overview.research_agent?.researched || 0} color="#7c3aed" />
            <Pill label="Scored" value={overview.kp_agent?.scored || 0} color="#0891b2" />
            <Pill label="Personalized" value={overview.personalization_agent?.personalized || 0} color="#d97706" />
            <Pill label="Sent" value={overview.outreach_agent?.sent || 0} color="#16a34a" />
            <Pill label="Unhandled" value={overview.response_handling_agent?.unhandled || 0} color="#ff4500" />
            <Pill label="Hot Leads" value={overview.booking_agent?.hot_leads || 0} color="#0369a1" />
          </div>
        )}
      </div>

      {/* Agent Cards */}
      {AGENTS.map(agent => {
        const isOpen = expandedAgent === agent.key
        const Icon = agent.icon
        const data = overview?.[agent.key] || {}
        const status = data.status || 'active'

        return (
          <div key={agent.key} style={s.agentBox}>
            <div style={s.agentHeader} onClick={() => setExpandedAgent(isOpen ? null : agent.key)}>
              <div style={s.agentLeft}>
                <div style={{ ...s.agentIcon, background: `${agent.color}15`, color: agent.color }}>
                  <Icon size={20} />
                </div>
                <div>
                  <div style={s.agentTitle}>{agent.label}</div>
                  <div style={s.agentDesc}>{agent.desc}</div>
                </div>
              </div>
              <div style={s.agentRight}>
                <span style={{ ...s.statusPill, background: 'rgba(22,163,74,0.1)', color: '#16a34a' }}>
                  <Zap size={11} /> active
                </span>
                {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              </div>
            </div>

            {isOpen && (
              <div style={s.agentBody}>

                {/* ── RESEARCH AGENT ──────────────────────────── */}
                {agent.key === 'research_agent' && (
                  <div>
                    <div style={s.statsRow}>
                      <Stat label="Researched" value={data.researched || 0} color="#7c3aed" />
                      <Stat label="Pending" value={data.pending || 0} color="#dc2626" />
                      <Stat label="Total Leads" value={data.total_leads || 0} color="#555" />
                    </div>
                    <div style={s.btnRow}>
                      <Button onClick={handleResearchAll} disabled={actionLoading === 'research_all'}>
                        <Search size={14} /> {actionLoading === 'research_all' ? 'Researching…' : 'Research All Leads'}
                      </Button>
                    </div>
                    {agentData.research_all && (
                      <ResultBox title="Batch Research Results">
                        <KV label="Researched" value={agentData.research_all.researched} />
                        <KV label="Failed" value={agentData.research_all.failed} />
                        <KV label="Total Processed" value={agentData.research_all.total_processed} />
                      </ResultBox>
                    )}
                    <div style={s.section}>
                      <h4 style={s.sectionTitle}>Research a Company</h4>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <input placeholder="e.g. stripe.com" value={researchDomain}
                          onChange={e => setResearchDomain(e.target.value)} style={{ ...s.input, flex: 1 }}
                          onKeyDown={e => e.key === 'Enter' && handleResearchCompany()} />
                        <Button onClick={handleResearchCompany} disabled={actionLoading === 'research_company'}>
                          {actionLoading === 'research_company' ? 'Researching…' : 'Research'}
                        </Button>
                      </div>
                    </div>
                    {agentData.research_company && (
                      <ResultBox title={`Company Intel: ${agentData.research_company.company_name || researchDomain}`}>
                        <KV label="Industry" value={agentData.research_company.industry} />
                        <KV label="Size" value={agentData.research_company.employee_count_estimate} />
                        <KV label="Funding" value={agentData.research_company.funding_stage} />
                        <KV label="HQ" value={agentData.research_company.hq_location} />
                        {agentData.research_company.personalization_hooks?.length > 0 && (
                          <div style={{ marginTop: 12 }}>
                            <strong style={{ fontSize: 12, color: '#555' }}>Personalization Hooks</strong>
                            {agentData.research_company.personalization_hooks.map((h, i) => (
                              <div key={i} style={s.hookItem}>💡 {h}</div>
                            ))}
                          </div>
                        )}
                        {agentData.research_company.recent_news?.length > 0 && (
                          <div style={{ marginTop: 12 }}>
                            <strong style={{ fontSize: 12, color: '#555' }}>Recent News</strong>
                            {agentData.research_company.recent_news.map((n, i) => (
                              <div key={i} style={s.hookItem}>📰 {n}</div>
                            ))}
                          </div>
                        )}
                      </ResultBox>
                    )}
                  </div>
                )}

                {/* ── KP AGENT ────────────────────────────────── */}
                {agent.key === 'kp_agent' && (
                  <div>
                    <div style={s.statsRow}>
                      <Stat label="Total Leads" value={data.total_leads || 0} color="#0891b2" />
                      <Stat label="Scored" value={data.scored || 0} color="#16a34a" />
                    </div>
                    <div style={s.btnRow}>
                      <Button onClick={handleScoreLeads} disabled={actionLoading === 'score_leads'}>
                        <Target size={14} /> {actionLoading === 'score_leads' ? 'Scoring…' : 'Score & Rank All Leads'}
                      </Button>
                      <Button variant="secondary" onClick={handleKeyPersons} disabled={actionLoading === 'key_persons'}>
                        <Star size={14} /> {actionLoading === 'key_persons' ? 'Finding…' : 'Identify Key Persons'}
                      </Button>
                      <Button variant="secondary" onClick={handleFlagWeak} disabled={actionLoading === 'flag_weak'}>
                        <AlertTriangle size={14} /> Flag Weak Leads
                      </Button>
                    </div>
                    {agentData.score_leads && (
                      <ResultBox title={`Lead Scoring — avg ${agentData.score_leads.average_score}/100`}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
                          <div>
                            <div style={s.miniHeader}>🏆 Top Leads ({agentData.score_leads.top_leads?.length})</div>
                            {agentData.score_leads.top_leads?.slice(0, 8).map((l, i) => (
                              <div key={i} style={s.leadRow}>
                                <ScoreBadge score={l.score} />
                                <div>
                                  <div style={s.leadName}>{l.name}</div>
                                  <div style={s.leadSub}>{l.title} · {l.company}</div>
                                  {l.is_decision_maker && <span style={s.dmTag}>DM</span>}
                                </div>
                              </div>
                            ))}
                          </div>
                          <div>
                            <div style={s.miniHeader}>⚠️ Weak Leads ({agentData.score_leads.weak_leads?.length})</div>
                            {agentData.score_leads.weak_leads?.slice(0, 5).map((l, i) => (
                              <div key={i} style={s.leadRow}>
                                <ScoreBadge score={l.score} />
                                <div>
                                  <div style={s.leadName}>{l.name}</div>
                                  <div style={s.leadSub}>{l.title}</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </ResultBox>
                    )}
                    {agentData.key_persons && (
                      <ResultBox title={`Key Persons — ${agentData.key_persons.total_companies} companies`}>
                        {agentData.key_persons.key_persons?.slice(0, 12).map((kp, i) => (
                          <div key={i} style={s.kpRow}>
                            <div style={s.kpDomain}>{kp.domain}</div>
                            <div>
                              <span style={s.kpName}>{kp.key_person.name}</span>
                              <span style={s.kpTitle}> · {kp.key_person.title}</span>
                              {kp.key_person.is_decision_maker && <span style={s.dmTag}>DM</span>}
                            </div>
                            <ScoreBadge score={kp.key_person.score} />
                          </div>
                        ))}
                      </ResultBox>
                    )}
                  </div>
                )}

                {/* ── PERSONALIZATION AGENT ────────────────────── */}
                {agent.key === 'personalization_agent' && (
                  <div>
                    <div style={s.statsRow}>
                      <Stat label="Personalized" value={data.personalized || 0} color="#d97706" />
                      <Stat label="Pending" value={data.pending || 0} color="#dc2626" />
                    </div>
                    <div style={s.btnRow}>
                      <Button onClick={handleBatchPersonalize} disabled={actionLoading === 'personalize'}>
                        <Sparkles size={14} /> {actionLoading === 'personalize' ? 'Personalizing…' : 'Batch Personalize All'}
                      </Button>
                    </div>
                    {agentData.personalize && (
                      <ResultBox title="Batch Personalization Results">
                        <KV label="Personalized" value={agentData.personalize.personalized} />
                        <KV label="Skipped" value={agentData.personalize.skipped} />
                        <KV label="Failed" value={agentData.personalize.failed} />
                      </ResultBox>
                    )}
                    <div style={{ ...s.section, marginTop: 16 }}>
                      <p style={s.tip}>
                        💡 Tip: Run the <strong>Research Agent</strong> first, then <strong>Score Leads</strong> with the KP Agent — the Personalization Agent uses that data to craft unique opening lines for each lead.
                      </p>
                    </div>
                  </div>
                )}

                {/* ── OUTREACH AGENT ───────────────────────────── */}
                {agent.key === 'outreach_agent' && (
                  <div>
                    <div style={s.statsRow}>
                      <Stat label="Pending" value={data.pending || 0} color="#dc2626" />
                      <Stat label="Approved" value={data.approved || 0} color="#d97706" />
                      <Stat label="Sent" value={data.sent || 0} color="#16a34a" />
                      <Stat label="No Reply" value={data.no_reply_count || 0} color="#888" />
                    </div>
                    <div style={s.btnRow}>
                      <Button onClick={handleRunPipeline} disabled={actionLoading === 'pipeline'}
                        style={{ background: '#16a34a', color: '#fff' }}>
                        <Zap size={14} /> {actionLoading === 'pipeline' ? 'Running…' : '▶ Run Full Pipeline'}
                      </Button>
                      <Button variant="secondary" onClick={handleGetQueue} disabled={actionLoading === 'send_queue'}>
                        <Mail size={14} /> View Send Queue
                      </Button>
                      <Button variant="secondary" onClick={handleBatchSend} disabled={actionLoading === 'batch_send'}>
                        <Send size={14} /> {actionLoading === 'batch_send' ? 'Sending…' : 'Batch Send Now'}
                      </Button>
                    </div>
                    {agentData.pipeline && (
                      <ResultBox title="Full Pipeline Results">
                        <KV label="Leads Scored" value={`${agentData.pipeline.scoring?.top} top / ${agentData.pipeline.scoring?.weak} weak`} />
                        <KV label="Researched" value={agentData.pipeline.research?.researched} />
                        <KV label="Personalized" value={agentData.pipeline.personalization?.personalized} />
                        <KV label="Sent" value={agentData.pipeline.send?.sent} />
                        <KV label="Failed" value={agentData.pipeline.send?.failed} />
                      </ResultBox>
                    )}
                    {agentData.send_queue && (
                      <ResultBox title={`Send Queue — ${agentData.send_queue.total_queued} emails`}>
                        <div style={{ display: 'flex', gap: 20, marginBottom: 12, fontSize: 13 }}>
                          <span>✅ {agentData.send_queue.approved} approved</span>
                          <span>⏳ {agentData.send_queue.pending_approval} pending</span>
                          <span>🔥 {agentData.send_queue.high_priority} high priority</span>
                        </div>
                        {agentData.send_queue.queue?.slice(0, 8).map((item, i) => (
                          <div key={i} style={s.queueRow}>
                            <span style={{ ...s.priorityDot, background: item.priority === 'high' ? '#dc2626' : '#d97706' }} />
                            <span style={s.queueName}>{item.lead_name}</span>
                            <span style={s.queueCompany}>{item.company}</span>
                            <span style={s.queueEmail}>{item.lead_email}</span>
                            <span style={{ ...s.queueStatus, color: item.step.status === 'approved' ? '#16a34a' : '#d97706' }}>
                              {item.step.status}
                            </span>
                          </div>
                        ))}
                      </ResultBox>
                    )}
                    {agentData.batch_send && (
                      <ResultBox title="Batch Send Results">
                        <KV label="Sent" value={agentData.batch_send.sent} />
                        <KV label="Failed" value={agentData.batch_send.failed} />
                        {agentData.batch_send.errors?.length > 0 && (
                          <div style={{ color: '#dc2626', fontSize: 12, marginTop: 8 }}>
                            Errors: {agentData.batch_send.errors.join(', ')}
                          </div>
                        )}
                      </ResultBox>
                    )}
                  </div>
                )}

                {/* ── RESPONSE HANDLING AGENT ──────────────────── */}
                {agent.key === 'response_handling_agent' && (
                  <div>
                    <div style={s.statsRow}>
                      <Stat label="Total Replies" value={data.total_replies || 0} color="#ff4500" />
                      <Stat label="Unhandled" value={data.unhandled || 0} color="#dc2626" />
                      {data.intent_breakdown && Object.entries(data.intent_breakdown).map(([k, v]) => (
                        <Stat key={k} label={k.replace(/_/g, ' ')} value={v} color="#555" />
                      ))}
                    </div>
                    <div style={s.btnRow}>
                      <Button onClick={handleGetResponseQueue} disabled={actionLoading === 'response_queue'}>
                        <MessageSquare size={14} /> View Response Queue
                      </Button>
                      <Button variant="secondary" onClick={handleHandleAll} disabled={actionLoading === 'handle_all'}>
                        <CheckCircle size={14} /> {actionLoading === 'handle_all' ? 'Processing…' : 'Process All Unhandled'}
                      </Button>
                    </div>
                    {agentData.handle_all && (
                      <ResultBox title="Handle All Results">
                        <KV label="Processed" value={agentData.handle_all.processed} />
                        <KV label="Auto-Sent" value={agentData.handle_all.auto_sent} />
                        <KV label="Failed" value={agentData.handle_all.failed} />
                      </ResultBox>
                    )}
                    {agentData.response_queue && (
                      <ResultBox title={`Reply Queue — ${agentData.response_queue.total_unhandled} unhandled`}>
                        <div style={{ display: 'flex', gap: 20, marginBottom: 12, fontSize: 13 }}>
                          <span style={{ color: '#dc2626' }}>🔴 {agentData.response_queue.urgent} urgent</span>
                          <span style={{ color: '#d97706' }}>🟡 {agentData.response_queue.normal} normal</span>
                          <span style={{ color: '#888' }}>⚪ {agentData.response_queue.low_priority} low</span>
                        </div>
                        {agentData.response_queue.queue?.slice(0, 8).map((item, i) => (
                          <div key={i} style={s.replyRow}>
                            <span style={{
                              ...s.intentTag,
                              background: item.priority === 'urgent' ? 'rgba(220,38,38,0.1)' : 'rgba(107,114,128,0.1)',
                              color: item.priority === 'urgent' ? '#dc2626' : '#555',
                            }}>{item.intent.replace(/_/g, ' ')}</span>
                            <span style={s.replyName}>{item.lead_name}</span>
                            <span style={s.replyCompany}>{item.company}</span>
                            {item.has_draft && <span style={s.draftTag}>draft ready</span>}
                          </div>
                        ))}
                      </ResultBox>
                    )}
                    <div style={s.section}>
                      <h4 style={s.sectionTitle}>Test Reply Agent</h4>
                      <input placeholder="From email" value={testReply.from_email}
                        onChange={e => setTestReply(p => ({ ...p, from_email: e.target.value }))} style={s.input} />
                      <input placeholder="Subject" value={testReply.subject}
                        onChange={e => setTestReply(p => ({ ...p, subject: e.target.value }))}
                        style={{ ...s.input, marginTop: 8 }} />
                      <textarea placeholder="Paste reply email body here…" rows={4}
                        value={testReply.body} onChange={e => setTestReply(p => ({ ...p, body: e.target.value }))}
                        style={{ ...s.textarea, marginTop: 8 }} />
                      <Button onClick={handleTestReply} disabled={actionLoading === 'test_reply'} style={{ marginTop: 12 }}>
                        <Play size={14} /> {actionLoading === 'test_reply' ? 'Processing…' : 'Process Reply'}
                      </Button>
                    </div>
                    {agentData.reply_result && (
                      <ResultBox title="Agent Response">
                        <div style={s.resultGrid}>
                          <KV label="Intent" value={agentData.reply_result.intent_data?.intent} />
                          <KV label="Confidence" value={`${Math.round((agentData.reply_result.intent_data?.confidence || 0) * 100)}%`} />
                          <KV label="Sentiment" value={agentData.reply_result.intent_data?.sentiment} />
                          <KV label="Urgency" value={agentData.reply_result.intent_data?.urgency} />
                        </div>
                        <div style={{ marginTop: 12 }}>
                          <strong style={{ fontSize: 12 }}>Auto-Generated Response:</strong>
                          <div style={s.responseBox}>{agentData.reply_result.auto_response}</div>
                        </div>
                      </ResultBox>
                    )}
                  </div>
                )}

                {/* ── BOOKING AGENT ────────────────────────────── */}
                {agent.key === 'booking_agent' && (
                  <div>
                    <div style={s.statsRow}>
                      <Stat label="Hot Leads" value={data.hot_leads || 0} color="#0369a1" />
                      <Stat label="Booked" value={data.booked || 0} color="#16a34a" />
                      <Stat label="Converted" value={data.converted || 0} color="#7c3aed" />
                      <Stat label="Booking Rate" value={`${data.booking_rate || 0}%`} color="#d97706" />
                    </div>
                    <div style={s.btnRow}>
                      <Button onClick={handleGetHotLeads} disabled={actionLoading === 'hot_leads'}>
                        <PhoneCall size={14} /> {actionLoading === 'hot_leads' ? 'Loading…' : 'Get Hot Leads'}
                      </Button>
                      <Button variant="secondary" onClick={handleGetBookingPipeline} disabled={actionLoading === 'booking_pipeline'}>
                        <TrendingUp size={14} /> View Funnel
                      </Button>
                      <Button variant="secondary" onClick={handleFollowUpUnbooked} disabled={actionLoading === 'follow_up_unbooked'}>
                        <ArrowRight size={14} /> Follow Up Unbooked
                      </Button>
                    </div>
                    {agentData.booking_pipeline && (
                      <ResultBox title="Booking Funnel">
                        {Object.entries(agentData.booking_pipeline.funnel || {}).map(([k, v]) => (
                          <div key={k} style={s.funnelRow}>
                            <span style={s.funnelLabel}>{k.replace(/_/g, ' ')}</span>
                            <div style={s.funnelBar}>
                              <div style={{
                                ...s.funnelFill,
                                width: `${Math.min(100, (v / Math.max(agentData.booking_pipeline.funnel.total_leads || 1, 1)) * 100)}%`,
                              }} />
                            </div>
                            <span style={s.funnelCount}>{v}</span>
                          </div>
                        ))}
                        <div style={{ marginTop: 12, fontSize: 13, color: '#555' }}>
                          Conversion rate: <strong>{agentData.booking_pipeline.conversion_rate}%</strong> &nbsp;|&nbsp;
                          Booking rate: <strong>{agentData.booking_pipeline.booking_rate}%</strong>
                        </div>
                      </ResultBox>
                    )}
                    {agentData.hot_leads && (
                      <ResultBox title={`Hot Leads — ${agentData.hot_leads.total_hot} ready to book`}>
                        {agentData.hot_leads.booking_link && (
                          <div style={s.bookingLinkBox}>
                            📅 Booking link: <a href={agentData.hot_leads.booking_link} target="_blank" rel="noopener noreferrer"
                              style={{ color: '#0369a1' }}>{agentData.hot_leads.booking_link}</a>
                          </div>
                        )}
                        {agentData.hot_leads.hot_leads?.slice(0, 10).map((item, i) => (
                          <div key={i} style={s.hotLeadRow}>
                            <div style={s.hotLeadInfo}>
                              <span style={s.hotLeadName}>{item.lead?.first_name} {item.lead?.last_name}</span>
                              <span style={s.hotLeadCompany}>{item.lead?.company}</span>
                              <span style={{ ...s.intentTag, background: 'rgba(3,105,161,0.1)', color: '#0369a1' }}>
                                {item.intent?.replace(/_/g, ' ')}
                              </span>
                              {item.is_booked && <span style={s.bookedTag}>✓ Booked</span>}
                            </div>
                            {!item.is_booked && item.lead?.id && (
                              <div style={{ display: 'flex', gap: 6 }}>
                                <button style={s.miniBtn}
                                  disabled={actionLoading === 'send_link_' + item.lead.id}
                                  onClick={() => handleSendBookingLink(item.lead.id)}>
                                  📅 Send Link
                                </button>
                                <button style={{ ...s.miniBtn, background: 'rgba(22,163,74,0.1)', color: '#16a34a' }}
                                  disabled={actionLoading === 'confirm_' + item.lead.id}
                                  onClick={() => handleConfirmBooking(item.lead.id)}>
                                  ✓ Confirm
                                </button>
                              </div>
                            )}
                          </div>
                        ))}
                      </ResultBox>
                    )}
                    {agentData.follow_up_unbooked && (
                      <ResultBox title="Follow-Up Results">
                        <KV label="Followed Up" value={agentData.follow_up_unbooked.followed_up} />
                        <KV label="Skipped" value={agentData.follow_up_unbooked.skipped} />
                      </ResultBox>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}

      {/* Agent Activity Log */}
      {logs.length > 0 && (
        <Card style={{ marginTop: 24 }}>
          <h3 style={s.logTitle}>Agent Activity Log</h3>
          <div>
            {logs.slice(0, 20).map((log, i) => (
              <div key={log.id || i} style={s.logRow}>
                <span style={{ ...s.logAgent, background: AGENT_COLORS[log.agent] || 'rgba(255,69,0,0.08)', color: AGENT_TEXT[log.agent] || '#ff4500' }}>
                  {log.agent?.replace(/_/g, ' ')}
                </span>
                <span style={s.logAction}>{log.action}</span>
                <span style={s.logDetail}>{log.detail}</span>
                <span style={s.logTime}>{new Date(log.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

// ─── Sub-components ───────────────────────────────────────────
function Stat({ label, value, color }) {
  return (
    <div style={s.stat}>
      <div style={{ ...s.statValue, color }}>{value}</div>
      <div style={s.statLabel}>{label}</div>
    </div>
  )
}

function Pill({ label, value, color }) {
  return (
    <div style={{ ...s.pill, borderColor: color + '40', color }}>
      <span style={{ fontWeight: 700 }}>{value}</span>
      <span style={{ fontSize: 10, opacity: 0.7 }}> {label}</span>
    </div>
  )
}

function ScoreBadge({ score }) {
  const color = score >= 70 ? '#16a34a' : score >= 50 ? '#d97706' : '#dc2626'
  return (
    <div style={{ ...s.scoreBadge, background: color + '15', color, border: `1px solid ${color}30` }}>
      {Math.round(score)}
    </div>
  )
}

function ResultBox({ title, children }) {
  return (
    <div style={s.resultBox}>
      <h4 style={s.resultTitle}>{title}</h4>
      {children}
    </div>
  )
}

function KV({ label, value }) {
  return (
    <div style={s.kv}>
      <span style={s.kvLabel}>{label}:</span>
      <span style={s.kvValue}>{value ?? '—'}</span>
    </div>
  )
}

const AGENT_COLORS = {
  research_agent: 'rgba(124,58,237,0.08)',
  kp_agent: 'rgba(8,145,178,0.08)',
  personalization_agent: 'rgba(217,119,6,0.08)',
  outreach_agent: 'rgba(22,163,74,0.08)',
  response_handling_agent: 'rgba(255,69,0,0.08)',
  booking_agent: 'rgba(3,105,161,0.08)',
  mail_agent: 'rgba(22,163,74,0.08)',
  reply_agent: 'rgba(255,69,0,0.08)',
  performance_agent: 'rgba(37,99,235,0.08)',
  context_agent: 'rgba(217,119,6,0.08)',
}
const AGENT_TEXT = {
  research_agent: '#7c3aed',
  kp_agent: '#0891b2',
  personalization_agent: '#d97706',
  outreach_agent: '#16a34a',
  response_handling_agent: '#ff4500',
  booking_agent: '#0369a1',
  mail_agent: '#16a34a',
  reply_agent: '#ff4500',
  performance_agent: '#2563eb',
  context_agent: '#d97706',
}

// ─── Styles ───────────────────────────────────────────────────
const s = {
  loading: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh', color: '#888' },
  headerRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 },
  title: { fontSize: 28, fontWeight: 700, color: '#1a1a1a' },
  subtitle: { fontSize: 14, color: '#888', marginTop: 4 },

  selectorRow: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, flexWrap: 'wrap' },
  selectorLabel: { fontSize: 12, fontWeight: 600, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em' },
  select: {
    padding: '8px 14px', borderRadius: 8, border: '1px solid #e0e0e0',
    background: '#fff', color: '#1a1a1a', fontSize: 14,
  },
  pillsRow: { display: 'flex', gap: 8, flexWrap: 'wrap', flex: 1 },
  pill: {
    display: 'flex', alignItems: 'center', gap: 4,
    padding: '4px 10px', borderRadius: 20, border: '1px solid', fontSize: 12,
  },

  agentBox: {
    background: '#fff', border: '1px solid #e0e0e0', borderRadius: 12,
    marginBottom: 14, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  agentHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '18px 24px', cursor: 'pointer', userSelect: 'none',
  },
  agentLeft: { display: 'flex', alignItems: 'center', gap: 14 },
  agentIcon: {
    width: 44, height: 44, borderRadius: 10,
    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
  },
  agentTitle: { fontSize: 16, fontWeight: 700, color: '#1a1a1a' },
  agentDesc: { fontSize: 12, color: '#888', marginTop: 2, maxWidth: 620 },
  agentRight: { display: 'flex', alignItems: 'center', gap: 12 },
  statusPill: {
    display: 'inline-flex', alignItems: 'center', gap: 4,
    padding: '4px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600,
  },
  agentBody: { borderTop: '1px solid #e0e0e0', padding: '20px 24px' },

  statsRow: { display: 'flex', gap: 28, marginBottom: 20, flexWrap: 'wrap' },
  stat: { minWidth: 70 },
  statValue: { fontSize: 22, fontWeight: 700 },
  statLabel: { fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: 2 },

  btnRow: { display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' },
  section: { marginTop: 20, paddingTop: 16, borderTop: '1px solid #f0f0f0' },
  sectionTitle: { fontSize: 14, fontWeight: 600, color: '#1a1a1a', marginBottom: 8 },
  tip: { fontSize: 13, color: '#555', background: '#fafafa', padding: '12px 14px', borderRadius: 8, border: '1px solid #e0e0e0', lineHeight: 1.6 },
  input: {
    padding: '10px 14px', borderRadius: 8, border: '1px solid #e0e0e0',
    background: '#fafafa', color: '#1a1a1a', fontSize: 13, width: '100%', boxSizing: 'border-box',
  },
  textarea: {
    padding: '10px 14px', borderRadius: 8, border: '1px solid #e0e0e0',
    background: '#fafafa', color: '#1a1a1a', fontSize: 13, width: '100%',
    resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.6, boxSizing: 'border-box',
  },

  resultBox: {
    background: '#fafafa', border: '1px solid #e0e0e0', borderRadius: 10,
    padding: 18, marginTop: 14,
  },
  resultTitle: { fontSize: 14, fontWeight: 600, marginBottom: 12, color: '#1a1a1a' },
  resultGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 24px' },
  kv: { display: 'flex', gap: 6, fontSize: 13, padding: '3px 0' },
  kvLabel: { color: '#888', minWidth: 100 },
  kvValue: { color: '#1a1a1a', fontWeight: 600 },

  hookItem: { fontSize: 13, color: '#555', padding: '6px 0', borderBottom: '1px solid #f0f0f0', lineHeight: 1.5 },

  leadRow: { display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', borderBottom: '1px solid #f0f0f0' },
  leadName: { fontSize: 13, fontWeight: 600, color: '#1a1a1a' },
  leadSub: { fontSize: 11, color: '#888', marginTop: 1 },
  dmTag: {
    display: 'inline-block', padding: '1px 6px', borderRadius: 4, fontSize: 9, fontWeight: 700,
    background: 'rgba(3,105,161,0.1)', color: '#0369a1', marginLeft: 4,
  },
  scoreBadge: {
    minWidth: 34, height: 34, borderRadius: 8, display: 'flex', alignItems: 'center',
    justifyContent: 'center', fontSize: 12, fontWeight: 700, flexShrink: 0,
  },
  miniHeader: { fontSize: 12, fontWeight: 700, color: '#555', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' },
  kpRow: {
    display: 'flex', alignItems: 'center', gap: 12, padding: '8px 0',
    borderBottom: '1px solid #f0f0f0', fontSize: 13,
  },
  kpDomain: { color: '#888', minWidth: 120, fontSize: 12 },
  kpName: { fontWeight: 600, color: '#1a1a1a' },
  kpTitle: { color: '#555' },

  queueRow: {
    display: 'flex', alignItems: 'center', gap: 12, padding: '7px 0',
    borderBottom: '1px solid #f0f0f0', fontSize: 13,
  },
  priorityDot: { width: 8, height: 8, borderRadius: '50%', flexShrink: 0 },
  queueName: { fontWeight: 600, color: '#1a1a1a', minWidth: 120 },
  queueCompany: { color: '#555', flex: 1 },
  queueEmail: { color: '#888', fontSize: 12 },
  queueStatus: { fontWeight: 600, fontSize: 11, textTransform: 'uppercase' },

  replyRow: {
    display: 'flex', alignItems: 'center', gap: 10, padding: '7px 0',
    borderBottom: '1px solid #f0f0f0', fontSize: 13,
  },
  replyName: { fontWeight: 600, color: '#1a1a1a', flex: 1 },
  replyCompany: { color: '#555' },
  intentTag: {
    padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
    textTransform: 'capitalize', flexShrink: 0,
  },
  draftTag: {
    padding: '2px 7px', borderRadius: 5, fontSize: 10, fontWeight: 700,
    background: 'rgba(22,163,74,0.1)', color: '#16a34a',
  },
  responseBox: {
    marginTop: 6, padding: 12, background: '#fff', border: '1px solid #e0e0e0',
    borderRadius: 8, fontSize: 13, color: '#1a1a1a', lineHeight: 1.7, whiteSpace: 'pre-wrap',
  },

  hotLeadRow: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '8px 0', borderBottom: '1px solid #f0f0f0',
  },
  hotLeadInfo: { display: 'flex', alignItems: 'center', gap: 10, flex: 1 },
  hotLeadName: { fontWeight: 600, color: '#1a1a1a', fontSize: 13 },
  hotLeadCompany: { color: '#555', fontSize: 13 },
  bookedTag: {
    padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 700,
    background: 'rgba(22,163,74,0.1)', color: '#16a34a',
  },
  miniBtn: {
    padding: '5px 10px', borderRadius: 6, border: '1px solid #e0e0e0',
    background: 'rgba(3,105,161,0.08)', color: '#0369a1', fontSize: 11,
    fontWeight: 600, cursor: 'pointer',
  },
  bookingLinkBox: {
    fontSize: 13, color: '#555', padding: '8px 12px', background: 'rgba(3,105,161,0.05)',
    borderRadius: 8, marginBottom: 12, border: '1px solid rgba(3,105,161,0.15)',
  },

  funnelRow: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 },
  funnelLabel: { fontSize: 12, color: '#555', minWidth: 110, textTransform: 'capitalize' },
  funnelBar: { flex: 1, height: 8, background: '#e0e0e0', borderRadius: 4, overflow: 'hidden' },
  funnelFill: { height: '100%', background: 'linear-gradient(90deg,#0369a1,#38bdf8)', borderRadius: 4, transition: 'width 0.3s' },
  funnelCount: { fontSize: 13, fontWeight: 700, color: '#1a1a1a', minWidth: 30, textAlign: 'right' },

  logTitle: { fontSize: 14, fontWeight: 600, color: '#1a1a1a', marginBottom: 12 },
  logRow: {
    display: 'flex', gap: 12, alignItems: 'center', padding: '7px 0',
    borderBottom: '1px solid #f0f0f0', fontSize: 12,
  },
  logAgent: {
    padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700,
    textTransform: 'uppercase', whiteSpace: 'nowrap',
  },
  logAction: { fontWeight: 600, color: '#1a1a1a', whiteSpace: 'nowrap' },
  logDetail: { color: '#555', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  logTime: { color: '#888', whiteSpace: 'nowrap' },
}
