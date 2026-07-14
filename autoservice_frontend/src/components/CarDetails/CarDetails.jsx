import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../../api/api';
import './CarDetails.css';

function CarDetails() {
    const { id } = useParams();
    const [car, setCar] = useState(null);
    const [forecast, setForecast] = useState(null);
    const [maintenanceHistory, setMaintenanceHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Сбрасываем состояние при переходе на другой автомобиль
        setCar(null);
        setForecast(null);
        setMaintenanceHistory([]);
        setLoading(true);
        setError(null);

        const loadCarData = async () => {
            try {
                // 1. Загружаем информацию об автомобиле
                const carResponse = await api.get(`cars/${id}/`);
                setCar(carResponse.data);
                
                // 2. Загружаем прогноз ТО
                try {
                    const forecastResponse = await api.get(`cars/${id}/forecast/`);
                    setForecast(forecastResponse.data);
                } catch (err) {
                    console.warn("Не удалось загрузить прогноз:", err);
                    setForecast(null);
                }
                
                // 3. Загружаем историю ТО
                try {
                    const historyResponse = await api.get(`records/?car=${id}`);
                    let historyData = historyResponse.data.results || historyResponse.data;
                    
                    // Сортируем историю: сначала самые свежие записи
                    historyData.sort((a, b) => new Date(b.date_performed) - new Date(a.date_performed));
                    setMaintenanceHistory(historyData);
                } catch (err) {
                    console.warn("Не удалось загрузить историю ТО:", err);
                    setMaintenanceHistory([]);
                }
                
                setError(null);
            } catch (err) {
                console.error("Ошибка загрузки данных:", err);
                setError('Не удалось загрузить данные автомобиля');
            } finally {
                setLoading(false);
            }
        };

        loadCarData();
    }, [id]);

    // Вспомогательная функция для формирования названия ТО (только как fallback)
    const getToName = (record) => {
        // Если есть пакет - используем его название
        if (record.package_name) {
            return record.package_name;
        }
        // Если пакета нет - рассчитываем по пробегу
        const toNumber = Math.round(record.mileage_at_service / 1000);
        return `ТО-${toNumber}`;
    };

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <p>Загрузка данных...</p>
            </div>
        );
    }

    if (error || !car) {
        return (
            <div className="error">
                <p>⚠️ {error || 'Автомобиль не найден'}</p>
                <Link to="/" className="back-link">← Назад к дашборду</Link>
            </div>
        );
    }

    return (
        <div className="car-details">
            <Link to="/" className="back-link">← Назад к дашборду</Link>
            
            <div className="car-header">
                <h1>{car.car_model_name || `Автомобиль #${id}`}</h1>
                <div className="car-meta">
                    <span className="vin">{car.vin}</span>
                    {car.license_plate && <span className="plate">{car.license_plate}</span>}
                </div>
            </div>

            <Link to={`/cars/${id}/add-record`} className="btn-add-record">
                <span className="btn-icon">+</span>
                Добавить запись о ТО
            </Link>

            <div className="car-info-section">
                <h2>Основная информация</h2>
                <div className="info-grid">
                    <div className="info-item">
                        <span className="label">Текущий пробег</span>
                        <span className="value">{car.current_mileage?.toLocaleString('ru-RU')} км</span>
                    </div>
                    <div className="info-item">
                        <span className="label">Дата регистрации</span>
                        <span className="value">{car.first_registration_date || '—'}</span>
                    </div>
                </div>
            </div>

            {forecast && (
                <div className="forecast-section">
                    <h2>🔮 Прогноз следующего ТО</h2>
                    
                    <div className="forecast-summary">
                        <div className="summary-card">
                            <span className="summary-label">Следующее ТО</span>
                            <span className="summary-value">{forecast.next_to_name || '—'}</span>
                        </div>
                        <div className="summary-card">
                            <span className="summary-label">Пробег</span>
                            <span className="summary-value">{forecast.next_to_position_km?.toLocaleString('ru-RU')} км</span>
                        </div>
                        <div className="summary-card">
                            <span className="summary-label">Осталось</span>
                            <span className="summary-value">{forecast.tasks?.[0]?.km_left?.toLocaleString('ru-RU') || '—'} км</span>
                        </div>
                    </div>

                    {forecast.tasks && forecast.tasks.length > 0 && (
                        <div className="tasks-section">
                            <h3>Запланированные работы</h3>
                            <ul className="tasks-list">
                                {forecast.tasks.map((task, index) => (
                                    <li key={index} className="task-item">
                                        <span className="task-name">{task.name}</span>
                                        <span className="task-system">{task.system}</span>
                                        {task.labor_cost > 0 && (
                                            <span className="task-cost">{task.labor_cost.toLocaleString('ru-RU')} ₽</span>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {forecast.shopping_list && forecast.shopping_list.length > 0 && (
                        <div className="parts-section">
                            <h3> Список запчастей</h3>
                            <table className="parts-table">
                                <thead>
                                    <tr>
                                        <th>Запчасть</th>
                                        <th>Кол-во</th>
                                        <th>Цена за ед.</th>
                                        <th>Итого</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {forecast.shopping_list.map((part, index) => (
                                        <tr key={index}>
                                            <td>{part.name}</td>
                                            <td>{part.quantity} {part.unit}</td>
                                            <td>{part.unit_price.toLocaleString('ru-RU')} ₽</td>
                                            <td className="total">{part.total_price.toLocaleString('ru-RU')} ₽</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    <div className="forecast-total">
                        <div className="total-row">
                            <span>Запчасти:</span>
                            <span>{forecast.total_parts_cost?.toLocaleString('ru-RU') || 0} ₽</span>
                        </div>
                        <div className="total-row">
                            <span>Работы:</span>
                            <span>{forecast.total_labor_cost?.toLocaleString('ru-RU') || 0} ₽</span>
                        </div>
                        <div className="total-row grand-total">
                            <span>Итого:</span>
                            <span>{forecast.total_forecast_cost?.toLocaleString('ru-RU') || 0} ₽</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Журнал ТО - Плоттер (Матрица замен) */}
            <div className="maintenance-history-section">
                <h2>📊 Плоттер замен (История обслуживания)</h2>
                
                {maintenanceHistory && maintenanceHistory.length > 0 ? (
                    <div className="plotter-wrapper">
                        <table className="plotter-table">
                            <thead>
                                <tr>
                                    <th className="sticky-col sticky-header">Элемент / Запчасть</th>
                                    {/* Сортируем ТО по возрастанию пробега (слева направо) */}
                                    {[...maintenanceHistory]
                                        .sort((a, b) => a.mileage_at_service - b.mileage_at_service)
                                        .map(record => (
                                            <th key={record.id} className="sticky-header">
                                                <div className="to-header-name">
                                                    {getToName(record)}
                                                </div>
                                                <div className="to-header-date">
                                                    {new Date(record.date_performed).toLocaleDateString('ru-RU')}
                                                </div>
                                            </th>
                                        ))}
                                </tr>
                            </thead>
                            <tbody>
                                {(() => {
                                    // 1. Собираем все уникальные названия запчастей и работ из всей истории
                                    const uniqueItems = new Set();
                                    maintenanceHistory.forEach(record => {
                                        if (record.used_parts_display) {
                                            record.used_parts_display.forEach(p => uniqueItems.add(`🔧 ${p.part_name}`));
                                        }
                                        if (record.tasks_display) {
                                            record.tasks_display.forEach(t => uniqueItems.add(`⚙️ ${t.name}`));
                                        }
                                    });

                                    // 2. Превращаем в отсортированный массив для строк
                                    const rows = Array.from(uniqueItems).sort();

                                    // 3. Отсортированная история для столбцов
                                    const sortedHistory = [...maintenanceHistory].sort(
                                        (a, b) => a.mileage_at_service - b.mileage_at_service
                                    );

                                    return rows.map(itemName => (
                                        <tr key={itemName}>
                                            <td className="sticky-col item-name-cell">{itemName}</td>
                                            {sortedHistory.map(record => {
                                                // Определяем тип элемента
                                                const isPart = itemName.startsWith('');
                                                const cleanName = itemName.substring(2).trim();
                                                
                                                // Приводим к нижнему регистру и убираем пробелы для надежного сравнения
                                                const cleanNameLower = cleanName.toLowerCase();
                                                
                                                // Ищем совпадение и в запчастях, и в работах (игнорируя регистр и пробелы)
                                                const wasChanged = 
                                                    record.used_parts_display?.some(p => p.part_name.toLowerCase().trim() === cleanNameLower) ||
                                                    record.tasks_display?.some(t => t.name.toLowerCase().trim() === cleanNameLower);

                                                return (
                                                    <td key={record.id} className={wasChanged ? 'changed-cell' : 'empty-cell'}>
                                                        {wasChanged ? new Date(record.date_performed).toLocaleDateString('ru-RU') : '—'}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    ));
                                })()}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="empty-history">
                        <p>История обслуживания пока пуста</p>
                        <Link to={`/cars/${id}/add-record`} className="btn-add-record">
                            <span className="btn-icon">+</span>
                            Добавить первую запись о ТО
                        </Link>
                    </div>
                )}
            </div>   
        </div>
    );
}

export default CarDetails;