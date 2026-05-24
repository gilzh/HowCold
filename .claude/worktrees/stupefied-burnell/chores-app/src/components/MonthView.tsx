import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  format,
  isSameMonth,
  isSameDay,
} from 'date-fns';
import { useMemo } from 'react';
import type { Chore } from '../types';
import { getChoresForRange } from '../utils/recurrence';
import { ChoreCard } from './ChoreCard';

interface MonthViewProps {
  selectedDate: Date;
  chores: Chore[];
  onToggleComplete: (id: string, dateStr: string) => void;
  onClickChore: (chore: Chore) => void;
  onClickDate: (date: Date) => void;
}

const MAX_VISIBLE = 3;

export function MonthView({
  selectedDate,
  chores,
  onToggleComplete,
  onClickChore,
  onClickDate,
}: MonthViewProps) {
  const today = new Date();
  const monthStart = startOfMonth(selectedDate);
  const monthEnd = endOfMonth(selectedDate);
  const calStart = startOfWeek(monthStart);
  const calEnd = endOfWeek(monthEnd);
  const days = eachDayOfInterval({ start: calStart, end: calEnd });

  const choreMap = useMemo(
    () => getChoresForRange(chores, calStart, calEnd),
    [chores, calStart.getTime(), calEnd.getTime()]
  );

  // Build weeks (rows of 7)
  const weeks: Date[][] = [];
  for (let i = 0; i < days.length; i += 7) {
    weeks.push(days.slice(i, i + 7));
  }

  return (
    <div className="month-view">
      <div className="month-day-headers">
        {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map(
          (d) => (
            <div key={d} className="month-day-header">
              {d}
            </div>
          )
        )}
      </div>

      <div className="month-grid" style={{ gridTemplateRows: `repeat(${weeks.length}, 1fr)` }}>
        {weeks.map((week) =>
          week.map((day) => {
            const dateStr = format(day, 'yyyy-MM-dd');
            const dayChores = choreMap.get(dateStr) || [];
            const isCurrentMonth = isSameMonth(day, selectedDate);
            const isToday = isSameDay(day, today);

            return (
              <div
                key={dateStr}
                className={`month-cell ${!isCurrentMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}`}
                onClick={() => onClickDate(day)}
              >
                <div className={`month-cell-date ${isToday ? 'today-circle' : ''}`}>
                  {format(day, 'd')}
                </div>
                <div className="month-cell-chores">
                  {dayChores.slice(0, MAX_VISIBLE).map((chore) => (
                    <ChoreCard
                      key={chore.id}
                      chore={chore}
                      dateStr={dateStr}
                      compact
                      onToggleComplete={onToggleComplete}
                      onClick={onClickChore}
                    />
                  ))}
                  {dayChores.length > MAX_VISIBLE && (
                    <div className="more-chores">
                      +{dayChores.length - MAX_VISIBLE} more
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
