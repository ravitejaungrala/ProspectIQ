export default function Card({ children, style = {}, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '24px',
        transition: 'all 0.15s',
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        ...(onClick ? { cursor: 'pointer' } : {}),
        ...style,
      }}
      onMouseEnter={(e) => {
        if (onClick) {
          e.currentTarget.style.background = 'var(--bg-card-hover)'
          e.currentTarget.style.borderColor = 'var(--accent)'
        }
      }}
      onMouseLeave={(e) => {
        if (onClick) {
          e.currentTarget.style.background = 'var(--bg-card)'
          e.currentTarget.style.borderColor = 'var(--border)'
        }
      }}
    >
      {children}
    </div>
  )
}
