export default function Button({ children, onClick, variant = 'primary', size = 'md', disabled = false, style = {} }) {
  const baseStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '7px',
    border: 'none',
    borderRadius: '10px',
    fontWeight: 600,
    fontFamily: 'inherit',
    letterSpacing: '0.01em',
    transition: 'all 0.16s ease',
    opacity: disabled ? 0.5 : 1,
    pointerEvents: disabled ? 'none' : 'auto',
    cursor: disabled ? 'not-allowed' : 'pointer',
    ...sizeStyles[size],
    ...variantStyles[variant],
    ...style,
  }

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={baseStyle}
      onMouseEnter={(e) => {
        if (disabled) return
        const v = variantStyles[variant]
        if (variant === 'primary') {
          e.currentTarget.style.background = 'linear-gradient(135deg, #e63e00, #ff4500)'
          e.currentTarget.style.boxShadow = '0 4px 16px rgba(255,69,0,.35)'
          e.currentTarget.style.transform = 'translateY(-1px)'
        } else if (variant === 'secondary') {
          e.currentTarget.style.borderColor = '#ff4500'
          e.currentTarget.style.color = '#ff4500'
        } else {
          e.currentTarget.style.opacity = '0.85'
        }
      }}
      onMouseLeave={(e) => {
        if (disabled) return
        if (variant === 'primary') {
          e.currentTarget.style.background = variantStyles.primary.background
          e.currentTarget.style.boxShadow = variantStyles.primary.boxShadow
          e.currentTarget.style.transform = 'translateY(0)'
        } else if (variant === 'secondary') {
          e.currentTarget.style.borderColor = 'var(--border)'
          e.currentTarget.style.color = '#1a1a1a'
        } else {
          e.currentTarget.style.opacity = '1'
        }
      }}
    >
      {children}
    </button>
  )
}

const sizeStyles = {
  sm:  { padding: '6px 14px',  fontSize: '12px', borderRadius: '8px' },
  md:  { padding: '10px 20px', fontSize: '14px' },
  lg:  { padding: '13px 28px', fontSize: '15px' },
}

const variantStyles = {
  primary: {
    background: 'linear-gradient(135deg, #ff4500, #ff6035)',
    color: '#fff',
    boxShadow: '0 2px 10px rgba(255,69,0,.28)',
    border: 'none',
  },
  secondary: {
    background: '#ffffff',
    color: '#1a1a1a',
    border: '1px solid var(--border)',
    boxShadow: 'var(--shadow-sm)',
  },
  success: {
    background: 'rgba(16,185,129,0.1)',
    color: '#047857',
    border: '1px solid rgba(16,185,129,0.25)',
  },
  danger: {
    background: 'rgba(239,68,68,0.1)',
    color: '#dc2626',
    border: '1px solid rgba(239,68,68,0.2)',
  },
  ghost: {
    background: 'transparent',
    color: '#555555',
    border: '1px solid transparent',
  },
}
