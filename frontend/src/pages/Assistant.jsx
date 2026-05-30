import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Sparkles, Search, PenLine, Building2, Users,
  ArrowUp, ExternalLink, Plus, Mail, Linkedin,
} from 'lucide-react'
import { sendChatMessage } from '../api/client'

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 18) return 'Good afternoon'
  return 'Good evening'
}

const CARDS = [
  {
    icon: Search,
    title: 'Find prospects',
    sub: 'Find contacts that match my ideal customer profile',
    prompt: 'I want to find prospects that match my ideal customer profile.',
  },
  {
    icon: PenLine,
    title: 'Draft outreach',
    sub: 'Draft personalized outreach for my contacts',
    prompt: 'Help me draft personalized outreach for my contacts.',
  },
  {
    icon: Building2,
    title: 'Research a company',
    sub: "Tell me about a company I'm about to reach out to",
    prompt: 'I want to research a company before I reach out to them.',
  },
  {
    icon: Users,
    title: 'Prep for a meeting',
    sub: 'Help me prepare for an upcoming call with a prospect',
    prompt: 'Help me prepare for an upcoming call with a prospect.',
  },
]

export default function Assistant() {
  const [messages, setMessages] = useState([])
  const [context, setContext] = useState({})
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text) => {
    const content = (text ?? input).trim()
    if (!content || loading) return
    const next = [...messages, { role: 'user', content }]
    setMessages(next)
    setInput('')
    setLoading(true)
    try {
      const apiMsgs = next.map((m) => ({ role: m.role, content: m.content }))
      const res = await sendChatMessage(apiMsgs, context)
      setContext(res.context || context)
      setMessages([
        ...next,
        { role: 'assistant', content: res.reply || '', data: res.data || {} },
      ])
    } catch (e) {
      setMessages([
        ...next,
        { role: 'assistant', content: 'Sorry - something went wrong: ' + e.message, data: {} },
      ])
    } finally {
      setLoading(false)
    }
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const newChat = () => {
    setMessages([])
    setContext({})
    setInput('')
  }

  const hasChat = messages.length > 0

  return (
    <div style={styles.wrap}>
      <style>{spinnerCss}</style>

      <div style={styles.topBar}>
        <div style={styles.brand}>
          <span style={styles.brandDot}><Sparkles size={15} color="#fff" /></span>
          ProspectIQ Assistant
        </div>
        {hasChat && (
          <button style={styles.newChat} onClick={newChat}>
            <Plus size={15} /> New chat
          </button>
        )}
      </div>

      <div style={styles.scroll}>
        {!hasChat ? (
          <Welcome onPick={send} />
        ) : (
          <div style={styles.thread}>
            {messages.map((m, i) =>
              m.role === 'user' ? (
                <div key={i} style={styles.userRow}>
                  <div style={styles.userBubble}>{m.content}</div>
                </div>
              ) : (
                <AssistantMessage key={i} message={m} navigate={navigate} />
              )
            )}
            {loading && <Thinking />}
            <div ref={endRef} />
          </div>
        )}
      </div>

      <div style={styles.composerWrap}>
        <div style={styles.composer}>
          <textarea
            style={styles.textarea}
            placeholder="Or ask me anything..."
            value={input}
            rows={1}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
          />
          <button
            style={{
              ...styles.sendBtn,
              ...(input.trim() && !loading ? styles.sendBtnActive : {}),
            }}
            onClick={() => send()}
            disabled={!input.trim() || loading}
            title="Send"
          >
            <ArrowUp size={18} />
          </button>
        </div>
        <div style={styles.hint}>
          ProspectIQ Assistant can research products, find leads and help with outreach.
        </div>
      </div>
    </div>
  )
}

function Welcome({ onPick }) {
  return (
    <div style={styles.welcome}>
      <h1 style={styles.greeting}>{greeting()}</h1>
      <div style={styles.introRow}>
        <span style={styles.introDot}><Sparkles size={16} color="#fff" /></span>
        <p style={styles.intro}>
          I'm the ProspectIQ Assistant. I help you find prospects, research
          companies, and craft outreach. Here's what I'd suggest:
        </p>
      </div>
      <div style={styles.cardGrid}>
        {CARDS.map((c) => {
          const Icon = c.icon
          return (
            <button key={c.title} style={styles.card} onClick={() => onPick(c.prompt)}>
              <Icon size={20} color="var(--accent)" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={styles.cardTitle}>{c.title}</div>
                <div style={styles.cardSub}>{c.sub}</div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function AssistantMessage({ message, navigate }) {
  const data = message.data || {}
  return (
    <div style={styles.botRow}>
      <span style={styles.botAvatar}><Sparkles size={14} color="#fff" /></span>
      <div style={styles.botBody}>
        {message.content && <div style={styles.botText}>{message.content}</div>}
        {data.campaign && <CampaignCard campaign={data.campaign} navigate={navigate} />}
        {data.leads && data.leads.length > 0 && <LeadsTable leads={data.leads} />}
        {data.research && <ResearchCard research={data.research} />}
      </div>
    </div>
  )
}

function CampaignCard({ campaign, navigate }) {
  return (
    <div style={styles.panel}>
      <div style={styles.panelHead}>
        <Building2 size={16} color="var(--accent)" />
        <span style={styles.panelTitle}>{campaign.product_name || 'Product'}</span>
      </div>
      {campaign.product_summary && (
        <p style={styles.panelText}>{campaign.product_summary}</p>
      )}
      {campaign.industries?.length > 0 && (
        <div style={styles.chips}>
          {campaign.industries.slice(0, 6).map((x) => (
            <span key={x} style={styles.chip}>{x}</span>
          ))}
        </div>
      )}
      {campaign.target_domains?.length > 0 && (
        <div style={styles.metaLine}>
          {campaign.target_domains.length} target company domains identified
        </div>
      )}
      <button style={styles.linkBtn} onClick={() => navigate(`/campaigns/${campaign.id}`)}>
        Open campaign <ExternalLink size={13} />
      </button>
    </div>
  )
}

function LeadsTable({ leads }) {
  return (
    <div style={styles.panel}>
      <div style={styles.panelHead}>
        <Users size={16} color="var(--accent)" />
        <span style={styles.panelTitle}>{leads.length} leads found</span>
      </div>
      <div style={styles.leadList}>
        {leads.map((l, i) => (
          <div key={i} style={styles.leadRow}>
            <div style={styles.leadMain}>
              <div style={styles.leadName}>{l.name || 'Unknown'}</div>
              <div style={styles.leadMeta}>
                {[l.title, l.company].filter(Boolean).join('  -  ')}
              </div>
            </div>
            <div style={styles.leadIcons}>
              {l.email && (
                <a href={`mailto:${l.email}`} style={styles.leadIcon} title={l.email}>
                  <Mail size={14} />
                </a>
              )}
              {l.linkedin_url && (
                <a href={l.linkedin_url} target="_blank" rel="noreferrer" style={styles.leadIcon} title="LinkedIn">
                  <Linkedin size={14} />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ResearchCard({ research }) {
  return (
    <div style={styles.panel}>
      <div style={styles.panelHead}>
        <Building2 size={16} color="var(--accent)" />
        <span style={styles.panelTitle}>{research.company}</span>
      </div>
      <p style={styles.panelText}>{research.brief}</p>
    </div>
  )
}

function Thinking() {
  return (
    <div style={styles.botRow}>
      <span style={styles.botAvatar}><Sparkles size={14} color="#fff" /></span>
      <div style={styles.thinking}>
        <span style={{ ...styles.dot, animationDelay: '0s' }} />
        <span style={{ ...styles.dot, animationDelay: '0.15s' }} />
        <span style={{ ...styles.dot, animationDelay: '0.3s' }} />
        <span style={styles.thinkingText}>Thinking...</span>
      </div>
    </div>
  )
}

const spinnerCss = `
@keyframes piq-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-4px); opacity: 1; }
}
`

const styles = {
  wrap: {
    display: 'flex',
    flexDirection: 'column',
    height: 'calc(100vh - 64px)',
    margin: '-32px',
    padding: '0',
  },
  topBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 28px',
    borderBottom: '1px solid var(--border)',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontWeight: 700,
    fontSize: '15px',
  },
  brandDot: {
    width: 26,
    height: 26,
    borderRadius: '50%',
    background: 'var(--accent)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  newChat: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    background: 'none',
    border: '1px solid var(--border)',
    borderRadius: '8px',
    padding: '7px 12px',
    fontSize: '13px',
    color: 'var(--text-secondary)',
  },
  scroll: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px 28px',
  },
  /* ---- welcome ---- */
  welcome: {
    maxWidth: '720px',
    margin: '0 auto',
    paddingTop: '6vh',
  },
  greeting: {
    fontSize: '34px',
    fontWeight: 700,
    textAlign: 'center',
    marginBottom: '28px',
  },
  introRow: {
    display: 'flex',
    gap: '12px',
    alignItems: 'flex-start',
    marginBottom: '24px',
  },
  introDot: {
    width: 30,
    height: 30,
    borderRadius: '50%',
    background: 'var(--accent)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  intro: {
    fontSize: '15px',
    color: 'var(--text-secondary)',
    lineHeight: 1.6,
  },
  cardGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '14px',
  },
  card: {
    display: 'flex',
    gap: '12px',
    alignItems: 'flex-start',
    textAlign: 'left',
    background: 'var(--bg-card)',
    border: '1px solid var(--border)',
    borderRadius: '12px',
    padding: '16px 18px',
    transition: 'border-color 0.15s, box-shadow 0.15s',
  },
  cardTitle: { fontSize: '14px', fontWeight: 600, marginBottom: '3px' },
  cardSub: { fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: 1.5 },
  /* ---- thread ---- */
  thread: {
    maxWidth: '760px',
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  userRow: { display: 'flex', justifyContent: 'flex-end' },
  userBubble: {
    background: 'var(--accent)',
    color: '#fff',
    padding: '10px 16px',
    borderRadius: '18px 18px 4px 18px',
    fontSize: '14px',
    maxWidth: '78%',
    whiteSpace: 'pre-wrap',
    lineHeight: 1.5,
  },
  botRow: { display: 'flex', gap: '12px', alignItems: 'flex-start' },
  botAvatar: {
    width: 28,
    height: 28,
    borderRadius: '50%',
    background: 'var(--accent)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    marginTop: '2px',
  },
  botBody: { flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '12px' },
  botText: {
    fontSize: '14.5px',
    color: 'var(--text-primary)',
    whiteSpace: 'pre-wrap',
    lineHeight: 1.65,
  },
  /* ---- panels ---- */
  panel: {
    border: '1px solid var(--border)',
    borderRadius: '12px',
    padding: '16px',
    background: 'var(--bg-card)',
  },
  panelHead: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' },
  panelTitle: { fontWeight: 600, fontSize: '14px' },
  panelText: { fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: 1.6 },
  chips: { display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '10px' },
  chip: {
    fontSize: '11.5px',
    background: 'var(--bg-secondary)',
    color: 'var(--text-secondary)',
    padding: '3px 9px',
    borderRadius: '20px',
  },
  metaLine: { fontSize: '12.5px', color: 'var(--text-muted)', marginTop: '10px' },
  linkBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '5px',
    marginTop: '12px',
    background: 'none',
    border: 'none',
    color: 'var(--accent)',
    fontSize: '13px',
    fontWeight: 600,
    padding: 0,
  },
  leadList: { display: 'flex', flexDirection: 'column' },
  leadRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
    padding: '9px 0',
    borderTop: '1px solid var(--border)',
  },
  leadMain: { minWidth: 0 },
  leadName: { fontSize: '13.5px', fontWeight: 600 },
  leadMeta: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  leadIcons: { display: 'flex', gap: '6px', flexShrink: 0 },
  leadIcon: {
    width: 28,
    height: 28,
    borderRadius: '6px',
    border: '1px solid var(--border)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'var(--text-secondary)',
  },
  /* ---- thinking ---- */
  thinking: { display: 'flex', alignItems: 'center', gap: '5px', paddingTop: '6px' },
  dot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    background: 'var(--accent)',
    display: 'inline-block',
    animation: 'piq-bounce 1s infinite ease-in-out',
  },
  thinkingText: { fontSize: '13px', color: 'var(--text-muted)', marginLeft: '6px' },
  /* ---- composer ---- */
  composerWrap: {
    padding: '12px 28px 18px',
    borderTop: '1px solid var(--border)',
  },
  composer: {
    maxWidth: '760px',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'flex-end',
    gap: '8px',
    border: '1px solid var(--border)',
    borderRadius: '14px',
    padding: '8px 8px 8px 16px',
    background: 'var(--bg-card)',
  },
  textarea: {
    flex: 1,
    border: 'none',
    outline: 'none',
    resize: 'none',
    fontSize: '14px',
    lineHeight: 1.5,
    maxHeight: '160px',
    padding: '6px 0',
    background: 'transparent',
    color: 'var(--text-primary)',
  },
  sendBtn: {
    width: 34,
    height: 34,
    borderRadius: '50%',
    border: 'none',
    background: 'var(--bg-secondary)',
    color: 'var(--text-muted)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  sendBtnActive: { background: 'var(--accent)', color: '#fff' },
  hint: {
    maxWidth: '760px',
    margin: '8px auto 0',
    textAlign: 'center',
    fontSize: '11.5px',
    color: 'var(--text-muted)',
  },
}
