import { BrowserRouter as Router, Routes, Route, NavLink, Link } from 'react-router-dom';
import CarList from './components/CarList/CarList';
import CarDetails from './components/CarDetails/CarDetails';
import MaintenanceRecordForm from './components/MaintenanceRecordForm/MaintenanceRecordForm';
import Dashboard from './components/Dashboard/Dashboard';
import CarForm from './components/CarForm/CarForm';
import Login from './components/Login/Login';
import ProtectedRoute from './components/ProtectedRoute/ProtectedRoute';
import LogoutButton from './components/LogoutButton/LogoutButton';
import { DJANGO_ADMIN_URL } from './config/config';
import './App.css';

function App() {
    const isLoggedIn = localStorage.getItem('access_token');

    return (
        <Router>
            <Routes>
                {/* Страница логина без навигации */}
                <Route path="/login" element={<Login />} />

                {/* Все остальные страницы защищены */}
                <Route
                    path="/*"
                    element={
                        <ProtectedRoute>
                            <div className="app">
                                <nav className="navbar">
                                    <div className="nav-container">
                                        <Link to="/" className="nav-brand">
                                            <span className="brand-icon">🔧</span>
                                            <span className="brand-text">АвтоСервис</span>
                                        </Link>

                                        <div className="nav-menu">
                                            <NavLink
                                                to="/"
                                                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                                                end
                                            >
                                                📊 Дашборд
                                            </NavLink>
                                            <NavLink
                                                to="/cars"
                                                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                                            >
                                                🚗 Автомобили
                                            </NavLink>
                                            <a href={DJANGO_ADMIN_URL} className="nav-link admin-link">
                                                ️ Админка
                                            </a>
                                            <LogoutButton />
                                        </div>
                                    </div>
                                </nav>

                                <main className="main-content">
                                    <Routes>
                                        <Route path="/" element={<Dashboard />} />
                                        <Route path="/cars" element={<CarList />} />
                                        <Route path="/cars/add" element={<CarForm />} />
                                        <Route path="/cars/:id" element={<CarDetails />} />
                                        <Route path="/cars/:id/add-record" element={<MaintenanceRecordForm />} />
                                    </Routes>
                                </main>
                            </div>
                        </ProtectedRoute>
                    }
                />
            </Routes>
        </Router>
    );
}

export default App;