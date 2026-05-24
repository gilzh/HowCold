import type { Chore } from '../types';

interface ChoreCardProps {
  chore: Chore;
  dateStr: string;
  compact?: boolean;
  onToggleComplete: (id: string, dateStr: string) => void;
  onClick: (chore: Chore) => void;
}

export function ChoreCard({
  chore,
  dateStr,
  compact = false,
  onToggleComplete,
  onClick,
}: ChoreCardProps) {
  const isCompleted = chore.completed[dateStr];

  return (
    <div
      className={`chore-card ${isCompleted ? 'completed' : ''} ${compact ? 'compact' : ''}`}
      style={{ borderLeftColor: chore.color }}
      onClick={(e) => {
        e.stopPropagation();
        onClick(chore);
      }}
    >
      <button
        className="chore-checkbox"
        onClick={(e) => {
          e.stopPropagation();
          onToggleComplete(chore.id, dateStr);
        }}
        style={{
          borderColor: chore.color,
          backgroundColor: isCompleted ? chore.color : 'transparent',
        }}
      >
        {isCompleted && (
          <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
            <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </button>
      <span className={`chore-title ${isCompleted ? 'struck' : ''}`}>
        {chore.title}
      </span>
      {chore.recurrence && (
        <span className="recurrence-icon" title={`Repeats ${chore.recurrence.frequency}`}>
          &#x21bb;
        </span>
      )}
    </div>
  );
}
