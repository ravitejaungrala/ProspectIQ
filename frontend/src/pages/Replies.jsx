import { useEffect, useState } from 'react'
import { MessageSquare, CheckCircle, AlertTriangle } from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import StatusBadge from '../components/StatusBadge'
import { getAllReplies, markReplyHandled } from '../api/client'
import toast from 'react-hot-toast'

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

  if (loading) return <div style={styles.loading}>Loading...</div>

  const unhandled = replies.filter(r => !r.is_handled).length

  return (
    <div>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Stage 5 — Replies</h1>
          <p style={styles.subtitle}>
            Classify + respond to inbound replies. {unhandled > 0 && `${unhandled} unhandled.`}
          </p>
        </div>
      </div>

      {/* Intent summary cards */}
      <div style={styles.intentGrid}>
        {['interested', 'question', 'demo', 'not_interested', 'out_of_office', 'unsubscribe'].map((intent) => {
          const count = replies.filter(r => r.intent === intent).length
          return (
            <Card key={intent}>
              <div style={styles.intentCard}>
                <StatusBadge status={intent} size="sm" />
                <div style={styles.intentCount}>{count}</div>
              </div>
            </Card>
          )
        })}
      </div>

      {replies.length === 0 ? (
        <Card>
          <div style={styles.empty}>
            <MessageSquare size={48} color="var(--text-muted)" />
            <p style={{ color: 'var(--text-secondary)', marginTop: '12px' }}>
              No replies yet. Replies will appear here once leads respond to your outreach.
            </p>
          </div>
        </Card>
      ) : (
        <div style={styles.list}>
          {replies.map((reply) => (
            <Card key={reply.id}>
              <div style={styles.replyHeader}>
                <div style={styles.replyLeft}>
                  <div style={styles.replyFrom}>{reply.from_email}</div>
                  <div style={styles.replySubject}>{reply.subject}</div>
                </div>
                <div style={styles.replyRight}>
                  <StatusBadge status={reply.intent} />
                  {reply.is_handled ? (
                    <CheckCircle size={16} color="var(--success)" />
                  ) : (
                    <AlertTriangle size={16} color="var(--warning)" />
                  )}
                  <span style={styles.replyDate}>
                    {new Date(reply.received_at).toLocaleString()}
                  </span>
                </div>
              </div>

              <div
                style={styles.replyBody}
                onClick={() => setExpandedReply(expandedReply === reply.id ? null : reply.id)}
              >
                {reply.body.slice(0, 200)}{reply.body.length > 200 ? '...' : ''}
              </div>

              {expandedReply === reply.id && (
                <div style={styles.expanded}>
                  <div style={styles.fullBody}>
                    <strong>Full Reply:</strong>
                    <p>{reply.body}</p>
                  </div>
                  {reply.ai_draft_reply && (
                    <div style={styles.aiDraft}>
                      <strong>AI Draft Reply:</strong>
                      <p>{reply.ai_draft_reply}</p>
                    </div>
                  )}
                  <div style={styles.expandedActions}>
                    {!reply.is_handled && (
                      <Button size="sm" variant="success" onClick={() => handleMarkHandled(reply.id)}>
                        <CheckCircle size={14} /> Mark Handled
                      </Button>
                    )}
                  </div>
                </div>
              )}
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
    height: '50vh', color: 'var(--text-secondary)',
  },
  header: { marginBottom: '24px' },
  title: { fontSize: '24px', fontWeight: 700 },
  subtitle: { fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' },
  intentGrid: {
    display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
    gap: '12px', marginBottom: '24px',
  },
  intentCard: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  },
  intentCount: { fontSize: '20px', fontWeight: 700 },
  list: { display: 'flex', flexDirection: 'column', gap: '12px' },
  replyHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
    marginBottom: '8px',
  },
  replyLeft: {},
  replyRight: { display: 'flex', alignItems: 'center', gap: '8px' },
  replyFrom: { fontSize: '14px', fontWeight: 600 },
  replySubject: { fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' },
  replyDate: { fontSize: '12px', color: 'var(--text-muted)' },
  replyBody: {
    fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.7,
    padding: '12px', background: 'var(--bg-primary)', borderRadius: '8px',
    cursor: 'pointer',
  },
  expanded: { marginTop: '12px' },
  fullBody: {
    padding: '12px', background: 'var(--bg-primary)', borderRadius: '8px',
    fontSize: '13px', lineHeight: 1.7, marginBottom: '12px',
  },
  aiDraft: {
    padding: '12px', background: 'rgba(108, 92, 231, 0.08)',
    borderRadius: '8px', border: '1px solid rgba(108, 92, 231, 0.2)',
    fontSize: '13px', lineHeight: 1.7, marginBottom: '12px',
  },
  expandedActions: { display: 'flex', gap: '8px' },
  empty: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', padding: '48px', textAlign: 'center',
  },
}
