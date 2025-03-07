document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;

    // Function to set the theme
    function setTheme(theme) {
        if (theme === 'dark') {
            body.classList.add('dark-mode');
            themeToggle.classList.remove('fa-moon');
            themeToggle.classList.add('fa-sun');
        } else {
            body.classList.remove('dark-mode');
            themeToggle.classList.remove('fa-sun');
            themeToggle.classList.add('fa-moon');
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

function vote(type, id, action) {
    fetch(`/vote/${type}/${id}/${action}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error voting');
        }
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
