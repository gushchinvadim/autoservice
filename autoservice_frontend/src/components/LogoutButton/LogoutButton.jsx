import { useNavigate } from 'react-router-dom';

function LogoutButton() {
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        navigate('/login');
    };

    return (
        <button onClick={handleLogout} className="nav-link logout-link" title="Выйти">
             Выйти
        </button>
    );
}

export default LogoutButton;