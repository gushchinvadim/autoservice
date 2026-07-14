import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../api/api';
import './CarList.css';

function CarList() {
    const [cars, setCars] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadCars();
    }, []);

    const loadCars = async () => {
        try {
            setLoading(true);
            const response = await api.get('cars/');
            setCars(response.data);
            setError(null);
        } catch (err) {
            console.error("Ошибка загрузки автомобилей:", err);
            setError('Не удалось загрузить список автомобилей. Убедитесь, что бэкенд запущен.');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <p>Загрузка автомобилей...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="error">
                <p>⚠️ {error}</p>
                <button onClick={loadCars}>Попробовать снова</button>
            </div>
        );
    }

    return (
        <div className="car-list">

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
                <h1 style={{ margin: 0 }}>📝Автопарк</h1>
                <Link to="/cars/add" className="btn-add-record" style={{ marginTop: 0 }}>
                    <span className="btn-icon">✚</span> Добавить авто
                </Link>
            </div>
            <h1>🚗 Мои автомобили</h1>
            
            {cars.length === 0 ? (
                <div className="empty-state">
                    <p> Автомобили не найдены</p>
                    <p>Добавьте первый автомобиль через <a href="/admin" target="_blank" rel="noopener noreferrer">админку Django</a></p>
                </div>
            ) : (
                <div className="cars-grid">
                    {cars.map(car => (
                        <div key={car.id} className="car-card">
                            <div className="car-header">
                                <h3>{car.car_model_name || `Автомобиль #${car.id}`}</h3>
                                <span className="car-vin">{car.vin}</span>
                            </div>
                            
                            <div className="car-info">
                                <div className="info-row">
                                    <span className="label">Пробег:</span>
                                    <span className="value">{car.current_mileage?.toLocaleString('ru-RU')} км</span>
                                </div>
                                <div className="info-row">
                                    <span className="label">Гос. номер:</span>
                                    <span className="value">{car.license_plate || '—'}</span>
                                </div>
                                <div className="info-row">
                                    <span className="label">Последнее ТО:</span>
                                    <span className="value">{car.last_maintenance || 'Нет данных'}</span>
                                </div>
                            </div>
                            
                            <Link to={`/cars/${car.id}`} className="car-link">
                                Подробнее →
                            </Link>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default CarList;