import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Rocket, Plus, ExternalLink, Trash2, X } from 'lucide-react'
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
    if (!window.confirm(`Delete campaign "${name || 'Untitled'}"? This will remove all leads, emails, and analytics.`)) return
    try {
      await deleteCampaign(id)
      toast.success('Campaign deleted')
      setCampaigns(campaigns.filter(c => c.id !== id))
    } catch (err) {
      toast.error(err.message)
    }
  }

  if (loading) return (
    <div style={{ padding:'40px 0' }}>
      {Array(3).fill(0).map((_,i) => (
        <div key={i} style={{ height:'72px', borderRadius:'14px', marginBottom:'12px' }} className="skeleton" />
      ))}
    </div>
  )

  return (
    <div className="animate-in">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Campaigns</h1>
          <p style={styles.subtitle}>{campaigns.length} campaign{campaigns.length !== 1 ? 's' : ''} running</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? <X size={15} /> : <Plus size={15} />}
          {showCreate ? 'Cancel' : 'New Campaign'}
        </Button>
      </div>

      {showCreate && (
        <Card style={{ marginBottom: '22px' }} accent>
          <div style={styles.createHeader}>
            <div style={styles.createStep}>Stage 1</div>
            <h3 style={styles.createTitle}>Setup Campaign</h3>
          </div>
          <p style={styles.createDesc}>
            Paste your product URL. Our AI will scrape the website, extract a product summary,
            and build an ideal customer profile automatically.
          </p>

          <input
            type="url"
            placeholder="https://your-product.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            style={styles.input}
          />

          <div style={styles.senderSection}>
            <div style={styles.senderLabel}>Sender Info</div>
            <div style={styles.senderGrid}>
              <input type="text" placeholder="Your Name"  value={senderName}  onChange={(e) => setSenderName(e.target.value)}  style={styles.input} />
              <input type="text" placeholder="Your Title" value={senderTitle} onChange={(e) => setSenderTitle(e.target.value)} style={styles.input} />
              <input type="email" placeholder="Your Email" value={senderEmail} onChange={(e) => setSenderEmail(e.target.value)} style={styles.input} />
              <input type="tel"  placeholder="Your Phone" value={senderPhone} onChange={(e) => setSenderPhone(e.target.value)} style={styles.input} />
            </div>
          </div>

          <div style={{ marginTop: '18px' }}>
            <Button onClick={handleCreate} disabled={creating || !url.trim()}>
              {creating
                ? <><span style={styles.spinner} />Analyzing...</>
                : <><Rocket size={14} />Analyze & Create</>
              }
            </Button>
          </div>
        </Card>
      )}

      {campaigns.length === 0 ? (
        <Card>
          <div style={styles.empty}>
            <div style={styles.emptyIcon}><Rocket size={26} color="#ff4500" /></div>
            <p style={styles.emptyTitle}>No campaigns yet</p>
            <p style={styles.emptyText}>Click "New Campaign" to get started!</p>
          </div>
        </Card>
      ) : (
        <div style={styles.list}>
          {campaigns.map((c) => (
            <Card key={c.id} onClick={() => navigate(`/campaigns/${c.id}`)}>
              <div style={styles.row}>
                <div style={styles.rowLeft}>
                  <div style={styles.campaignIcon}>
                    <Rocket size={15} color="#ff4500" />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={styles.name}>{c.product_name || 'Processing...'}</div>
                    <div style={styles.url}>
                      <ExternalLink size={11} style={{ flexShrink: 0 }} />
                      <span style={{ overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{c.product_url}</span>
                    </div>
                  </div>
                </div>
                <div style={styles.rowRight}>
                  <span style={styles.leadsChip}>{c.lead_count} leads</span>
                  <StatusBadge status={c.status} />
                  <span style={styles.date}>{new Date(c.created_at).toLocaleDateString()}</span>
                  <button
                    onClick={(e) => handleDelete(e, c.id, c.product_name)}
                    style={styles.deleteBtn}
                    title="Delete campaign"
                    onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(239,68,68,0.08)'; e.currentTarget.style.color = '#ef4444' }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-muted)' }}
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
  header: { display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'24px' },
  title: { fontSize:'26px', fontWeight:800, letterSpacing:'-0.4px' },
  subtitle: { fontSize:'13px', color:'var(--text-muted)', marginTop:'4px' },
  createHeader: { display:'flex', alignItems:'center', gap:'10px', marginBottom:'8px' },
  createStep: {
    fontSize:'10px', fontWeight:700, padding:'3px 10px', borderRadius:'20px',
    background:'rgba(255,69,0,0.1)', color:'#ff4500', letterSpacing:'0.4px',
  },
  createTitle: { fontSize:'15px', fontWeight:700 },
  createDesc: { fontSize:'13px', color:'var(--text-secondary)', marginBottom:'16px', lineHeight:1.6 },
  input: {
    width:'100%', padding:'11px 14px', borderRadius:'10px', marginBottom:'10px',
    border:'1.5px solid var(--border)', background:'var(--bg-secondary)',
    color:'var(--text-primary)', fontSize:'14px', outline:'none',
    transition:'border-color 0.15s',
  },
  senderSection: { marginTop:'4px' },
  senderLabel: {
    fontSize:'11px', fontWeight:700, color:'var(--text-muted)',
    textTransform:'uppercase', letterSpacing:'0.7px', marginBottom:'10px',
  },
  senderGrid: { display:'grid', gridTemplateColumns:'1fr 1fr', gap:'10px' },
  spinner: {
    display:'inline-block', width:'13px', height:'13px', borderRadius:'50%',
    border:'2px solid rgba(255,255,255,0.3)', borderTopColor:'#fff',
    animation:'spin 0.7s linear infinite',
  },
  list: { display:'flex', flexDirection:'column', gap:'10px' },
  row: { display:'flex', justifyContent:'space-between', alignItems:'center', gap:'12px' },
  rowLeft: { display:'flex', alignItems:'center', gap:'12px', flex:1, minWidth:0 },
  campaignIcon: {
    width:'36px', height:'36px', borderRadius:'9px', background:'rgba(255,69,0,0.08)',
    display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0,
  },
  rowRight: { display:'flex', alignItems:'center', gap:'10px', flexShrink:0 },
  name: { fontSize:'14px', fontWeight:700, color:'#111' },
  url: {
    fontSize:'11px', color:'var(--text-muted)', marginTop:'3px',
    display:'flex', alignItems:'center', gap:'4px', maxWidth:'300px', overflow:'hidden',
  },
  leadsChip: {
    fontSize:'12px', fontWeight:600, color:'#374151',
    background:'var(--bg-secondary)', padding:'4px 10px',
    borderRadius:'20px', border:'1px solid var(--border)', flexShrink:0,
  },
  date: { fontSize:'12px', color:'var(--text-muted)' },
  deleteBtn: {
    display:'flex', alignItems:'center', justifyContent:'center',
    width:'30px', height:'30px', borderRadius:'7px',
    background:'transparent', border:'none',
    color:'var(--text-muted)', cursor:'pointer', transition:'all 0.15s',
  },
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
  emptyText: { fontSize:'13px', color:'var(--text-muted)' },
}
