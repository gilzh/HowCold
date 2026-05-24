import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  format,
  isSameMonth,
  isSameDay,
  addMonths,
  subMonths,
} from 'date-fns';
import { useState } from 'react';

interface MiniCalendarProps {
  selectedDate: Date;
  onSelectDate: (date: Date) => void;
}

export function MiniCalendar({ selectedDate, onSelectDate }: MiniCalendarProps) {
  const [viewMonth, setViewMonth] = useState(startOfMonth(selectedDate));
  const today = new Date();

  const monthStart = startOfMonth(viewMonth);
  const monthEnd = endOfMonth(viewMonth);
  const calStart = startOfWeek(monthStart);
  const calEnd = endOfWeek(monthEnd);
  const days = eachDayOfInterval({ start: calStart, end: calEnd });

  return (
    <div className="mini-calendar">
      <div className="mini-calendar-header">
        <button
          className="mini-nav-btn"
          onClick={() => setViewMonth(subMonths(viewMonth, 1))}
        >
          &lsaquo;
        </button>
        <span className="mini-month-label">
          {format(viewMonth, 'MMMM yyyy')}
        </span>
        <button
          className="mini-nav-btn"
          onClick={() => setViewMonth(addMonths(viewMonth, 1))}
        >
          &rsaquo;
        </button>
      </div>

      <div className="mini-calendar-grid">
        {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map((d) => (
          <div key={d} className="mini-day-header">
            {d}
          </div>
        ))}
        {days.map((day) => {
          const isCurrentMonth = isSameMonth(day, viewMonth);
          const isSelected = isSameDay(day, selectedDate);
          const isToday = isSameDay(day, today);

          return (
            <button
              key={day.toISOString()}
              className={[
                'mini-day',
                !isCurrentMonth && 'other-month',
                isSelected && 'selected',
                isToday && 'today',
              ]
                .filter(Boolean)
                .join(' ')}
              onClick={() => onSelectDate(day)}
            >
              {format(day, 'd')}
            </button>
          );
        })}
      </div>
    </div>
  );
}
