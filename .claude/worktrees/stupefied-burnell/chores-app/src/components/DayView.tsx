import { format } from 'date-fns';
import { useMemo } from 'react';
import type { Chore } from '../types';
import { getChoresForRange } from '../utils/recurrence';
import { ChoreCard } from './ChoreCard';

interface DayViewProps {
  selectedDate: Date;
  chores: Chore[];
  onToggleComplete: (id: string, dateStr: string) => void;
  onClickChore: (chore: Chore) => void;
  onClickDate: (date: Date) => void;
}

export function DayView({
  selectedDate,
  chores,
  onToggleComplete,
  onClickChore,
  onClickDate,
}: DayViewProps) {
  const dateStr = format(selectedDate, 'yyyy-MM-dd');

  const choreMap = useMemo(
    () => getChoresForRange(chores, selectedDate, selectedDate),
    [chores, selectedDate.getTime()]
  );

  const dayChores = choreMap.get(dateStr) || [];

  return (
    <div className="day-view" onClick={() => onClickDate(selectedDate)}>
      <div className="day-view-header">
        <span className="day-view-day">{format(selectedDate, 'EEEE')}</span>
        <span className="day-view-date">{format(selectedDate, 'MMMM d, yyyy')}</span>
      </div>

      <div className="day-view-body">
        {dayChores.length === 0 ? (
          <div className="day-view-empty">
            No chores scheduled. Click to add one.
          </div>
        ) : (
          dayChores.map((chore) => (
            <div key={chore.id} className="day-view-item">
              <ChoreCard
                chore={chore}
                dateStr={dateStr}
                onToggleComplete={onToggleComplete}
                onClick={onClickChore}
              />
              {chore.description && (
                <p className="day-view-description">{chore.description}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
