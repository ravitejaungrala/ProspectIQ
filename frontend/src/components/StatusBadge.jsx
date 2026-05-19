export default function StatusBadge({ status, size = 'sm' }) {
  const config = statusConfig[status] || statusConfig.default
  const padding = size === 'sm' ? '3px 10px' : '5px 14px'
  const fontSize = size === 'sm' ? '11px' : '13px'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding,
        fontSize,
        fontWeight: 600,
        borderRadius: '20px',
        background: config.bg,
        color: config.color,
        textTransform: 'capitalize',
        letterSpacing: '0.02em',
      }}
    >
      <span style={{
        width: '6px', height: '6px', borderRadius: '50%',
        background: config.color,
      }} />
      {config.label || status.replace(/_/g, ' ')}
    </span>
  )
}

const statusConfig = {
  setup: { bg: 'rgba(37, 99, 235, 0.1)', color: '#2563eb', label: 'Setup' },
  finding_leads: { bg: 'rgba(217, 119, 6, 0.1)', color: '#d97706', label: 'Finding Leads' },
  verifying: { bg: 'rgba(217, 119, 6, 0.1)', color: '#d97706', label: 'Verifying' },
  outreach: { bg: 'rgba(255, 69, 0, 0.1)', color: '#ff4500', label: 'Outreach' },
  active: { bg: 'rgba(22, 163, 74, 0.1)', color: '#16a34a', label: 'Active' },
  paused: { bg: 'rgba(100, 116, 139, 0.1)', color: '#64748b', label: 'Paused' },
  completed: { bg: 'rgba(22, 163, 74, 0.1)', color: '#16a34a', label: 'Completed' },
  // Lead statuses
  raw: { bg: 'rgba(100, 116, 139, 0.1)', color: '#64748b', label: 'Raw' },
  verified: { bg: 'rgba(37, 99, 235, 0.1)', color: '#2563eb', label: 'Verified' },
  scored: { bg: 'rgba(217, 119, 6, 0.1)', color: '#d97706', label: 'Scored' },
  clean: { bg: 'rgba(22, 163, 74, 0.1)', color: '#16a34a', label: 'Clean' },
  enrolled: { bg: 'rgba(255, 69, 0, 0.1)', color: '#ff4500', label: 'Enrolled' },
  contacted: { bg: 'rgba(255, 69, 0, 0.1)', color: '#ff4500', label: 'Contacted' },
  replied: { bg: 'rgba(217, 119, 6, 0.1)', color: '#d97706', label: 'Replied' },
  converted: { bg: 'rgba(22, 163, 74, 0.1)', color: '#16a34a', label: 'Converted' },
  dropped: { bg: 'rgba(220, 38, 38, 0.1)', color: '#dc2626', label: 'Dropped' },
  // Email statuses
  valid: { bg: 'rgba(22, 163, 74, 0.1)', color: '#16a34a', label: 'Valid' },
  risky: { bg: 'rgba(253, 203, 110, 0.15)', color: '#fdcb6e', label: 'Risky' },
  invalid: { bg: 'rgba(255, 118, 117, 0.15)', color: '#ff7675', label: 'Invalid' },
  pending: { bg: 'rgba(99, 110, 114, 0.15)', color: '#636e72', label: 'Pending' },
  sent: { bg: 'rgba(108, 92, 231, 0.15)', color: '#a29bfe', label: 'Sent' },
  // Reply intents
  interested: { bg: 'rgba(0, 206, 201, 0.15)', color: '#00cec9', label: 'Interested' },
  question: { bg: 'rgba(116, 185, 255, 0.15)', color: '#74b9ff', label: 'Question' },
  demo: { bg: 'rgba(0, 206, 201, 0.15)', color: '#00cec9', label: 'Demo' },
  not_interested: { bg: 'rgba(255, 118, 117, 0.15)', color: '#ff7675', label: 'Not Interested' },
  out_of_office: { bg: 'rgba(99, 110, 114, 0.15)', color: '#636e72', label: 'Out of Office' },
  unsubscribe: { bg: 'rgba(255, 118, 117, 0.15)', color: '#ff7675', label: 'Unsubscribe' },
  default: { bg: 'rgba(99, 110, 114, 0.15)', color: '#636e72' },
}
