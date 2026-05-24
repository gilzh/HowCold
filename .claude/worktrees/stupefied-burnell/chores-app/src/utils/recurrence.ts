import {
  addDays,
  addWeeks,
  addMonths,
  isBefore,
  isAfter,
  isSameDay,
  parseISO,
  format,
} from 'date-fns';
import type { Chore } from '../types';

/**
 * Returns all dates within [rangeStart, rangeEnd] where this chore occurs.
 */
export function getOccurrences(
  chore: Chore,
  rangeStart: Date,
  rangeEnd: Date
): string[] {
  const startDate = parseISO(chore.date);
  const endDate = chore.recurrence?.endDate
    ? parseISO(chore.recurrence.endDate)
    : null;

  if (!chore.recurrence) {
    // Non-recurring: just check if the single date falls in range
    if (
      (isSameDay(startDate, rangeStart) || isAfter(startDate, rangeStart)) &&
      (isSameDay(startDate, rangeEnd) || isBefore(startDate, rangeEnd))
    ) {
      return [chore.date];
    }
    return [];
  }

  const dates: string[] = [];
  let current = startDate;

  // Advance to a point near rangeStart to avoid iterating from the beginning
  while (isBefore(current, rangeStart) && !isSameDay(current, rangeStart)) {
    current = nextDate(current, chore.recurrence.frequency);
  }

  // Collect all occurrences within the range
  while (
    (isBefore(current, rangeEnd) || isSameDay(current, rangeEnd)) &&
    (!endDate || isBefore(current, endDate) || isSameDay(current, endDate))
  ) {
    if (isSameDay(current, rangeStart) || isAfter(current, rangeStart)) {
      dates.push(format(current, 'yyyy-MM-dd'));
    }
    current = nextDate(current, chore.recurrence.frequency);
  }

  return dates;
}

function nextDate(
  current: Date,
  frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly'
): Date {
  switch (frequency) {
    case 'daily':
      return addDays(current, 1);
    case 'weekly':
      return addWeeks(current, 1);
    case 'biweekly':
      return addWeeks(current, 2);
    case 'monthly':
      return addMonths(current, 1);
  }
}

/**
 * For a given date range, returns a map of dateString -> Chore[] for rendering.
 */
export function getChoresForRange(
  chores: Chore[],
  rangeStart: Date,
  rangeEnd: Date
): Map<string, Chore[]> {
  const map = new Map<string, Chore[]>();

  for (const chore of chores) {
    const dates = getOccurrences(chore, rangeStart, rangeEnd);
    for (const dateStr of dates) {
      const existing = map.get(dateStr) || [];
      existing.push(chore);
      map.set(dateStr, existing);
    }
  }

  return map;
}
