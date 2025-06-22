import { authConfig } from '../config/auth.config';
import { endpoints } from '../api/config';

class AuthService {
    initiateYandexAuth() {
        try {
            const { clientId, redirectUri, authUrl, scope } = authConfig.yandex;
            const scopeString = scope.join(' ');
            const state = Math.random().toString(36).substring(7);
            localStorage.setItem('oauth_state', state);
            
            const params = new URLSearchParams({
                response_type: 'code',
                client_id: clientId,
                redirect_uri: redirectUri,
                scope: scopeString,
                state: state,
                force_confirm: 'true',
                display: 'popup'
            });
            
            const url = `${authUrl}?${params.toString()}`;
            console.log('Redirecting to Yandex OAuth:', url);
            window.location.href = url;
        } catch (error) {
            console.error('Ошибка при инициализации авторизации:', error);
            throw error;
        }
    }

    async handleAuthCallback(code) {
        try {
            const state = localStorage.getItem('oauth_state');
            console.log('Отправка кода авторизации на сервер:', code, 'state:', state);
            
            const response = await fetch('http://localhost:8000/api/auth/yandex/callback/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ 
                    code: code,
                    state: state 
                }),
            });
            
            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    throw new Error(`Ошибка авторизации Яндекс: ${errorData.error || 'Неизвестная ошибка'}`);
                } else {
                    const errorText = await response.text();
                    console.error('Ответ сервера:', errorText);
                    throw new Error('Ошибка сервера при авторизации');
                }
            }

            const data = await response.json();
            console.log('Получены данные авторизации:', data);
            
            if (data.token) {
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(data.user));
                return data;
            }
            throw new Error('Токен не получен');
        } catch (error) {
            console.error('Ошибка при обработке авторизации:', error);
            throw error;
        }
    }

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('oauth_state');
    }

    getCurrentUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }

    isAuthenticated() {
        const token = localStorage.getItem('token');
        const user = this.getCurrentUser();
        return !!token && !!user;
    }
}

export default new AuthService(); 