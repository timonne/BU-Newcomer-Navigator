import type { AcademicCategory, Tag } from '../types';

export const CATEGORIES: AcademicCategory[] = [
  // Academic
  { id: 'btech', name: 'B.Tech', type: 'academic', subcategories: ['CSE', 'ECE', 'ME', 'CE', 'EE'] },
  { id: 'bca', name: 'BCA', type: 'academic' },
  { id: 'bsc', name: 'B.Sc', type: 'academic', subcategories: ['Physics', 'Chemistry', 'Mathematics'] },
  { id: 'bcom', name: 'B.Com', type: 'academic' },
  { id: 'bba', name: 'BBA', type: 'academic' },
  { id: 'mass-comm', name: 'Mass Communication', type: 'academic', subcategories: ['Journalism', 'Film & TV', 'Advertising'] },
  { id: 'mtech', name: 'M.Tech', type: 'academic', subcategories: ['CSE', 'ECE', 'ME'] },
  { id: 'mba', name: 'MBA', type: 'academic' },
  { id: 'mca', name: 'MCA', type: 'academic' },
  { id: 'msc', name: 'M.Sc', type: 'academic' },
  { id: 'phd', name: 'PhD', type: 'academic' },
  { id: 'law', name: 'LLB / Law', type: 'academic' },
  // Non-academic
  { id: 'hostel', name: 'Hostel', type: 'non-academic' },
  { id: 'campus-life', name: 'Campus Life', type: 'non-academic' },
  { id: 'sports', name: 'Sports', type: 'non-academic' },
  { id: 'clubs', name: 'Clubs & Societies', type: 'non-academic' },
  { id: 'events', name: 'Events', type: 'non-academic' },
  { id: 'transport', name: 'Transport', type: 'non-academic' },
  { id: 'food', name: 'Food & Cafeteria', type: 'non-academic' },
  { id: 'facilities', name: 'Facilities', type: 'non-academic' },
  { id: 'general', name: 'General', type: 'non-academic' },
];

export const TAGS: Tag[] = [
  { id: 'admission', name: 'Admission', color: '#1E3A8A' },
  { id: 'hostel', name: 'Hostel', color: '#7C3AED' },
  { id: 'fees', name: 'Fees', color: '#DC2626' },
  { id: 'library', name: 'Library', color: '#059669' },
  { id: 'placement', name: 'Placement', color: '#D97706' },
  { id: 'exam', name: 'Exam', color: '#DB2777' },
  { id: 'sports', name: 'Sports', color: '#0891B2' },
  { id: 'coding', name: 'Coding', color: '#4F46E5' },
  { id: 'clubs', name: 'Clubs', color: '#65A30D' },
  { id: 'wifi', name: 'Wi-Fi', color: '#EA580C' },
  { id: 'transport', name: 'Transport', color: '#0F766E' },
  { id: 'events', name: 'Events', color: '#9333EA' },
  { id: 'mess', name: 'Mess', color: '#B45309' },
  { id: 'scholarship', name: 'Scholarship', color: '#16A34A' },
  { id: 'internship', name: 'Internship', color: '#1D4ED8' },
  { id: 'faculty', name: 'Faculty', color: '#BE185D' },
];

export function getCategoryById(id: string): AcademicCategory | undefined {
  return CATEGORIES.find(c => c.id === id);
}

export function getTagById(id: string): Tag | undefined {
  return TAGS.find(t => t.id === id);
}
