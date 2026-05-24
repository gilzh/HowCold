import { useState, useEffect } from 'react';
import type { Chore, RecurrenceRule } from '../types';
import { CHORE_COLORS } from '../types';

interface ChoreModalProps {
  chore: Chore | null; // null = creating new
  defaultDate: string;
  onSave: (data: {
    title: string;
    description: string;
    date: string;
    color: string;
    recurrence: RecurrenceRule | null;
  }) => void;
  onDelete?: () => void;
  onClose: () => void;
}

export function ChoreModal({
  chore,
  defaultDate,
  onSave,
  onDelete,
  onClose,
}: ChoreModalProps) {
  const [title, setTitle] = useState(chore?.title ?? '');
  const [description, setDescription] = useState(chore?.description ?? '');
  const [date, setDate] = useState(chore?.date ?? defaultDate);
  const [color, setColor] = useState(chore?.color ?? CHORE_COLORS[0]);
  const [isRecurring, setIsRecurring] = useState(!!chore?.recurrence);
  const [frequency, setFrequency] = useState<RecurrenceRule['frequency']>(
    chore?.recurrence?.frequency ?? 'weekly'
  );
  const [endDate, setEndDate] = useState(chore?.recurrence?.endDate ?? '');

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    onSave({
      title: title.trim(),
      description: description.trim(),
      date,
      color,
      recurrence: isRecurring
        ? { frequency, endDate: endDate || undefined }
        : null,
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header" style={{ backgroundColor: color }}>
          <h3>{chore ? 'Edit Chore' : 'New Chore'}</h3>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <form className="modal-body" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="chore-title">Title</label>
            <input
              id="chore-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Clean kitchen"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="chore-desc">Description</label>
            <textarea
              id="chore-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional details..."
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="chore-date">Date</label>
            <input
              id="chore-date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Color</label>
            <div className="color-picker">
              {CHORE_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  className={`color-swatch ${color === c ? 'selected' : ''}`}
                  style={{ backgroundColor: c }}
                  onClick={() => setColor(c)}
                />
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isRecurring}
                onChange={(e) => setIsRecurring(e.target.checked)}
              />
              Recurring chore
            </label>
          </div>

          {isRecurring && (
            <div className="recurrence-options">
              <div className="form-group">
                <label htmlFor="chore-freq">Frequency</label>
                <select
                  id="chore-freq"
                  value={frequency}
                  onChange={(e) =>
                    setFrequency(e.target.value as RecurrenceRule['frequency'])
                  }
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Biweekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="chore-end">End date (optional)</label>
                <input
                  id="chore-end"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>
          )}

          <div className="modal-actions">
            {chore && onDelete && (
              <button
                type="button"
                className="delete-btn"
                onClick={onDelete}
              >
                Delete
              </button>
            )}
            <div className="modal-actions-right">
              <button type="button" className="cancel-btn" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="save-btn">
                {chore ? 'Save' : 'Create'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
