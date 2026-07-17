const isDev = import.meta.env.DEV;

export const API_BASE_URL = isDev 
  ? 'http://127.0.0.1:8000/api/' 
  : '/api/'; // На продакшене используем относительный путь!

export const DJANGO_ADMIN_URL = isDev
  ? 'http://127.0.0.1:8000/admin'
  : '/admin';