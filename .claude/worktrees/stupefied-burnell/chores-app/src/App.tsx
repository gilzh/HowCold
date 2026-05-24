import { useState, useCallback } from 'react';
import { format } from 'date-fns';
import type { CalendarView, Chore } from './types';
import { useChores } from './hooks/useChores';
import { Sidebar } from './components/Sidebar';
import { CalendarHeader } from './components/CalendarHeader';
import { MonthView } from './components/MonthView';
import { WeekView } from './components/WeekView';
import { DayView } from './components/DayView';
import { ChoreModal } from './components/ChoreModal';

export function App() {
  const { chores, addChore, updateChore, deleteChore, toggleComplete } =
    useChores();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [view, setView] = useState<CalendarView>('month');
  const [modal, setModal] = useState<{
    open: boolean;
    chore: Chore | null;
    defaultDate: string;
  }>({ open: false, chore: null, defaultDate: '' });

  const openNewChore = useCallback(
    (date?: Date) => {
      setModal({
        open: true,
        chore: null,
        defaultDate: format(date ?? selectedDate, 'yyyy-MM-dd'),
      });
    },
    [selectedDate]
  );

  const openEditChore = useCallback((chore: Chore) => {
    setModal({ open: true, chore, defaultDate: chore.date });
  }, []);

  const closeModal = useCallback(() => {
    setModal({ open: false, chore: null, defaultDate: '' });
  }, []);

  const handleSave = useCallback(
    (data: Parameters<typeof addChore>[0]) => {
      if (modal.chore) {
        updateChore(modal.chore.id, data);
      } else {
        addChore(data);
      }
      closeModal();
    },
    [modal.chore, addChore, updateChore, closeModal]
  );

  const handleDelete = useCallback(() => {
    if (modal.chore) {
      deleteChore(modal.chore.id);
      closeModal();
    }
  }, [modal.chore, deleteChore, closeModal]);

  const handleClickDate = useCallback(
    (date: Date) => {
      if (view === 'month') {
        setSelectedDate(date);
        setView('day');
      } else {
        openNewChore(date);
      }
    },
    [view, openNewChore]
  );

  const viewProps = {
    selectedDate,
    chores,
    onToggleComplete: toggleComplete,
    onClickChore: openEditChore,
    onClickDate: handleClickDate,
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Office Chores</h1>
      </header>

      <div className="app-body">
        <Sidebar
          selectedDate={selectedDate}
          onSelectDate={(d) => setSelectedDate(d)}
          onNewChore={() => openNewChore()}
          onToday={() => setSelectedDate(new Date())}
        />

        <main className="calendar-main">
          <CalendarHeader
            view={view}
            selectedDate={selectedDate}
            onViewChange={setView}
            onDateChange={setSelectedDate}
          />

          <div className="calendar-body">
            {view === 'month' && <MonthView {...viewProps} />}
            {view === 'week' && <WeekView {...viewProps} />}
            {view === 'day' && <DayView {...viewProps} />}
          </div>
        </main>
      </div>

      {modal.open && (
        <ChoreModal
          chore={modal.chore}
          defaultDate={modal.defaultDate}
          onSave={handleSave}
          onDelete={modal.chore ? handleDelete : undefined}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
