import {
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  format,
  isSameDay,
} from 'date-fns';
import { useMemo } from 'react';
import type { Chore } from '../types';
import { getChoresForRange } from '../utils/recurrence';
import { ChoreCard } from './ChoreCard';

interface WeekViewProps {
  selectedDate: Date;
  chores: Chore[];
  onToggleComplete: (id: string, dateStr: string) => void;
  onClickChore: (chore: Chore) => void;
  onClickDate: (date: Date) => void;
}

export function WeekView({
  selectedDate,
  chores,
  onToggleComplete,
  onClickChore,
  onClickDate,
}: WeekViewProps) {
  const today = new Date();
  const weekStart = startOfWeek(selectedDate);
  const weekEnd = endOfWeek(selectedDate);
  const days = eachDayOfInterval({ start: weekStart, end: weekEnd });

  const choreMap = useMemo(
    () => getChoresForRange(chores, weekStart, weekEnd),
    [chores, weekStart.getTime(), weekEnd.getTime()]
  );

  return (
    <div className="week-view">
      <div className="week-grid">
        {days.map((day) => {
          const dateStr = format(day, 'yyyy-MM-dd');
          const dayChores = choreMap.get(dateStr) || [];
          const isToday = isSameDay(day, today);

          return (
            <div
              key={dateStr}
              className={`week-column ${isToday ? 'today' : ''}`}
              onClick={() => onClickDate(day)}
            >
              <div className="week-column-header">
                <span className="week-day-name">{format(day, 'EEE')}</span>
                <span className={`week-day-number ${isToday ? 'today-circle' : ''}`}>
                  {format(day, 'd')}
                </span>
              </div>
              <div className="week-column-body">
                {dayChores.map((chore) => (
                  <ChoreCard
                    key={chore.id}
                    chore={chore}
                    dateStr={dateStr}
                    onToggleComplete={onToggleComplete}
                    onClick={onClickChore}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
