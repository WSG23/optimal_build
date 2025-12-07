interface AllocationRingProps {
  data: {
    name: string
    value: number
    color: string
  }[]
  totalAllocation: number
  size?: number
}

export function AllocationRing({
  data,
  totalAllocation,
  size = 160,
}: AllocationRingProps) {
  const strokeWidth = 8
  const radius = (size - strokeWidth) / 2
  const center = size / 2
  const circumference = 2 * Math.PI * radius

  // Re-calculate pure dasharrays for separate paths (easier for independent styling/animation)
  let cumulativePercent = 0

  const ringSegments = data.map((item) => {
    const startPercent = cumulativePercent
    const lengthPercent = item.value / 100
    cumulativePercent += lengthPercent

    const dashArray = `${lengthPercent * circumference} ${circumference}`
    const rotate = startPercent * 360 - 90

    return {
      ...item,
      dashArray,
      rotate,
    }
  })

  // Format main label
  const labelValue = Math.round(totalAllocation)

  return (
    <div className="allocation-ring" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="allocation-ring__svg"
      >
        {/* Background Track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--ob-color-border-subtle)"
          strokeWidth={strokeWidth}
          opacity="0.2"
        />

        {/* Segments */}
        {ringSegments.map((segment) => (
          <circle
            key={segment.name}
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={segment.color}
            strokeWidth={strokeWidth}
            strokeDasharray={segment.dashArray}
            strokeDashoffset={0}
            transform={`rotate(${segment.rotate} ${center} ${center})`}
            className={`allocation-ring__segment ${segment.name === 'Unallocated' ? 'allocation-ring__segment--pulse' : ''}`}
            style={{
              // Add distinctive glow for colored segments
              filter:
                segment.name !== 'Unallocated'
                  ? `drop-shadow(0 0 4px ${segment.color})`
                  : 'none',
              transition: 'all 0.5s ease-out',
            }}
          />
        ))}
      </svg>

      {/* Center Label */}
      <div className="allocation-ring__center">
        <span className="allocation-ring__value">{labelValue}%</span>
        {totalAllocation >= 100 ? (
          <span className="allocation-ring__sub">ALLOCATED</span>
        ) : (
          <span className="allocation-ring__sub allocation-ring__sub--warning">
            PENDING
          </span>
        )}
      </div>
      {/* Decorative 3D Ring Effect (Pseudo-element handled in CSS usually, but adding a specialized glow container here) */}
      <div className="allocation-ring__glow-effect" />
    </div>
  )
}
