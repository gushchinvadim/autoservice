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
import { useState } from 'react';
import './App.css';


function App() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
    const closeMenu = () => setIsMenuOpen(false);

    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                    path="/*"
                    element={
                        <ProtectedRoute>
                            <div className="app">
                                <nav className="navbar">
                                    <div className="nav-container">
                                        <Link to="/" className="nav-brand" onClick={closeMenu}>
                                            <span className="brand-icon">🔧</span>
                                            <span className="brand-text">АвтоСервис</span>
                                        </Link>

                                        {/* Кнопка-бургер (видна только на мобильных) */}
                                        <button 
                                            className={`burger-button ${isMenuOpen ? 'active' : ''}`}
                                            onClick={toggleMenu}
                                            aria-label="Меню"
                                        >
                                            <span></span>
                                            <span></span>
                                            <span></span>
                                        </button>

                                        {/* Меню */}
                                        <div className={`nav-menu ${isMenuOpen ? 'open' : ''}`}>
                                            <NavLink
                                                to="/"
                                                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                                                end
                                                onClick={closeMenu}
                                            >
                                                📊 Дашборд
                                            </NavLink>
                                            <NavLink
                                                to="/cars"
                                                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                                                onClick={closeMenu}
                                            >
                                                🚗 Автомобили
                                            </NavLink>
                                            <a 
                                                href={DJANGO_ADMIN_URL} 
                                                className="nav-link admin-link"
                                                onClick={closeMenu}
                                            >
                                                ⚙️ Админка
                                            </a>
                                            <LogoutButton onClick={closeMenu} />
                                        </div>
                                    </div>
                                </nav>

                                {/* Оверлей для закрытия меню при клике вне его */}
                                {isMenuOpen && (
                                    <div className="nav-overlay" onClick={closeMenu}></div>
                                )}

                                <main className="main-content">
                                    <Routes>
                                        <Route path="/" element={<Dashboard />} />
                                        <Route path="/cars" element={<CarList />} />
                                        <Route path="/cars/add" element={<CarForm />} />
                                        <Route path="/cars/:id" element={<CarDetails />} />
                                        <Route path="/cars/:id/add-record" element={<MaintenanceRecordForm />} />
                                    </Routes>
                                </main>
                                {/* Нижняя навигация для мобильных */}
                                <div className="bottom-nav">
                                    <NavLink 
                                        to="/" 
                                        className={({ isActive }) => `bottom-nav-item ${isActive ? 'active' : ''}`} 
                                        end 
                                        onClick={closeMenu}
                                    >
                                        <span className="bottom-nav-icon">📊</span>
                                        <span className="bottom-nav-text">Главная</span>
                                    </NavLink>
                                    <NavLink 
                                        to="/cars" 
                                        className={({ isActive }) => `bottom-nav-item ${isActive ? 'active' : ''}`} 
                                        onClick={closeMenu}
                                    >
                                        <span className="bottom-nav-icon">🚗</span>
                                        <span className="bottom-nav-text">Авто</span>
                                    </NavLink>
                                    <a href={DJANGO_ADMIN_URL} className="bottom-nav-item">
                                        <span className="bottom-nav-icon">⚙️</span>
                                        <span className="bottom-nav-text">Админ</span>
                                    </a>
                                </div>
                            </div>
                        </ProtectedRoute>
                    }
                />
            </Routes>
        </Router>
    );
}

export default App;