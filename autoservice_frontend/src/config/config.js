// autoservice_frontend/src/config/config.js

// Проверяем, запущен ли проект в режиме разработки (Vite)
const isDev = import.meta.env.DEV;

export const API_BASE_URL = isDev
  ? 'http://127.0.0.1:8000/api/'
  : (import.meta.env.VITE_API_BASE_URL || '/api/'); // На продакшене: относительный путь (рекомендуется) или полный URL

export const DJANGO_ADMIN_URL = isDev
  ? 'http://127.0.0.1:8000/admin'
  : (import.meta.env.VITE_DJANGO_ADMIN_URL || '/admin');