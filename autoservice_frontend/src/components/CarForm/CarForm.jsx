import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../api/api';
import './CarForm.css';

function CarForm() {
    const navigate = useNavigate();
    const [models, setModels] = useState([]);
    const [formData, setFormData] = useState({
        car_model: '',
        vin: '',
        license_plate: '',
        current_mileage: 0,
        first_registration_date: ''
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        api.get('car-models/').then(res => setModels(res.data.results || res.data)).catch(console.error);
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload = {
                ...formData,
                car_model: parseInt(formData.car_model),
                current_mileage: parseInt(formData.current_mileage)
            };
            await api.post('cars/', payload);
            navigate('/');
        } catch (error) {
            console.error("Ошибка сохранения:", error);
            alert("Ошибка при сохранении автомобиля");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="form-container">
            <Link to="/" className="back-link">← Назад к списку</Link>
            <h1>Добавить новый автомобиль</h1>
            
            <form onSubmit={handleSubmit} className="modern-form">
                <div className="form-grid">
                    <div className="form-group">
                        <label>Модель автомобиля *</label>
                        <select name="car_model" value={formData.car_model} onChange={handleChange} required>
                            <option value="">Выберите модель...</option>
                            {models.map(m => (
                                <option key={m.id} value={m.id}>{m.make} {m.model} ({m.engine})</option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label>VIN номер *</label>
                        <input type="text" name="vin" value={formData.vin} onChange={handleChange} required maxLength="17" placeholder="17 символов" />
                    </div>

                    <div className="form-group">
                        <label>Государственный номер</label>
                        <input type="text" name="license_plate" value={formData.license_plate} onChange={handleChange} placeholder="А123БВ777" />
                    </div>

                    <div className="form-group">
                        <label>Текущий пробег (км) *</label>
                        <input type="number" name="current_mileage" value={formData.current_mileage} onChange={handleChange} required min="0" />
                    </div>

                    <div className="form-group">
                        <label>Дата первой регистрации</label>
                        <input type="date" name="first_registration_date" value={formData.first_registration_date} onChange={handleChange} />
                    </div>
                </div>

                <div className="form-actions">
                    <button type="button" className="btn-cancel" onClick={() => navigate('/')}>Отмена</button>
                    <button type="submit" className="btn-submit" disabled={loading}>
                        {loading ? 'Сохранение...' : 'Добавить автомобиль'}
                    </button>
                </div>
            </form>
        </div>
    );
}

export default CarForm;