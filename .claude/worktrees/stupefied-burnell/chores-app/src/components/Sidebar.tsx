import { MiniCalendar } from './MiniCalendar';

interface SidebarProps {
  selectedDate: Date;
  onSelectDate: (date: Date) => void;
  onNewChore: () => void;
  onToday: () => void;
}

export function Sidebar({
  selectedDate,
  onSelectDate,
  onNewChore,
  onToday,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <button className="new-chore-btn" onClick={onNewChore}>
        + New Chore
      </button>

      <MiniCalendar selectedDate={selectedDate} onSelectDate={onSelectDate} />

      <button className="today-btn" onClick={onToday}>
        Today
      </button>
    </aside>
  );
}
