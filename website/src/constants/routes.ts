/**
 * Application Routes
 * Centralized route definitions to prevent spelling mistakes and provide type safety
 */

export const Route = {
  home: '/',
  dashboard: {
    base: '/dashboard',
    settings: '/dashboard/settings',
    customize: '/dashboard/customize',
    calendars: '/dashboard/calendars',
    'create-assistant': '/dashboard/create-assistant',
  },
} as const;

// Type for valid dashboard sections (just the section name)
export type DashboardSection = 'settings' | 'customize' | 'calendars' | 'create-assistant';

// Array of valid dashboard sections for validation
export const validDashboardSections: DashboardSection[] = [
  'settings',
  'customize',
  'calendars',
  'create-assistant',
];

