import { useState, useEffect, useCallback } from 'react';
import { nanoid } from 'nanoid';
import type { Chore, RecurrenceRule } from '../types';

const STORAGE_KEY = 'chores-app-data';

function loadChores(): Chore[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveChores(chores: Chore[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(chores));
}

export function useChores() {
  const [chores, setChores] = useState<Chore[]>(loadChores);

  useEffect(() => {
    saveChores(chores);
  }, [chores]);

  const addChore = useCallback(
    (data: {
      title: string;
      description: string;
      date: string;
      color: string;
      recurrence: RecurrenceRule | null;
    }) => {
      const chore: Chore = {
        id: nanoid(),
        ...data,
        completed: {},
      };
      setChores((prev) => [...prev, chore]);
      return chore;
    },
    []
  );

  const updateChore = useCallback(
    (
      id: string,
      data: Partial<Omit<Chore, 'id' | 'completed'>>
    ) => {
      setChores((prev) =>
        prev.map((c) => (c.id === id ? { ...c, ...data } : c))
      );
    },
    []
  );

  const deleteChore = useCallback((id: string) => {
    setChores((prev) => prev.filter((c) => c.id !== id));
  }, []);

  const toggleComplete = useCallback((id: string, dateStr: string) => {
    setChores((prev) =>
      prev.map((c) => {
        if (c.id !== id) return c;
        const completed = { ...c.completed };
        completed[dateStr] = !completed[dateStr];
        return { ...c, completed };
      })
    );
  }, []);

  return { chores, addChore, updateChore, deleteChore, toggleComplete };
}
