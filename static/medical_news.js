document.addEventListener('DOMContentLoaded', function() {
    function fetchNews() {
        const newsCards = document.getElementById('news-cards');
        const loadingIndicator = document.getElementById('loading-indicator');
        loadingIndicator.style.display = 'block'; // Show loading indicator

        // Add a fallback if fetch fails completely
        const fallbackNews = [
            {
                id: 0,
                title: 'Understanding Liver Disease Prevention',
                description: 'Learn about the latest research on preventing liver disease through lifestyle changes.',
                link: 'https://www.liverfoundation.org/for-patients/about-the-liver/health-wellness/',
                source: 'liverfoundation.org'
            },
            {
                id: 1,
                title: 'Nutrition for Liver Health',
                description: 'Discover the best foods and dietary patterns to maintain optimal liver function.',
                link: 'https://www.hopkinsmedicine.org/health/conditions-and-diseases/liver-health',
                source: 'hopkinsmedicine.org'
            },
            {
                id: 2,
                title: 'New Treatments for Liver Disease',
                description: 'Recent advances in medical treatments for various liver conditions.',
                link: 'https://www.mayoclinic.org/diseases-conditions/liver-problems/diagnosis-treatment/drc-20374502',
                source: 'mayoclinic.org'
            }
        ];

        // Add console logging for debugging
        console.log('Fetching news from API...');

        fetch('/api/medical_news')
            .then(response => {
                console.log('API response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('News data received:', data);
                newsCards.innerHTML = ''; // Clear existing news cards
                
                // Check if data.news exists and has items
                if (data && data.news && data.news.length > 0) {
                    data.news.forEach((news, index) => {
                        const newsCard = document.createElement('div');
                        newsCard.className = 'news-card';
                        newsCard.innerHTML = `
                            <h3>${news.title || 'No Title Available'}</h3>
                            <p>${news.description || 'No description available'}</p>
                            <div class="news-source">Source: ${news.source || 'Unknown'}</div>
                            <a href="${news.link}" target="_blank" class="read-more-btn">Read more</a>
                        `;
                        newsCards.appendChild(newsCard);
                    });
                } else {
                    console.warn('No news items found in API response, using fallback');
                    displayFallbackNews();
                }
                loadingIndicator.style.display = 'none'; // Hide loading indicator
            })
            .catch(error => {
                console.error('Error fetching news:', error);
                loadingIndicator.style.display = 'none'; // Hide loading indicator
                displayFallbackNews();
            });

        function displayFallbackNews() {
            newsCards.innerHTML = '<div class="error-message">Could not load news from our sources. Showing some general liver health information:</div>';
            fallbackNews.forEach(news => {
                const newsCard = document.createElement('div');
                newsCard.className = 'news-card';
                newsCard.innerHTML = `
                    <h3>${news.title}</h3>
                    <p>${news.description}</p>
                    <div class="news-source">Source: ${news.source}</div>
                    <a href="${news.link}" target="_blank" class="read-more-btn">Read more</a>
                `;
                newsCards.appendChild(newsCard);
            });
        }
    }

    // Fetch news initially and then every 5 minutes
    fetchNews();
    setInterval(fetchNews, 300000); // 300000 ms = 5 minutes
});
