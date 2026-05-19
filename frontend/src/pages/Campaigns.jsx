import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Rocket, Plus, ExternalLink, Trash2 } from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import StatusBadge from '../components/StatusBadge'
import { getCampaigns, createCampaign, deleteCampaign } from '../api/client'
import toast from 'react-hot-toast'

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [url, setUrl] = useState('')
  const [senderName, setSenderName] = useState('')
  const [senderTitle, setSenderTitle] = useState('')
  const [senderEmail, setSenderEmail] = useState('')
  const [senderPhone, setSenderPhone] = useState('')
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()

  const load = () => {
    getCampaigns().then(setCampaigns).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    if (!url.trim()) return
    setCreating(true)
    try {
      const campaign = await createCampaign({
        product_url: url.trim(),
        sender_name: senderName.trim(),
        sender_title: senderTitle.trim(),
        sender_email: senderEmail.trim(),
        sender_phone: senderPhone.trim(),
      })
      toast.success('Campaign created! AI is analyzing your product...')
      setCampaigns([campaign, ...campaigns])
      setUrl(''); setSenderName(''); setSenderTitle(''); setSenderEmail(''); setSenderPhone('')
      setShowCreate(false)
      setTimeout(() => navigate(`/campaigns/${campaign.id}`), 1000)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (e, id, name) => {
    e.stopPropagation()
    if (!window.confirm(`Delete campaign "${name || 'Untitled'}"? This will remove all leads, emails, and analytics for this campaign.`)) return
    try {
      await deleteCampaign(id)
      toast.success('Campaign deleted')
      setCampaigns(campaigns.filter(c => c.id !== id))
    } catch (err) {
      toast.error(err.message)
    }
  }

  if (loading) return <div style={styles.loading}>Loading...</div>

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Campaigns</h1>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus size={16} /> New Campaign
        </Button>
      </div>

      {showCreate && (
        <Card style={{ marginBottom: '24px' }}>
          <h3 style={styles.createTitle}>Stage 1 — Setup</h3>
          <p style={styles.createDesc}>
            Paste your product URL. Our AI will scrape the website, extract a product summary,
            and build an ideal customer profile automatically.
          </p>
          <div style={styles.createForm}>
            <input
              type="url"
              placeholder="https://your-product.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              style={styles.input}
            />
          </div>
          <div style={styles.senderSection}>
            <div style={styles.senderLabel}>Sender Info (for email templates)</div>
            <div style={styles.senderGrid}>
              <input
                type="text"
                placeholder="Your Name"
                value={senderName}
                onChange={(e) => setSenderName(e.target.value)}
                style={styles.input}
              />
              <input
                type="text"
                placeholder="Your Title (e.g. Growth Lead)"
                value={senderTitle}
                onChange={(e) => setSenderTitle(e.target.value)}
                style={styles.input}
              />
              <input
                type="email"
                placeholder="Your Email"
                value={senderEmail}
                onChange={(e) => setSenderEmail(e.target.value)}
                style={styles.input}
              />
              <input
                type="tel"
                placeholder="Your Phone"
                value={senderPhone}
                onChange={(e) => setSenderPhone(e.target.value)}
                style={styles.input}
              />
            </div>
          </div>
          <div style={{ marginTop: '16px' }}>
            <Button onClick={handleCreate} disabled={creating || !url.trim()}>
              {creating ? 'Creating...' : 'Analyze & Create'}
            </Button>
          </div>
        </Card>
      )}

      {campaigns.length === 0 ? (
        <Card>
          <div style={styles.empty}>
            <Rocket size={48} color="var(--text-muted)" />
            <p style={{ color: 'var(--text-secondary)', marginTop: '12px' }}>
              No campaigns yet. Click "New Campaign" to get started!
            </p>
          </div>
        </Card>
      ) : (
        <div style={styles.list}>
          {campaigns.map((c) => (
            <Card key={c.id} onClick={() => navigate(`/campaigns/${c.id}`)}>
              <div style={styles.row}>
                <div style={styles.rowLeft}>
                  <div style={styles.name}>
                    {c.product_name || 'Processing...'}
                  </div>
                  <div style={styles.url}>
                    <ExternalLink size={12} /> {c.product_url}
                  </div>
                </div>
                <div style={styles.rowRight}>
                  <span style={styles.leads}>{c.lead_count} leads</span>
                  <StatusBadge status={c.status} />
                  <span style={styles.date}>
                    {new Date(c.created_at).toLocaleDateString()}
                  </span>
                  <button
                    onClick={(e) => handleDelete(e, c.id, c.product_name)}
                    style={styles.deleteBtn}
                    title="Delete campaign"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
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
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: '24px',
  },
  title: { fontSize: '28px', fontWeight: 700 },
  createTitle: { fontSize: '16px', fontWeight: 600, marginBottom: '8px' },
  createDesc: { fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '16px' },
  createForm: { display: 'flex', gap: '12px', marginBottom: '16px' },
  senderSection: { marginTop: '4px' },
  senderLabel: { fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' },
  senderGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' },
  input: {
    flex: 1, padding: '10px 16px', borderRadius: '8px',
    border: '1px solid var(--border)', background: 'var(--bg-primary)',
    color: 'var(--text-primary)', fontSize: '14px', outline: 'none',
  },
  list: { display: 'flex', flexDirection: 'column', gap: '12px' },
  row: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  },
  rowLeft: {},
  rowRight: {
    display: 'flex', alignItems: 'center', gap: '12px',
  },
  name: { fontSize: '15px', fontWeight: 600 },
  url: {
    fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px',
    display: 'flex', alignItems: 'center', gap: '4px',
  },
  leads: {
    fontSize: '12px', color: 'var(--text-secondary)',
    background: 'var(--bg-primary)', padding: '4px 10px', borderRadius: '20px',
  },
  date: { fontSize: '12px', color: 'var(--text-muted)' },
  deleteBtn: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: '30px', height: '30px', borderRadius: '6px',
    background: 'none', border: '1px solid transparent',
    color: 'var(--text-muted)', cursor: 'pointer', transition: 'all 0.15s',
  },
  empty: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', padding: '48px', textAlign: 'center',
  },
}
