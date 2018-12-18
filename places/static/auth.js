const togglePassword = document.getElementById('toggle-password');

function showOrHidePassword() {
    password.type = (password.type === 'password') ? 'text' : 'password';
}

togglePassword.addEventListener('change', showOrHidePassword);
