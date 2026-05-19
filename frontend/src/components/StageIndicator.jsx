export default function StageIndicator({ stages, currentStage }) {
  const stageList = stages || [
    { key: 'setup', label: 'Setup', num: 1 },
    { key: 'finding_leads', label: 'Find Leads', num: 2 },
    { key: 'verifying', label: 'Verify & Score', num: 3 },
    { key: 'outreach', label: 'Reach Out', num: 4 },
    { key: 'active', label: 'Active', num: 5 },
  ]

  const currentIndex = stageList.findIndex(s => s.key === currentStage)

  return (
    <div style={styles.container}>
      {stageList.map((stage, index) => {
        const isCompleted = index < currentIndex
        const isCurrent = index === currentIndex
        const isUpcoming = index > currentIndex

        return (
          <div key={stage.key} style={styles.step}>
            <div style={{
              ...styles.circle,
              ...(isCompleted ? styles.completed : {}),
              ...(isCurrent ? styles.current : {}),
              ...(isUpcoming ? styles.upcoming : {}),
            }}>
              {isCompleted ? '✓' : stage.num}
            </div>
            <span style={{
              ...styles.label,
              color: isCurrent ? 'var(--accent-light)' : isCompleted ? 'var(--success)' : 'var(--text-muted)',
              fontWeight: isCurrent ? 600 : 400,
            }}>
              {stage.label}
            </span>
            {index < stageList.length - 1 && (
              <div style={{
                ...styles.line,
                background: isCompleted ? 'var(--success)' : 'var(--border)',
              }} />
            )}
          </div>
        )
      })}
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    gap: '0',
    padding: '20px 0',
  },
  step: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    position: 'relative',
  },
  circle: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '13px',
    fontWeight: 600,
    flexShrink: 0,
  },
  completed: {
    background: 'rgba(22, 163, 74, 0.1)',
    color: '#16a34a',
    border: '2px solid #16a34a',
  },
  current: {
    background: 'rgba(255, 69, 0, 0.1)',
    color: '#ff4500',
    border: '2px solid #ff4500',
  },
  upcoming: {
    background: '#f5f5f5',
    color: '#888888',
    border: '2px solid #e0e0e0',
  },
  label: {
    fontSize: '13px',
    whiteSpace: 'nowrap',
  },
  line: {
    width: '40px',
    height: '2px',
    marginLeft: '8px',
    marginRight: '8px',
    borderRadius: '1px',
  },
}
