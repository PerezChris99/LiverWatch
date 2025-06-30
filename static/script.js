document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;

    // Function to set the theme
    function setTheme(theme) {
        if (theme === 'dark') {
            body.classList.add('dark-mode');
            themeToggle.textContent = 'Toggle Light Mode';
        } else {
            body.classList.remove('dark-mode');
            themeToggle.textContent = 'Toggle Dark Mode';
        }
        localStorage.setItem('theme', theme);
    }

    // Event listener for the theme toggle button
    themeToggle.addEventListener('click', function() {
        if (body.classList.contains('dark-mode')) {
            setTheme('light');
        } else {
            setTheme('dark');
        }
    });

    // Check for saved theme in localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    }
});
