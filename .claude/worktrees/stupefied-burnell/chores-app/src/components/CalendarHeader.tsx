import { format, addMonths, subMonths, addWeeks, subWeeks, addDays, subDays } from 'date-fns';
import type { CalendarView } from '../types';

interface CalendarHeaderProps {
  view: CalendarView;
  selectedDate: Date;
  onViewChange: (view: CalendarView) => void;
  onDateChange: (date: Date) => void;
}

export function CalendarHeader({
  view,
  selectedDate,
  onViewChange,
  onDateChange,
}: CalendarHeaderProps) {
  const navigate = (direction: 1 | -1) => {
    const fn = direction === 1
      ? view === 'month' ? addMonths : view === 'week' ? addWeeks : addDays
      : view === 'month' ? subMonths : view === 'week' ? subWeeks : subDays;
    onDateChange(fn(selectedDate, 1));
  };

  const getTitle = () => {
    switch (view) {
      case 'month':
        return format(selectedDate, 'MMMM yyyy');
      case 'week':
        return format(selectedDate, "'Week of' MMM d, yyyy");
      case 'day':
        return format(selectedDate, 'EEEE, MMMM d, yyyy');
    }
  };

  return (
    <div className="calendar-header">
      <div className="calendar-header-left">
        <button className="nav-btn" onClick={() => navigate(-1)}>
          &lsaquo;
        </button>
        <h2 className="calendar-title">{getTitle()}</h2>
        <button className="nav-btn" onClick={() => navigate(1)}>
          &rsaquo;
        </button>
      </div>

      <div className="view-toggle">
        {(['day', 'week', 'month'] as CalendarView[]).map((v) => (
          <button
            key={v}
            className={`view-toggle-btn ${view === v ? 'active' : ''}`}
            onClick={() => onViewChange(v)}
          >
            {v.charAt(0).toUpperCase() + v.slice(1)}
          </button>
        ))}
      </div>
    </div>
  );
}
