# LiverWatch

LiverWatch is a Flask-based automated medical web app that collects real-time information about biliary cirrhosis and biliary atresia from across the web. The system uses web scraping to gather data on disease causes, symptoms, recovery rates, death statistics, and surgical procedures at different stages. The extracted posts are stored in a database and displayed in a responsive, scrollable blog format.

## Features

1. **Automated Blog Post Generation**:
   - Each post includes a title, an image, a brief summary, full details, and metadata (date, source, and statistics).
   - Posts are displayed in a scrollable grid layout with square post cards.
   - Clicking a post opens a detailed view.
   - Posts include best practices for keeping the liver safe and healthy at different life stages.

2. **Real-Time Web Scraping & Storage**:
   - Uses BeautifulSoup to scrape relevant medical sources.
   - Filters and cleans the extracted data using NLP to ensure accuracy.
   - Stores posts in a PostgreSQL/MySQL/MongoDB database.

3. **User Interface (Frontend) Enhancements**:
   - Uses Flask with Jinja2 templates and Vanilla JS for interactive UI updates.
   - Minimalistic design with subtle blue and white as the main colors.
   - Clean, responsive, and aesthetically pleasing layout.

4. **Dark/Light Mode Toggle**:
   - A toggle button that switches between dark and light mode.
   - Stores user preferences in localStorage so the selected mode persists across sessions.

5. **Newsletter Subscription System**:
   - Users can subscribe with their email.
   - Subscribers receive real-time email alerts when new posts are added.
   - Uses Flask-Mail for email notifications.

6. **Security & Performance**:
   - Implements rate limiting (Flask-Limiter) to prevent scraping abuse.
   - Protects API endpoints using JWT authentication.
   - Optimizes performance using caching (Redis) for faster data retrieval.

7. **Optional Admin Dashboard**:
   - A backend panel where an admin can review, edit, or remove posts before publishing.

## Tech Stack

- **Backend**: Flask + Flask-SQLAlchemy (or Flask-PyMongo)
- **Scraping**: BeautifulSoup/Scrapy/Selenium + NLP for filtering
- **Frontend**: Flask-Jinja2 Templates + Vanilla JS + CSS
- **Database**: PostgreSQL/MySQL/MongoDB
- **Caching**: Redis (optional for performance)
- **Email Alerts**: Flask-Mail / SendGrid API

## Usage

- Visit the home page to see the latest posts.
- Subscribe to the newsletter to receive email alerts for new posts.
- Admins can log in to manage posts.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## Copyright ©️ 

This project is copyrighted .
