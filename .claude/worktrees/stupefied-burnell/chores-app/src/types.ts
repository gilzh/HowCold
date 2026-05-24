export interface RecurrenceRule {
  frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly';
  endDate?: string;
}

export interface Chore {
  id: string;
  title: string;
  description: string;
  date: string; // ISO date YYYY-MM-DD — first occurrence
  color: string;
  recurrence: RecurrenceRule | null;
  completed: Record<string, boolean>; // keyed by YYYY-MM-DD
}

export type CalendarView = 'day' | 'week' | 'month';

export const CHORE_COLORS = [
  '#0078d4', // blue
  '#107c10', // green
  '#d83b01', // orange
  '#b4009e', // purple
  '#008272', // teal
  '#c239b3', // pink
  '#e3008c', // magenta
  '#986f0b', // gold
] as const;
