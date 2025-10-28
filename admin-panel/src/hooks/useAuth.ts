import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export const useAuth = () => {
    const navigate = useNavigate();

    // Check authentication on component mount
    useEffect(() => {
        const isLoggedIn = localStorage.getItem('isLoggedIn');
        const userId = localStorage.getItem('userId');
        if (!isLoggedIn || isLoggedIn !== 'true' || !userId) {
            navigate('/login');
        }
    }, [navigate]);

    const logout = () => {
        localStorage.clear();
        navigate('/login');
    };

    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true' && !!localStorage.getItem('userId');

    return {
        isLoggedIn,
        logout
    };
};