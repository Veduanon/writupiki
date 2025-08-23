async function checkAuth() {
    const token = localStorage.getItem('token');

    if (!token) {
        alert('You must be logged in.');
        window.location.href = '/login.html';
        return false;
    }

    try {
        const response = await fetch('/api/checkToken?token=' + token);

        console.log(response)

        if (response.ok) return true;

        localStorage.removeItem('token');
        alert('Session expired.');
        window.location.href = '/login.html';
        return false;
    } catch (error) {
        console.error('Auth error:', error);
        alert('Authentication failed.');
        window.location.href = '/login.html';
        return false;
    }
}