import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../api/api';
import './Dashboard.css';

function Dashboard() {
    const [stats, setStats] = useState({
        totalCars: 0,
        upcomingMaintenance: 0,
        overdueMaintenance: 0,
        totalSpentThisMonth: 0
    });
    const [recentRecords, setRecentRecords] = useState([]);

    const [overdueCars, setOverdueCars] = useState([]); // <-- Явно объявляем состояние
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            setLoading(true);
            const [carsRes, recordsRes] = await Promise.all([
                api.get('cars/'),
                api.get('records/')
            ]);

            const cars = carsRes.data.results || carsRes.data;
            const records = recordsRes.data.results || recordsRes.data;

            // Считаем общую сумму за текущий месяц
            const now = new Date();
            const thisMonthRecords = records.filter(r => {
                const recordDate = new Date(r.date_performed);
                return recordDate.getMonth() === now.getMonth() && 
                       recordDate.getFullYear() === now.getFullYear();
            });
            
            const totalSpent = thisMonthRecords.reduce((sum, r) => sum + (parseFloat(r.cost) || 0), 0);

            // Анализ предстоящих и просроченных ТО
            const upcoming = [];
            const overdue = []; // <-- ЯВНО ОБЪЯВЛЯЕМ ПЕРЕД ЦИКЛОМ

            for (const car of cars) {
                try {
                    const forecast = await api.get(`cars/${car.id}/forecast/`);
                    if (forecast.data.tasks && forecast.data.tasks.length > 0) {
                        const firstTask = forecast.data.tasks[0];
                        if (firstTask.km_left < 0) {
                            overdue.push({
                                id: car.id,
                                carInfo: car,
                                kmOverdue: Math.abs(firstTask.km_left),
                                nextToName: forecast.data.next_to_name
                            });
                        } else if (firstTask.km_left <= 5000) {
                            upcoming.push({
                                id: car.id,
                                carInfo: car,
                                kmLeft: firstTask.km_left,
                                nextToName: forecast.data.next_to_name
                            });
                        }
                    }
                } catch (err) {
                    // Игнорируем ошибки прогноза для отдельных машин (например, если нет цикла ТО)
                    // Это предотвращает падение всего дашборда
                    console.warn(`Прогноз для авто ${car.id} недоступен:`, err.message);
                }
            }

            setStats({
                totalCars: cars.length,
                upcomingMaintenance: upcoming.length,
                overdueMaintenance: overdue.length,
                totalSpentThisMonth: totalSpent
            });

            setUpcomingCars(upcoming);
            setOverdueCars(overdue); // <-- Сохраняем в состояние

            // Последние 5 записей о ТО
            const sortedRecords = records
                .sort((a, b) => new Date(b.date_performed) - new Date(a.date_performed))
                .slice(0, 5);
            
            const recordsWithCars = sortedRecords.map(record => {
                const car = cars.find(c => c.id === record.car);
                return { ...record, carInfo: car };
            });
            
            setRecentRecords(recordsWithCars);

        } catch (error) {
            console.error("Критическая ошибка загрузки данных дашборда:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="dashboard-loading">
                <div className="spinner"></div>
                <p>Загрузка дашборда...</p>
            </div>
        );
    }

    return (
        <div className="dashboard">
            <h1>📊 Панель управления</h1>

            {/* Карточки статистики */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon">🚗</div>
                    <div className="stat-content">
                        <span className="stat-value">{stats.totalCars}</span>
                        <span className="stat-label">Автомобилей в парке</span>
                    </div>
                </div>

                <div className="stat-card warning">
                    <div className="stat-icon">⚠️</div>
                    <div className="stat-content">
                        <span className="stat-value">{stats.overdueMaintenance}</span>
                        <span className="stat-label">Просрочено ТО</span>
                    </div>
                </div>

                <div className="stat-card info">
                    <div className="stat-icon">🔜</div>
                    <div className="stat-content">
                        <span className="stat-value">{stats.upcomingMaintenance}</span>
                        <span className="stat-label">ТО в ближайшие 5000 км</span>
                    </div>
                </div>

                <div className="stat-card success">
                    <div className="stat-icon">💰</div>
                    <div className="stat-content">
                        <span className="stat-value">{stats.totalSpentThisMonth.toLocaleString('ru-RU')} ₽</span>
                        <span className="stat-label">Расходы в этом месяце</span>
                    </div>
                </div>
            </div>

            {/* Просроченные ТО */}
            {overdueCars.length > 0 && (
                <div className="dashboard-section">
                    <h2>⚠️ Требуют срочного внимания</h2>
                    <div className="alert-list">
                        {overdueCars.map(car => (
                            <div key={car.id} className="alert-item">
                                <div className="alert-car">
                                    <strong>{car.carInfo?.car_model_name || `Авто #${car.id}`}</strong>
                                    <span className="alert-vin">{car.carInfo?.vin}</span>
                                </div>
                                <div className="alert-info">
                                    <span className="alert-badge overdue">Просрочено на {car.kmOverdue.toLocaleString('ru-RU')} км</span>
                                    <span className="alert-to">{car.nextToName}</span>
                                </div>
                                <Link to={`/cars/${car.id}`} className="btn-small">Перейти →</Link>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Последние записи о ТО */}
            <div className="dashboard-section">
                <h2>📝 Последние записи о ТО</h2>
                {recentRecords.length === 0 ? (
                    <p className="empty-message">Записей о ТО пока нет</p>
                ) : (
                    <div className="recent-records">
                        {recentRecords.map(record => (
                            <div key={record.id} className="record-card">
                                <div className="record-header">
                                    <span className="record-car">
                                        {record.carInfo?.car_model_name || `Авто #${record.car}`}
                                    </span>
                                    <span className="record-date">
                                        {new Date(record.date_performed).toLocaleDateString('ru-RU')}
                                    </span>
                                </div>
                                <div className="record-details">
                                    <span className="record-mileage">{record.mileage_at_service.toLocaleString('ru-RU')} км</span>
                                    <span className="record-cost">{record.cost?.toLocaleString('ru-RU')} ₽</span>
                                </div>
                                <Link to={`/cars/${record.car}`} className="record-link">
                                    Подробнее
                                </Link>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default Dashboard;