import { useEffect, useState } from 'react'
import { MessageSquare, CheckCircle, AlertTriangle, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import StatusBadge from '../components/StatusBadge'
import { getAllReplies, markReplyHandled } from '../api/client'
import toast from 'react-hot-toast'

const INTENT_META = {
  interested:    { color: '#10b981', bg: 'rgba(16,185,129,0.1)',   label: 'Interested' },
  question:      { color: '#3b82f6', bg: 'rgba(59,130,246,0.1)',   label: 'Question' },
  demo:          { color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)',   label: 'Demo' },
  not_interested:{ color: '#ef4444', bg: 'rgba(239,68,68,0.1)',    label: 'Not Interested' },
  out_of_office: { color: '#9ca3af', bg: 'rgba(156,163,175,0.1)', label: 'Out of Office' },
  unsubscribe:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)',   label: 'Unsubscribe' },
}

export default function Replies() {
  const [replies, setReplies] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedReply, setExpandedReply] = useState(null)

  useEffect(() => {
    getAllReplies().then(setReplies).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleMarkHandled = async (replyId) => {
    try {
      await markReplyHandled(replyId)
      setReplies(replies.map(r => r.id === replyId ? { ...r, is_handled: true } : r))
      toast.success('Reply marked as handled')
    } catch (err) {
      toast.error(err.message)
    }
  }

  if (loading) return (
    <div style={{ padding:'40px 0' }}>
      {Array(4).fill(0).map((_,i) => (
        <div key={i} style={{ height:'90px', borderRadius:'14px', marginBottom:'12px' }} className="skeleton" />
      ))}
    </div>
  )

  const unhandled = replies.filter(r => !r.is_handled).length

  return (
    <div className="animate-in">
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.headerIcon}><MessageSquare size={20} color="#ff4500" /></div>
          <div>
            <h1 style={styles.title}>Replies</h1>
            <p style={styles.subtitle}>
              {unhandled > 0
                ? <><span style={styles.urgentBadge}>{unhandled} unhandled</span> · {replies.length} total</>
                : `${replies.length} total replies`}
            </p>
          </div>
        </div>
      </div>

      {/* Intent summary chips */}
      <div style={styles.intentGrid}>
        {Object.entries(INTENT_META).map(([intent, meta]) => {
          const count = replies.filter(r => r.intent === intent).length
          return (
            <div key={intent} style={{ ...styles.intentChip, background: meta.bg, borderColor: `${meta.color}30` }}>
              <span style={{ ...styles.intentCount, color: meta.color }}>{count}</span>
              <span style={{ ...styles.intentLabel, color: meta.color }}>{meta.label}</span>
            </div>
          )
        })}
      </div>

      {replies.length === 0 ? (
        <Card>
          <div style={styles.empty}>
            <div style={styles.emptyIcon}><MessageSquare size={26} color="#ff4500" /></div>
            <p style={styles.emptyTitle}>No replies yet</p>
            <p style={styles.emptyText}>Replies will appear here once leads respond to your outreach.</p>
          </div>
        </Card>
      ) : (
        <div style={styles.list}>
          {replies.map((reply) => {
            const isExpanded = expandedReply === reply.id
            const meta = INTENT_META[reply.intent] || { color: '#9ca3af', bg: 'rgba(156,163,175,0.1)' }
            return (
              <div key={reply.id} style={{ ...styles.replyCard, borderLeft: `3px solid ${meta.color}` }}>
                {/* Top accent */}
                <span style={{ position:'absolute', top:0, left:0, right:0, height:'2px',
                  background:`linear-gradient(90deg, ${meta.color}, transparent)`, borderRadius:'14px 14px 0 0' }} />

                <div style={styles.replyHeader}>
                  <div style={styles.replyLeft}>
                    <div style={{ ...styles.replyAvatar, background: meta.bg, color: meta.color }}>
                      {reply.from_email?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div>
                      <div style={styles.replyFrom}>{reply.from_email}</div>
                      <div style={styles.replySubject}>{reply.subject}</div>
                    </div>
                  </div>
                  <div style={styles.replyRight}>
                    <StatusBadge status={reply.intent} />
                    {reply.is_handled
                      ? <span style={styles.handledBadge}><CheckCircle size={12} /> Handled</span>
                      : <span style={styles.pendingBadge}><AlertTriangle size={12} /> Pending</span>
                    }
                    <span style={styles.replyDate}>{new Date(reply.received_at).toLocaleString()}</span>
                    <button
                      style={styles.expandBtn}
                      onClick={() => setExpandedReply(isExpanded ? null : reply.id)}
                    >
                      {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                    </button>
                  </div>
                </div>

                {/* Preview */}
                <div style={styles.replyPreview} onClick={() => setExpandedReply(isExpanded ? null : reply.id)}>
                  {reply.body.slice(0, 180)}{reply.body.length > 180 ? '...' : ''}
                </div>

                {/* Expanded */}
                {isExpanded && (
                  <div style={styles.expanded} className="animate-in">
                    <div style={styles.fullBody}>
                      <div style={styles.bodyLabel}>Full Reply</div>
                      <p style={styles.bodyText}>{reply.body}</p>
                    </div>
                    {reply.ai_draft_reply && (
                      <div style={styles.aiDraft}>
                        <div style={styles.aiLabel}>
                          <Sparkles size={13} color="#8b5cf6" />
                          AI Draft Reply
                        </div>
                        <p style={styles.bodyText}>{reply.ai_draft_reply}</p>
                      </div>
                    )}
                    {!reply.is_handled && (
                      <div style={{ marginTop: '12px' }}>
                        <Button size="sm" variant="success" onClick={() => handleMarkHandled(reply.id)}>
                          <CheckCircle size={13} /> Mark Handled
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

const styles = {
  header: { marginBottom:'22px' },
  headerLeft: { display:'flex', alignItems:'center', gap:'14px' },
  headerIcon: {
    width:'44px', height:'44px', borderRadius:'12px',
    background:'rgba(255,69,0,0.08)',
    display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0,
  },
  title: { fontSize:'24px', fontWeight:800, letterSpacing:'-0.3px' },
  subtitle: { fontSize:'13px', color:'var(--text-muted)', marginTop:'3px', display:'flex', alignItems:'center', gap:'6px' },
  urgentBadge: {
    fontSize:'11px', fontWeight:700, padding:'2px 8px', borderRadius:'20px',
    background:'rgba(255,69,0,0.1)', color:'#ff4500',
  },
  intentGrid: {
    display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(140px,1fr))',
    gap:'10px', marginBottom:'22px',
  },
  intentChip: {
    display:'flex', alignItems:'center', justifyContent:'space-between',
    padding:'12px 14px', borderRadius:'12px', border:'1px solid',
  },
  intentCount: { fontSize:'22px', fontWeight:800 },
  intentLabel: { fontSize:'11px', fontWeight:700, textTransform:'uppercase', letterSpacing:'0.5px' },
  list: { display:'flex', flexDirection:'column', gap:'10px' },
  replyCard: {
    background:'#fff', border:'1px solid var(--border)', borderRadius:'14px',
    padding:'18px 20px', boxShadow:'var(--shadow-sm)', position:'relative', overflow:'hidden',
    transition:'var(--transition)',
  },
  replyHeader: { display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'10px' },
  replyLeft: { display:'flex', alignItems:'center', gap:'12px' },
  replyAvatar: {
    width:'36px', height:'36px', borderRadius:'9px',
    display:'flex', alignItems:'center', justifyContent:'center',
    fontSize:'14px', fontWeight:800, flexShrink:0,
  },
  replyFrom: { fontSize:'14px', fontWeight:700 },
  replySubject: { fontSize:'12px', color:'var(--text-muted)', marginTop:'2px' },
  replyRight: { display:'flex', alignItems:'center', gap:'8px', flexShrink:0 },
  handledBadge: {
    display:'inline-flex', alignItems:'center', gap:'4px',
    fontSize:'11px', fontWeight:700, padding:'3px 9px', borderRadius:'20px',
    background:'rgba(16,185,129,0.1)', color:'#047857',
  },
  pendingBadge: {
    display:'inline-flex', alignItems:'center', gap:'4px',
    fontSize:'11px', fontWeight:700, padding:'3px 9px', borderRadius:'20px',
    background:'rgba(245,158,11,0.1)', color:'#92400e',
  },
  replyDate: { fontSize:'11px', color:'var(--text-muted)' },
  expandBtn: {
    width:'28px', height:'28px', borderRadius:'7px', border:'1px solid var(--border)',
    background:'var(--bg-secondary)', display:'flex', alignItems:'center', justifyContent:'center',
    cursor:'pointer', color:'var(--text-muted)', transition:'all 0.15s',
  },
  replyPreview: {
    fontSize:'13px', color:'var(--text-secondary)', lineHeight:1.65,
    padding:'10px 12px', background:'var(--bg-secondary)', borderRadius:'9px',
    cursor:'pointer',
  },
  expanded: { marginTop:'12px' },
  fullBody: {
    padding:'14px', background:'var(--bg-secondary)', borderRadius:'10px',
    marginBottom:'10px', border:'1px solid var(--border)',
  },
  aiDraft: {
    padding:'14px', background:'rgba(139,92,246,0.06)', borderRadius:'10px',
    border:'1px solid rgba(139,92,246,0.2)', marginBottom:'10px',
  },
  bodyLabel: {
    fontSize:'10px', fontWeight:700, textTransform:'uppercase',
    letterSpacing:'0.7px', color:'var(--text-muted)', marginBottom:'8px',
  },
  aiLabel: {
    display:'flex', alignItems:'center', gap:'5px',
    fontSize:'10px', fontWeight:700, textTransform:'uppercase',
    letterSpacing:'0.7px', color:'#8b5cf6', marginBottom:'8px',
  },
  bodyText: { fontSize:'13px', lineHeight:1.7, color:'var(--text-secondary)' },
  empty: {
    display:'flex', flexDirection:'column', alignItems:'center',
    padding:'52px 24px', textAlign:'center',
  },
  emptyIcon: {
    width:'56px', height:'56px', borderRadius:'14px',
    background:'rgba(255,69,0,0.08)',
    display:'flex', alignItems:'center', justifyContent:'center', marginBottom:'14px',
  },
  emptyTitle: { fontSize:'15px', fontWeight:700, marginBottom:'6px' },
  emptyText: { fontSize:'13px', color:'var(--text-muted)', maxWidth:'300px' },
}
