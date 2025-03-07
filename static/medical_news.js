document.addEventListener('DOMContentLoaded', function() {
    function fetchNews() {
        const newsCards = document.getElementById('news-cards');
        const loadingIndicator = document.getElementById('loading-indicator');
        loadingIndicator.style.display = 'block'; // Show loading indicator

        fetch('/api/medical_news')
            .then(response => response.json())
            .then(data => {
                newsCards.innerHTML = ''; // Clear existing news cards
                data.news.forEach((news, index) => {
                    const newsCard = document.createElement('div');
                    newsCard.className = 'news-card';
                    newsCard.innerHTML = `
                        <h3>${news.title}</h3>
                        <p>${news.description}</p>
                        <a href="${news.link}" target="_blank">Read more</a>
                    `;
                    newsCards.appendChild(newsCard);
                });
                loadingIndicator.style.display = 'none'; // Hide loading indicator
            })
            .catch(error => {
                console.error('Error fetching news:', error);
                loadingIndicator.style.display = 'none'; // Hide loading indicator
            });
    }

    // Fetch news initially and then every 5 minutes
    fetchNews();
    setInterval(fetchNews, 300000); // 300000 ms = 5 minutes
});
