document.getElementById('toggle-password').addEventListener(
    'change',
    () => password.type = (password.type == 'password') ? 'text' : 'password'
);
