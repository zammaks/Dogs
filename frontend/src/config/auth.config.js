export const authConfig = {
    yandex: {
        clientId: '5549c064b08e4a7b8be4f77568ac559a',
        authUrl: 'https://oauth.yandex.ru/authorize',
        redirectUri: 'http://localhost:8000/api/auth/yandex/callback/',
        scope: ['login:email', 'login:info', 'login:avatar'],
    }
}; 