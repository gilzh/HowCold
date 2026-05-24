# Chores App - Implementation Plan

## Overview
Office chores management app with an Outlook-like calendar interface. React + TypeScript, Vite, local storage, no backend.

## Tech Choices
- **Vite** for project scaffolding and bundling
- **React 18 + TypeScript**
- **date-fns** for date manipulation (lightweight, tree-shakeable)
- **nanoid** for generating unique IDs
- **No UI library** — custom CSS to match Outlook's look and feel

## Data Model

```ts
interface Chore {
  id: string;
  title: string;
  description?: string;
  date: string;           // ISO date string (YYYY-MM-DD) for the first occurrence
  color: string;          // category color for calendar display
  recurrence: RecurrenceRule | null;
  completed: Record<string, boolean>; // keyed by date string, tracks completion per occurrence
}

interface RecurrenceRule {
  frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly';
  endDate?: string;       // optional end date, otherwise infinite
}
```

## Architecture

```
src/
├── App.tsx                  # Main layout (sidebar + calendar)
├── main.tsx                 # Entry point
├── index.css                # Global styles + Outlook theme
├── types.ts                 # Chore, RecurrenceRule types
├── hooks/
│   └── useChores.ts         # CRUD + localStorage persistence + recurrence expansion
├── utils/
│   └── recurrence.ts        # Generate occurrences of recurring chores for a date range
├── components/
│   ├── Sidebar.tsx           # Mini month navigator + chore list/add button
│   ├── CalendarHeader.tsx    # View toggle (Day/Week/Month) + navigation arrows + current date
│   ├── MonthView.tsx         # 6-week grid calendar
│   ├── WeekView.tsx          # 7-column week grid
│   ├── DayView.tsx           # Single day detail view
│   ├── ChoreCard.tsx         # Small card rendered on calendar cells
│   ├── ChoreModal.tsx        # Add/edit chore modal form
│   └── MiniCalendar.tsx      # Small month calendar for sidebar navigation
```

## Key Implementation Details

### Storage (`useChores` hook)
- Stores array of `Chore` objects in `localStorage` under key `"chores"`
- Exposes: `chores`, `addChore()`, `updateChore()`, `deleteChore()`, `toggleComplete(choreId, date)`
- On mount, reads from localStorage; on change, writes back

### Recurrence expansion (`recurrence.ts`)
- `getOccurrences(chore, rangeStart, rangeEnd)` → returns array of dates where the chore appears
- For daily: every day in range
- For weekly: same weekday each week
- For biweekly: same weekday every 2 weeks
- For monthly: same day-of-month each month
- Calendar views call this to know which chores appear on which dates

### Calendar Views
- **MonthView**: 6-row × 7-column grid. Each cell shows the date number and up to ~3 chore cards, with a "+N more" overflow indicator.
- **WeekView**: 7-column grid (single row), each column is a day showing all chores for that day.
- **DayView**: Single column listing all chores for the selected day with full details.
- All views support clicking a chore to edit, and clicking an empty area to add a new chore on that date.

### Sidebar (Outlook-style)
- Mini calendar at the top for month navigation (click a date to jump to it)
- "New Chore" button
- Today button to jump back to current date

### Outlook-like Styling
- Blue header bar (#0078d4)
- Light gray background, white calendar cells
- Left sidebar with mini calendar
- Rounded chore cards with colored left border
- Hover states and subtle shadows
- Segmented control for Day/Week/Month toggle

## Implementation Order

1. **Scaffold** — `npm create vite`, install deps (date-fns, nanoid)
2. **Types + utils** — Data model and recurrence logic
3. **useChores hook** — CRUD + localStorage
4. **App layout** — Sidebar + main area shell with Outlook styling
5. **MiniCalendar + Sidebar** — Navigation
6. **MonthView** — Primary calendar view
7. **WeekView + DayView** — Additional views
8. **ChoreModal** — Add/edit/delete form with recurrence options
9. **ChoreCard** — Rendered in calendar cells with completion toggle
10. **Polish** — Responsive tweaks, transitions, final styling
