import { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../../api/api';
import './MaintenanceRecordForm.css';

function MaintenanceRecordForm() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [car, setCar] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [parts, setParts] = useState([]);
    const [loading, setLoading] = useState(true);

    const { register, control, handleSubmit, watch, setValue, getValues } = useForm({
        defaultValues: {
            date_performed: new Date().toISOString().split('T')[0],
            mileage_at_service: 0,
            labor_cost: 0,
            notes: '',
            performed_tasks: [],
            used_parts: []
        }
    });

    const { fields, append, remove } = useFieldArray({
        control,
        name: "used_parts"
    });

    const watchedParts = watch("used_parts");
    const watchedLabor = watch("labor_cost") || 0;

    // Расчет итогов в реальном времени
    const partsTotal = watchedParts?.reduce((sum, item) => {
        const qty = parseFloat(item.quantity) || 0;
        const price = parseFloat(item.unit_price) || 0;
        return sum + (qty * price);
    }, 0) || 0;

    const grandTotal = partsTotal + parseFloat(watchedLabor);

    useEffect(() => {
        const loadData = async () => {
            try {
                setLoading(true);
                
                const [carRes, tasksRes, partsRes] = await Promise.all([
                    api.get(`cars/${id}/`),
                    api.get('tasks/'),
                    api.get('spareparts/') // ← Теперь этот адрес точно существует!
                ]);
                
                setCar(carRes.data);
                setTasks(tasksRes.data.results || tasksRes.data); 
                setParts(partsRes.data.results || partsRes.data);
                
                setValue('mileage_at_service', carRes.data.current_mileage || 0);
            } catch (error) {
                console.error("Критическая ошибка загрузки данных для формы:", error);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [id, setValue]);

    const onPartChange = (index, partId) => {
        const selectedPart = parts.find(p => p.id === parseInt(partId));
        if (selectedPart) {
            setValue(`used_parts.${index}.unit_price`, selectedPart.current_price);
            setValue(`used_parts.${index}.quantity`, 1);
        }
    };

    const onSubmit = async (data) => {
        try {
            const payload = {
                car: parseInt(id),
                date_performed: data.date_performed,
                mileage_at_service: parseInt(data.mileage_at_service),
                labor_cost: parseFloat(data.labor_cost) || 0,
                notes: data.notes,
                performed_tasks: data.performed_tasks.map(Number),
                used_parts: data.used_parts.map(p => ({
                    part: parseInt(p.part),
                    quantity: parseFloat(p.quantity),
                    unit_price: parseFloat(p.unit_price)
                }))
            };

            await api.post('records/', payload);
            alert('Запись о ТО успешно сохранена!');
            navigate(`/cars/${id}`);
        } catch (error) {
            console.error("Ошибка сохранения:", error.response?.data || error);
            alert('Ошибка при сохранении. Проверьте консоль.');
        }
    };

    if (loading) return <div className="loading"><div className="spinner"></div><p>Загрузка...</p></div>;

    return (
        <div className="record-form-container">
            <Link to={`/cars/${id}`} className="back-link">← Назад к автомобилю</Link>
            <h1>Новая запись о ТО: {car.car_model_name}</h1>

            <form onSubmit={handleSubmit(onSubmit)} className="record-form">
                {/* Основная информация */}
                <div className="form-section">
                    <h2>Основная информация</h2>
                    <div className="form-grid">
                        <div className="form-group">
                            <label>Дата проведения</label>
                            <input type="date" {...register("date_performed")} required />
                        </div>
                        <div className="form-group">
                            <label>Пробег на момент ТО (км)</label>
                            <input type="number" {...register("mileage_at_service", { valueAsNumber: true })} required />
                        </div>
                        <div className="form-group">
                            <label>Стоимость работ (₽)</label>
                            <input type="number" step="0.01" {...register("labor_cost", { valueAsNumber: true })} placeholder="0" />
                        </div>
                    </div>
                    <div className="form-group full-width">
                        <label>Примечания</label>
                        <textarea {...register("notes")} rows="3" placeholder="Например: заменено по гарантии, есть люфт..." />
                    </div>
                </div>

                {/* Выбор задач */}
                <div className="form-section">
                    <h2>Выполненные работы</h2>
                    <div className="tasks-grid">
                        {tasks.map(task => (
                            <label key={task.id} className="task-checkbox">
                                <input 
                                    type="checkbox" 
                                    value={task.id} 
                                    {...register("performed_tasks")} 
                                />
                                <span>{task.name} <small>({task.interval_km} км)</small></span>
                            </label>
                        ))}
                    </div>
                </div>

                {/* Используемые запчасти */}
                <div className="form-section">
                    <div className="section-header">
                        <h2>Использованные запчасти</h2>
                        <button type="button" className="btn-add" onClick={() => append({ part: '', quantity: 1, unit_price: 0 })}>
                            + Добавить запчасть
                        </button>
                    </div>
                    
                    <div className="parts-list">
                        {fields.map((field, index) => (
                            <div key={field.id} className="part-row">
                                <select 
                                    {...register(`used_parts.${index}.part`)} 
                                    onChange={(e) => onPartChange(index, e.target.value)}
                                    required
                                >
                                    <option value="">Выберите запчасть</option>
                                    {parts.map(p => (
                                        <option key={p.id} value={p.id}>{p.name} ({p.manufacturer})</option>
                                    ))}
                                </select>
                                
                                <input 
                                    type="number" 
                                    step="0.1" 
                                    placeholder="Кол-во" 
                                    {...register(`used_parts.${index}.quantity`, { valueAsNumber: true })} 
                                    required 
                                />
                                
                                <input 
                                    type="number" 
                                    step="0.01" 
                                    placeholder="Цена за ед." 
                                    {...register(`used_parts.${index}.unit_price`, { valueAsNumber: true })} 
                                    required 
                                />
                                
                                <span className="row-total">
                                    {((watchedParts[index]?.quantity || 0) * (watchedParts[index]?.unit_price || 0)).toFixed(2)} ₽
                                </span>
                                
                                <button type="button" className="btn-remove" onClick={() => remove(index)}>×</button>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Итоги */}
                <div className="form-summary">
                    <div className="summary-row">
                        <span>Стоимость запчастей:</span>
                        <span>{partsTotal.toLocaleString('ru-RU')} ₽</span>
                    </div>
                    <div className="summary-row">
                        <span>Стоимость работ:</span>
                        <span>{parseFloat(watchedLabor).toLocaleString('ru-RU')} ₽</span>
                    </div>
                    <div className="summary-row grand-total">
                        <span>ИТОГО:</span>
                        <span>{grandTotal.toLocaleString('ru-RU')} ₽</span>
                    </div>
                </div>

                <div className="form-actions">
                    <button type="button" className="btn-cancel" onClick={() => navigate(`/cars/${id}`)}>Отмена</button>
                    <button type="submit" className="btn-submit">Сохранить запись о ТО</button>
                </div>
            </form>
        </div>
    );
}

export default MaintenanceRecordForm;