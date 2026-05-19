import { useEffect, useState } from 'react'
import {
  Bot, MessageSquare, Send, BarChart3, BookOpen, Play, RefreshCw,
  ChevronDown, ChevronRight, CheckCircle, Clock, AlertTriangle,
  Zap, ArrowRight, HelpCircle
} from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import StatusBadge from '../components/StatusBadge'
import {
  getCampaigns, getAgentOverview, getAgentLogs, getNoReplyLeads,
  autoAdvanceSequence, analyzePerformance, buildContext, getContext,
  askContextQuestion, processReply
} from '../api/client'
import toast from 'react-hot-toast'

const AGENTS = [
  { key: 'reply_agent', label: 'Reply Agent', icon: MessageSquare, color: '#ff4500',
    desc: 'Monitors replies, classifies intent (schedule call, demo request, pricing, objections), and auto-generates smart responses' },
  { key: 'mail_agent', label: 'Mail Agent', icon: Send, color: '#16a34a',
    desc: 'Tracks email sends, detects no-replies, auto-advances leads to next sequence step' },
  { key: 'performance_agent', label: 'Performance Agent', icon: BarChart3, color: '#2563eb',
    desc: 'Analyzes campaign metrics, identifies top-performing emails/roles, gives AI optimization recommendations' },
  { key: 'context_agent', label: 'Context Agent', icon: BookOpen, color: '#d97706',
    desc: 'Builds business knowledge base — FAQs, objection handling, use cases, competitive advantages' },
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

  // Simulated reply test
  const [testReply, setTestReply] = useState({ from_email: '', subject: '', body: '' })

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

  // ─── Agent Actions ─────────────────────────────────────
  const handleNoReply = async () => {
    setActionLoading('no_reply')
    try {
      const data = await getNoReplyLeads(selectedCampaign)
      setAgentData(prev => ({ ...prev, no_reply: data }))
      toast.success(`Found ${data.length} leads with no reply`)
    } catch (err) { toast.error(err.message) }
    finally { setActionLoading('') }
  }

  const handleAutoAdvance = async () => {
    setActionLoading('advance')
    try {
      const result = await autoAdvanceSequence(selectedCampaign)
      toast.success(`Advanced ${result.advanced} leads, ${result.skipped} skipped`)
      await loadOverview()
    } catch (err) { toast.error(err.message) }
    finally { setActionLoading('') }
  }

  const handleAnalyze = async () => {
    setActionLoading('analyze')
    try {
      const data = await analyzePerformance(selectedCampaign)
      setAgentData(prev => ({ ...prev, performance: data }))
      toast.success('Performance analysis complete')
    } catch (err) { toast.error(err.message) }
    finally { setActionLoading('') }
  }

  const handleBuildContext = async () => {
    setActionLoading('context')
    try {
      const data = await buildContext(selectedCampaign)
      setAgentData(prev => ({ ...prev, context: data }))
      toast.success('Business context built successfully')
      await loadOverview()
    } catch (err) { toast.error(err.message) }
    finally { setActionLoading('') }
  }

  const handleAsk = async () => {
    if (!question.trim()) return
    setActionLoading('ask')
    try {
      const data = await askContextQuestion(selectedCampaign, question)
      setAgentData(prev => ({ ...prev, answer: data.answer }))
      toast.success('Got answer')
    } catch (err) { toast.error(err.message) }
    finally { setActionLoading('') }
  }

  const handleTestReply = async () => {
    if (!testReply.body.trim()) return
    setActionLoading('test_reply')
    try {
      // Get first lead for testing
      const camp = campaigns.find(c => c.id === selectedCampaign)
      const data = await processReply({
        campaign_id: selectedCampaign,
        lead_id: testReply.lead_id || 'test',
        from_email: testReply.from_email || 'test@example.com',
        subject: testReply.subject || 'Re: Follow up',
        body: testReply.body,
      })
      setAgentData(prev => ({ ...prev, reply_result: data }))
      toast.success(`Intent: ${data.intent_data?.intent} — Response generated`)
      await loadOverview()
    } catch (err) { toast.error(err.message) }
    finally { setActionLoading('') }
  }

  if (loading) return <div style={styles.loading}>Loading...</div>

  const campaign = campaigns.find(c => c.id === selectedCampaign)

  return (
    <div>
      <div style={styles.headerRow}>
        <div>
          <h1 style={styles.title}>AI Agents</h1>
          <p style={styles.subtitle}>4 specialized agents working together to automate your outreach</p>
        </div>
        <Button variant="ghost" onClick={loadOverview}><RefreshCw size={14} /> Refresh</Button>
      </div>

      {/* Campaign Selector */}
      <div style={styles.selectorRow}>
        <label style={styles.selectorLabel}>Campaign</label>
        <select value={selectedCampaign} onChange={e => setSelectedCampaign(e.target.value)} style={styles.select}>
          {campaigns.map(c => (
            <option key={c.id} value={c.id}>{c.product_name || c.product_url}</option>
          ))}
        </select>
      </div>

      {/* Agent Cards */}
      {AGENTS.map(agent => {
        const isOpen = expandedAgent === agent.key
        const Icon = agent.icon
        const data = overview?.[agent.key] || {}
        const status = data.status || 'idle'

        return (
          <div key={agent.key} style={styles.agentBox}>
            <div style={styles.agentHeader} onClick={() => setExpandedAgent(isOpen ? null : agent.key)}>
              <div style={styles.agentLeft}>
                <div style={{ ...styles.agentIcon, background: `${agent.color}15`, color: agent.color }}>
                  <Icon size={20} />
                </div>
                <div>
                  <div style={styles.agentTitle}>{agent.label}</div>
                  <div style={styles.agentDesc}>{agent.desc}</div>
                </div>
              </div>
              <div style={styles.agentRight}>
                <span style={{
                  ...styles.statusPill,
                  background: status === 'active' ? 'rgba(22,163,74,0.1)' : status === 'ready' ? 'rgba(37,99,235,0.1)' : 'rgba(136,136,136,0.1)',
                  color: status === 'active' ? '#16a34a' : status === 'ready' ? '#2563eb' : '#888',
                }}>
                  {status === 'active' ? <Zap size={12} /> : <Clock size={12} />}
                  {status}
                </span>
                {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              </div>
            </div>

            {isOpen && (
              <div style={styles.agentBody}>
                {/* Reply Agent Panel */}
                {agent.key === 'reply_agent' && (
                  <div>
                    <div style={styles.statsRow}>
                      <Stat label="Total Replies" value={data.total_replies || 0} color="#ff4500" />
                      <Stat label="Unhandled" value={data.unhandled || 0} color="#dc2626" />
                      {data.intent_breakdown && Object.entries(data.intent_breakdown).map(([k, v]) => (
                        <Stat key={k} label={k.replace(/_/g, ' ')} value={v} color="#555" />
                      ))}
                    </div>

                    <div style={styles.section}>
                      <h4 style={styles.sectionTitle}>Test Reply Agent</h4>
                      <p style={styles.sectionDesc}>Paste an email reply to see how the agent classifies and responds</p>
                      <input placeholder="From email" value={testReply.from_email}
                        onChange={e => setTestReply(p => ({ ...p, from_email: e.target.value }))} style={styles.input} />
                      <input placeholder="Subject" value={testReply.subject}
                        onChange={e => setTestReply(p => ({ ...p, subject: e.target.value }))} style={{ ...styles.input, marginTop: 8 }} />
                      <textarea placeholder="Paste the reply email body here..." rows={4}
                        value={testReply.body}
                        onChange={e => setTestReply(p => ({ ...p, body: e.target.value }))}
                        style={{ ...styles.textarea, marginTop: 8 }} />
                      <Button onClick={handleTestReply} disabled={actionLoading === 'test_reply'} style={{ marginTop: 12 }}>
                        <Play size={14} /> {actionLoading === 'test_reply' ? 'Processing...' : 'Process Reply'}
                      </Button>
                    </div>

                    {agentData.reply_result && (
                      <div style={styles.resultBox}>
                        <h4 style={styles.resultTitle}>Agent Response</h4>
                        <div style={styles.resultGrid}>
                          <div><strong>Intent:</strong> {agentData.reply_result.intent_data?.intent}</div>
                          <div><strong>Confidence:</strong> {Math.round((agentData.reply_result.intent_data?.confidence || 0) * 100)}%</div>
                          <div><strong>Sentiment:</strong> {agentData.reply_result.intent_data?.sentiment}</div>
                          <div><strong>Urgency:</strong> {agentData.reply_result.intent_data?.urgency}</div>
                        </div>
                        {agentData.reply_result.intent_data?.key_points?.length > 0 && (
                          <div style={styles.keyPoints}>
                            <strong>Key Points:</strong>
                            <ul>{agentData.reply_result.intent_data.key_points.map((p, i) => <li key={i}>{p}</li>)}</ul>
                          </div>
                        )}
                        <div style={styles.autoResponse}>
                          <strong>Auto-Generated Response:</strong>
                          <div style={styles.responseText}>{agentData.reply_result.auto_response}</div>
                        </div>
                        {agentData.reply_result.actions_taken?.length > 0 && (
                          <div style={styles.actions}>
                            <strong>Actions Taken:</strong>
                            {agentData.reply_result.actions_taken.map((a, i) => (
                              <span key={i} style={styles.actionTag}>{a.type}: {a.label || a.status || a.reason || ''}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Mail Agent Panel */}
                {agent.key === 'mail_agent' && (
                  <div>
                    <div style={styles.statsRow}>
                      <Stat label="Pending" value={data.pending || 0} color="#dc2626" />
                      <Stat label="Approved" value={data.approved || 0} color="#16a34a" />
                      <Stat label="Sent" value={data.sent || 0} color="#ff4500" />
                      <Stat label="No Reply" value={data.no_reply_count || 0} color="#d97706" />
                    </div>
                    <div style={styles.buttonRow}>
                      <Button variant="secondary" onClick={handleNoReply} disabled={actionLoading === 'no_reply'}>
                        <AlertTriangle size={14} /> {actionLoading === 'no_reply' ? 'Checking...' : 'Check No-Reply Leads'}
                      </Button>
                      <Button onClick={handleAutoAdvance} disabled={actionLoading === 'advance'}>
                        <ArrowRight size={14} /> {actionLoading === 'advance' ? 'Advancing...' : 'Auto-Advance Sequence'}
                      </Button>
                    </div>
                    {agentData.no_reply?.length > 0 && (
                      <div style={styles.resultBox}>
                        <h4 style={styles.resultTitle}>No-Reply Leads ({agentData.no_reply.length})</h4>
                        {agentData.no_reply.slice(0, 10).map((item, i) => (
                          <div key={i} style={styles.noReplyRow}>
                            <span style={styles.noReplyName}>{item.lead.first_name} {item.lead.last_name}</span>
                            <span style={styles.noReplyCompany}>{item.lead.company}</span>
                            <span style={styles.noReplyDays}>{item.days_waiting}d waiting</span>
                            <span style={styles.noReplyStep}>{item.sent_count}/{item.total_steps} steps</span>
                            {item.next_step && <span style={styles.nextTag}>Next: {item.next_step.template_type}</span>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Performance Agent Panel */}
                {agent.key === 'performance_agent' && (
                  <div>
                    <div style={styles.statsRow}>
                      <Stat label="Total Sent" value={data.total_sent || 0} color="#ff4500" />
                      <Stat label="Reply Rate" value={`${data.reply_rate || 0}%`} color="#16a34a" />
                    </div>
                    <Button onClick={handleAnalyze} disabled={actionLoading === 'analyze'} style={{ marginBottom: 16 }}>
                      <BarChart3 size={14} /> {actionLoading === 'analyze' ? 'Analyzing...' : 'Run AI Analysis'}
                    </Button>
                    {agentData.performance?.recommendations && (
                      <div style={styles.resultBox}>
                        <h4 style={styles.resultTitle}>AI Recommendations</h4>
                        {agentData.performance.recommendations.map((rec, i) => (
                          <div key={i} style={styles.recCard}>
                            <div style={styles.recHeader}>
                              <span style={{ ...styles.priorityTag, color: rec.priority === 'high' ? '#dc2626' : rec.priority === 'medium' ? '#d97706' : '#16a34a' }}>
                                {rec.priority}
                              </span>
                              <span style={styles.recCategory}>{rec.category}</span>
                            </div>
                            <div style={styles.recTitle}>{rec.title}</div>
                            <div style={styles.recDesc}>{rec.description}</div>
                          </div>
                        ))}
                      </div>
                    )}
                    {agentData.performance?.metrics?.by_type && (
                      <div style={styles.resultBox}>
                        <h4 style={styles.resultTitle}>Performance by Email Type</h4>
                        {Object.entries(agentData.performance.metrics.by_type).map(([type, m]) => (
                          <div key={type} style={styles.metricRow}>
                            <span style={styles.metricLabel}>{type.replace(/_/g, ' ')}</span>
                            <span>{m.sent} sent</span>
                            <span>{m.replied} replied</span>
                            <span style={{ color: '#16a34a', fontWeight: 600 }}>{m.reply_rate}%</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Context Agent Panel */}
                {agent.key === 'context_agent' && (
                  <div>
                    <div style={styles.buttonRow}>
                      <Button onClick={handleBuildContext} disabled={actionLoading === 'context'}>
                        <BookOpen size={14} /> {actionLoading === 'context' ? 'Building...' : data.has_context ? 'Rebuild Context' : 'Build Context'}
                      </Button>
                    </div>

                    {agentData.context && (
                      <div style={styles.resultBox}>
                        <h4 style={styles.resultTitle}>Business Context</h4>
                        {agentData.context.elevator_pitch && (
                          <div style={styles.ctxSection}>
                            <strong>Elevator Pitch:</strong>
                            <p>{agentData.context.elevator_pitch}</p>
                          </div>
                        )}
                        {agentData.context.value_propositions?.length > 0 && (
                          <div style={styles.ctxSection}>
                            <strong>Value Propositions:</strong>
                            <ul>{agentData.context.value_propositions.map((v, i) => <li key={i}>{v}</li>)}</ul>
                          </div>
                        )}
                        {agentData.context.common_objections?.length > 0 && (
                          <div style={styles.ctxSection}>
                            <strong>Objection Playbook:</strong>
                            {agentData.context.common_objections.map((o, i) => (
                              <div key={i} style={styles.objection}>
                                <div style={styles.objQ}>❓ {o.objection}</div>
                                <div style={styles.objA}>→ {o.response}</div>
                              </div>
                            ))}
                          </div>
                        )}
                        {agentData.context.faq?.length > 0 && (
                          <div style={styles.ctxSection}>
                            <strong>FAQ:</strong>
                            {agentData.context.faq.map((f, i) => (
                              <div key={i} style={styles.objection}>
                                <div style={styles.objQ}>{f.question}</div>
                                <div style={styles.objA}>{f.answer}</div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    <div style={styles.section}>
                      <h4 style={styles.sectionTitle}>Ask the Context Agent</h4>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <input placeholder="Ask a question about the product..." value={question}
                          onChange={e => setQuestion(e.target.value)} style={{ ...styles.input, flex: 1 }}
                          onKeyDown={e => e.key === 'Enter' && handleAsk()} />
                        <Button onClick={handleAsk} disabled={actionLoading === 'ask'}>
                          <HelpCircle size={14} /> Ask
                        </Button>
                      </div>
                      {agentData.answer && (
                        <div style={styles.answerBox}>{agentData.answer}</div>
                      )}
                    </div>
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
          <h3 style={styles.logTitle}>Agent Activity Log</h3>
          <div>
            {logs.slice(0, 20).map(log => (
              <div key={log.id} style={styles.logRow}>
                <span style={styles.logAgent}>{log.agent.replace(/_/g, ' ')}</span>
                <span style={styles.logAction}>{log.action}</span>
                <span style={styles.logDetail}>{log.detail}</span>
                <span style={styles.logTime}>{new Date(log.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

function Stat({ label, value, color }) {
  return (
    <div style={styles.stat}>
      <div style={{ ...styles.statValue, color }}>{value}</div>
      <div style={styles.statLabel}>{label}</div>
    </div>
  )
}

const styles = {
  loading: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh', color: '#888' },
  headerRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 },
  title: { fontSize: 28, fontWeight: 700, color: '#1a1a1a' },
  subtitle: { fontSize: 14, color: '#888', marginTop: 4 },
  selectorRow: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 },
  selectorLabel: { fontSize: 12, fontWeight: 600, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em' },
  select: {
    padding: '8px 14px', borderRadius: 8, border: '1px solid #e0e0e0',
    background: '#fff', color: '#1a1a1a', fontSize: 14, flex: 1, maxWidth: 400,
  },

  // Agent box
  agentBox: {
    background: '#fff', border: '1px solid #e0e0e0', borderRadius: 12,
    marginBottom: 16, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
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
  agentDesc: { fontSize: 12, color: '#888', marginTop: 2, maxWidth: 600 },
  agentRight: { display: 'flex', alignItems: 'center', gap: 12 },
  statusPill: {
    display: 'inline-flex', alignItems: 'center', gap: 4,
    padding: '4px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600, textTransform: 'capitalize',
  },
  agentBody: { borderTop: '1px solid #e0e0e0', padding: '20px 24px' },

  // Stats
  statsRow: { display: 'flex', gap: 24, marginBottom: 20, flexWrap: 'wrap' },
  stat: { minWidth: 80 },
  statValue: { fontSize: 22, fontWeight: 700 },
  statLabel: { fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: 2 },

  // Controls
  buttonRow: { display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' },
  section: { marginTop: 20, paddingTop: 16, borderTop: '1px solid #f0f0f0' },
  sectionTitle: { fontSize: 14, fontWeight: 600, color: '#1a1a1a', marginBottom: 8 },
  sectionDesc: { fontSize: 12, color: '#888', marginBottom: 12 },
  input: {
    padding: '10px 14px', borderRadius: 8, border: '1px solid #e0e0e0',
    background: '#fafafa', color: '#1a1a1a', fontSize: 13, width: '100%', boxSizing: 'border-box',
  },
  textarea: {
    padding: '10px 14px', borderRadius: 8, border: '1px solid #e0e0e0',
    background: '#fafafa', color: '#1a1a1a', fontSize: 13, width: '100%', resize: 'vertical',
    fontFamily: 'inherit', lineHeight: 1.6, boxSizing: 'border-box',
  },

  // Results
  resultBox: {
    background: '#fafafa', border: '1px solid #e0e0e0', borderRadius: 10,
    padding: 20, marginTop: 16,
  },
  resultTitle: { fontSize: 14, fontWeight: 600, marginBottom: 12, color: '#1a1a1a' },
  resultGrid: {
    display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 24px',
    fontSize: 13, color: '#555', marginBottom: 12,
  },
  keyPoints: { fontSize: 13, color: '#555', marginBottom: 12, lineHeight: 1.7 },
  autoResponse: { marginTop: 12 },
  responseText: {
    marginTop: 6, padding: 14, background: '#fff', border: '1px solid #e0e0e0',
    borderRadius: 8, fontSize: 13, color: '#1a1a1a', lineHeight: 1.7, whiteSpace: 'pre-wrap',
  },
  actions: { marginTop: 12, fontSize: 13 },
  actionTag: {
    display: 'inline-block', padding: '3px 10px', borderRadius: 6,
    background: 'rgba(255,69,0,0.08)', color: '#ff4500', fontSize: 11,
    fontWeight: 600, marginLeft: 6, marginTop: 4,
  },

  // No-reply
  noReplyRow: {
    display: 'flex', gap: 16, alignItems: 'center', padding: '8px 0',
    borderBottom: '1px solid #f0f0f0', fontSize: 13,
  },
  noReplyName: { fontWeight: 600, color: '#1a1a1a', minWidth: 120 },
  noReplyCompany: { color: '#555', minWidth: 100 },
  noReplyDays: { color: '#dc2626', fontWeight: 600 },
  noReplyStep: { color: '#888' },
  nextTag: {
    padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600,
    background: 'rgba(22,163,74,0.08)', color: '#16a34a',
  },

  // Performance
  recCard: {
    background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8,
    padding: 14, marginBottom: 10,
  },
  recHeader: { display: 'flex', gap: 8, marginBottom: 6 },
  priorityTag: { fontSize: 11, fontWeight: 700, textTransform: 'uppercase' },
  recCategory: { fontSize: 11, color: '#888', textTransform: 'uppercase' },
  recTitle: { fontSize: 14, fontWeight: 600, color: '#1a1a1a' },
  recDesc: { fontSize: 13, color: '#555', marginTop: 4, lineHeight: 1.6 },
  metricRow: {
    display: 'flex', gap: 24, padding: '8px 0', borderBottom: '1px solid #f0f0f0',
    fontSize: 13, textTransform: 'capitalize',
  },
  metricLabel: { fontWeight: 600, color: '#1a1a1a', minWidth: 120 },

  // Context
  ctxSection: { marginBottom: 16, fontSize: 13, color: '#555', lineHeight: 1.7 },
  objection: { padding: '8px 0', borderBottom: '1px solid #f0f0f0' },
  objQ: { fontWeight: 600, color: '#1a1a1a', fontSize: 13 },
  objA: { color: '#555', fontSize: 13, marginTop: 4 },
  answerBox: {
    marginTop: 12, padding: 14, background: '#fafafa', border: '1px solid #e0e0e0',
    borderRadius: 8, fontSize: 13, color: '#1a1a1a', lineHeight: 1.7,
  },

  // Logs
  logTitle: { fontSize: 14, fontWeight: 600, color: '#1a1a1a', marginBottom: 12 },
  logRow: {
    display: 'flex', gap: 12, alignItems: 'center', padding: '8px 0',
    borderBottom: '1px solid #f0f0f0', fontSize: 12,
  },
  logAgent: {
    padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700,
    background: 'rgba(255,69,0,0.08)', color: '#ff4500', textTransform: 'uppercase',
    whiteSpace: 'nowrap',
  },
  logAction: { fontWeight: 600, color: '#1a1a1a', whiteSpace: 'nowrap' },
  logDetail: { color: '#555', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  logTime: { color: '#888', whiteSpace: 'nowrap' },
}
