# LiverWatch

LiverWatch is a Flask-based automated medical web app that collects real-time information about biliary cirrhosis and biliary atresia from across the web. The system uses web scraping to gather data on disease causes, symptoms, recovery rates, death statistics, and surgical procedures at different stages. The extracted posts are stored in a database and displayed in a responsive, scrollable blog format.

## Focus on Uganda

This system is specifically focused on Uganda, where biliary cirrhosis and biliary atresia are not well-known diseases. LiverWatch aims to raise awareness and provide valuable information to the Ugandan population about these liver diseases. By collecting and displaying real-time information, the system helps educate the public and healthcare professionals about the causes, symptoms, and treatments of these conditions.

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

8. **Community Forum & Q&A**:
   - Users can ask and answer liver health-related questions.
   - Store discussions in PostgreSQL/MySQL.
   - Use Vanilla JS for interactive UI.

9. **Liver Health Tracker**:
   - Allow users to log habits (alcohol, diet, exercise) and visualize trends using Chart.js.
   - Store logs in PostgreSQL/MySQL.

10. **Diet & Recipe Suggestions**:
    - Provide liver-friendly foods and meal ideas, searchable by ingredient or meal type.
    - Update weekly.

11. **Medical Appointment Finder**:
    - Use Google Maps API to find liver specialists nearby.
    - Filter by distance, rating, and availability.

12. **Liver Disease News Feed**:
    - Fetch and display real-time liver health updates from WHO/CDC APIs in a scrollable, card-based UI.

13. **Child Health Section**:
    - Detailed signs and symptoms for newborns, infants, and toddlers.
    - Includes treatments and procedures for each.

## Tech Stack

- **Backend**: Flask + Flask-SQLAlchemy (or Flask-PyMongo)
- **Scraping**: BeautifulSoup/Scrapy/Selenium + NLP for filtering
- **Frontend**: Flask-Jinja2 Templates + Vanilla JS + CSS
- **Database**: PostgreSQL/MySQL/MongoDB
- **Caching**: Redis (optional for performance)
- **Email Alerts**: Flask-Mail / SendGrid API

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/LiverWatch.git
   cd LiverWatch
   ```

2. Create a virtual environment and activate it:
   ```sh
   python -m venv env
   source env/bin/activate  # On Windows, use `env\Scripts\activate`
   ```

3. Install the dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Set environment variables for `SECRET_KEY`, `MAIL` settings, and `DATABASE_URL`.

5. Run the Flask app:
   ```sh
   python app.py
   ```

## Usage

- Visit the home page to see the latest posts.
- Subscribe to the newsletter to receive email alerts for new posts.
- Admins can log in to manage posts.
- Use the forum to ask and answer liver health-related questions.
- Log daily habits in the health tracker and visualize trends.
- Find liver-friendly diet and recipe suggestions.
- Search for nearby liver specialists using the appointment finder.
- Stay updated with the latest liver health news.
- Learn about signs, symptoms, treatments, and procedures for newborns, infants, and toddlers in the child health section.

## Contributing

Contributions are currently not welcome.

## Badges

![WHO](https://img.shields.io/badge/WHO-World%20Health%20Organization-blue)
![CDC](https://img.shields.io/badge/CDC-Centers%20for%20Disease%20Control%20and%20Prevention-blue)
![NIH](https://img.shields.io/badge/NIH-National%20Institutes%20of%20Health-blue)
![Liver Foundation](https://img.shields.io/badge/Liver%20Foundation-American%20Liver%20Foundation-blue)
![Hepatitis B Foundation](https://img.shields.io/badge/Hepatitis%20B%20Foundation-Hepatitis%20B%20Foundation-blue)

## Legal Notice

© Kweezi Perez Christopher. All rights reserved. Unauthorized use of this project without express permission from the owner is strictly prohibited and will result in legal action.
