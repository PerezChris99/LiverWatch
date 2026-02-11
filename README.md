# 🏥 LiverWatch

<div align="center">

**Uganda's Premier Liver Health Awareness Platform**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![Google ADK](https://img.shields.io/badge/Google_ADK-1.24.1-orange.svg)](https://github.com/google/genai-adk)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Quality](https://img.shields.io/badge/Code_Quality-Production_Ready-brightgreen.svg)]()

---

### 🚀 Current Status - v2.0.0 (February 2026)

**✅ PRODUCTION READY:**
- ✨ **Complete code modernization** - Professional Flask blueprints architecture
- 🎨 **Clean codebase** - Zero inline styles/scripts, fully modular CSS/JS
- 🔐 **Production authentication** - Flask-Login with rate limiting and security features
- 🤖 **AI Agent System** - 5 specialized health advisors powered by Google ADK v1.24.1
- 📊 **Test Coverage** - Comprehensive pytest suite for all components
- 🚫 **Zero errors** - All compilation and syntax issues resolved

**📖 Documentation:**
- See [docs/AGENTS_DOCUMENTATION.md](docs/AGENTS_DOCUMENTATION.md) for AI agent architecture
- See [docs/TEST_RESULTS.md](docs/TEST_RESULTS.md) for testing documentation
- Run `pytest` to verify all functionality

**🔧 Setup:**
```bash
pip install -r requirements.txt
cp .env.example .env  # Configure GOOGLE_API_KEY and other variables
python run.py
```

---

</div>

---

## 📋 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)

---

## 🎯 About

**LiverWatch** is a comprehensive web application designed to empower Ugandans with liver health knowledge, tracking tools, and community support. The platform addresses the growing concern of liver diseases in Uganda by providing accessible health education, personalized tracking, and AI-powered recommendations.

### The Challenge

- Liver diseases (biliary cirrhosis, biliary atresia) are significant health concerns in Uganda, yet awareness remains low
- Limited access to liver health information in local context
- Difficulty tracking liver health metrics over time
- Lack of community support for those affected

### Our Solution

LiverWatch provides:

- 📊 **Health Tracking** - Monitor liver enzymes, symptoms, and health trends
- 🤖 **AI Recommendations** - Personalized health advice based on your data
- 👥 **Community Forum** - Connect with others on similar health journeys
- 📰 **Medical News** - Stay updated with latest liver health research
- 🗺️ **Healthcare Finder** - Locate nearby liver health specialists
- 🍽️ **Diet Resources** - Liver-friendly recipes and nutrition guidance

---

## ✨ Features

### 🔐 Authentication & Authorization (Production-Ready)

- **Secure Registration**: Email validation, password strength requirements (min 8 chars), username uniqueness
- **Rate-Limited Login**: 5 attempts/minute to prevent brute force attacks
- **Session Management**: Flask-Login with "remember me" functionality
- **Password Security**: pbkdf2:sha256 hashing, secure session cookies
- **User Profiles**: View and edit email, change password with current password verification
- **CSRF Protection**: All forms protected with WTForms tokens
- **Active Status Checks**: User accounts can be deactivated without deletion

### 🤖 AI Health Advisors (Google ADK v1.24.1)

| Agent | Purpose | Capabilities |
|-------|---------|-------------|
| **Diet Agent** | Nutrition guidance | Liver-friendly meal plans, food recommendations, dietary restrictions |
| **Health Educator** | Medical information | Disease education, treatment options, prevention strategies |
| **Healthcare Finder** | Provider location | Find specialists, hospitals, clinics with liver care services |
| **Lab Agent** | Result interpretation | Explain liver enzyme tests, trends, normal ranges |
| **Symptom Agent** | Symptom analysis | Assess symptoms, urgency levels, when to seek care |

### 📊 Core Features

| Feature | Description |
|---------|-------------|
| **Health Dashboard** | Interactive charts for liver enzymes (ALT, AST, bilirubin) with trend analysis |
| **AI Health Advisor** | Real-time chat with specialized medical AI agents |
| **Community Forum** | Discussion platform with voting, nested comments, and search |
| **News Aggregator** | Medical news from WHO, CDC, NIH with smart web scraping |
| **Appointment Finder** | Google Maps integration for healthcare facility search |
| **Recipe Database** | 100+ liver-friendly recipes with nutritional breakdowns |
| **Survival Rate Calculator** | Interactive statistics for various liver conditions |
| **Child Health Section** | Pediatric liver health information for newborns through toddlers |

### 👤 User Features

- 📱 **Fully Responsive** - Mobile-first design, works on all devices
- 🎨 **Modern UI** - Clean interface with CSS variables for consistent theming
- 🔔 **Real-time Notifications** - In-app notification center with filters
- 📈 **Personal Analytics** - Track health metrics over time with Chart.js visualizations
- 📧 **Email Subscriptions** - Newsletter with health tips and updates
- 🔍 **Advanced Search** - Find forum posts, recipes, and articles quickly
- ⚡ **Fast Performance** - Event delegation, optimized assets, caching

### 📊 Admin Dashboard

- 📉 **Site Statistics** - User growth, engagement metrics, content analytics
- 👥 **User Management** - View, edit, activate/deactivate accounts
- 📝 **Content Moderation** - Review and manage forum posts and comments
- 📰 **News Management** - Approve, edit, and schedule news articles
- 📨 **Newsletter Tools** - Send targeted emails to subscribers

---

## 🛠️ Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.9+ | Primary programming language |
| **Flask** | 3.x | Web framework with application factory pattern |
| **SQLAlchemy** | 2.x | ORM for database operations with relationship management |
| **Flask-Login** | Latest | User session management and authentication |
| **Flask-Mail** | Latest | Email sending for notifications and newsletters |
| **Flask-Caching** | Latest | Performance optimization with Redis/SimpleCache |
| **Flask-Limiter** | Latest | Rate limiting for authentication and API endpoints |
| **APScheduler** | 3.x | Background task scheduling (news scraping, emails) |
| **BeautifulSoup4** | 4.x | Web scraping for medical news aggregation |
| **Alembic** | 1.x | Database schema migrations |
| **WTForms** | 3.x | Form validation and rendering with CSRF protection |
| **Google ADK** | 1.24.1 | AI agent development kit for health advisors |
| **Werkzeug** | 3.x | Password hashing (pbkdf2:sha256) and security utilities |

### Frontend

| Technology | Purpose |
|------------|---------|
| **HTML5/CSS3** | Semantic markup and modern styling (Grid, Flexbox) |
| **JavaScript (ES6+)** | Event delegation, async/await, modular architecture |
| **Chart.js** | Interactive data visualizations for health metrics |
| **Font Awesome** | 1,000+ icons for consistent UI |
| **Google Fonts** | Inter & Poppins for professional typography |
| **CSS Custom Properties** | Theme variables for consistent colors and spacing |

### Database

| Technology | Purpose |
|------------|---------|
| **SQLite** | Development database (included) |
| **PostgreSQL** | Production database (recommended) |
| **MySQL/MariaDB** | Alternative production option |

### Development & Testing

| Technology | Purpose |
|------------|---------|
| **pytest** | Unit and integration testing framework |
| **pytest-cov** | Test coverage reporting |
| **Flask-Testing** | Flask-specific test utilities |
| **Factory Boy** | Test fixture generation |

---

## 📁 Project Structure

```
LiverWatch/
├── run.py                     # Application entry point
├── requirements.txt           # Python dependencies
├── alembic.ini               # Database migration config
├── pytest.ini                # Test configuration
│
├── app/                       # Main application package (Blueprint architecture)
│   ├── __init__.py           # App factory with Flask-Login setup
│   ├── config.py             # Configuration classes (Dev, Prod, Test)
│   ├── models.py             # SQLAlchemy models (User, Post, HealthLog, etc.)
│   ├── forms.py              # WTForms with validators
│   │
│   ├── blueprints/           # Modular route blueprints
│   │   ├── main.py           # Main routes (home, about, survival rates)
│   │   ├── auth.py           # Authentication (login, register, profile)
│   │   ├── admin.py          # Admin dashboard
│   │   ├── forum.py          # Forum discussions
│   │   ├── health.py         # Health tracker
│   │   ├── api.py            # REST API endpoints
│   │   ├── analytics.py      # Analytics dashboard
│   │   ├── notifications.py  # Notification center
│   │   └── agents.py         # AI agent interactions
│   │
│   ├── services/             # Business logic layer
│   │   ├── ai_recommendations.py  # AI health advisor
│   │   ├── scraper.py        # Medical news web scraper
│   │   └── utils.py          # Helper functions
│   │
│   ├── static/               # Static assets (fully external, zero inline code)
│   │   ├── css/              # Modular CSS architecture
│   │   │   ├── main.css      # Entry point (imports all modules)
│   │   │   ├── variables.css # CSS custom properties (colors, spacing)
│   │   │   ├── base.css      # Reset, typography, global styles
│   │   │   ├── components.css# Reusable UI components (buttons, cards)
│   │   │   ├── layout.css    # Grid, containers, responsive layouts
│   │   │   ├── pages.css     # Page-specific styles
│   │   │   ├── animations.css# Transitions and keyframes
│   │   │   ├── auth.css      # Authentication pages
│   │   │   ├── forum-index.css     # Forum listing
│   │   │   ├── health-tracker.css  # Health dashboard
│   │   │   ├── medical-news.css    # News feed
│   │   │   ├── recipes.css         # Recipe cards
│   │   │   ├── survival-rates.css  # Stats visualizations
│   │   │   ├── ai-assistant.css    # AI chat interface
│   │   │   ├── analytics-dashboard.css  # Analytics charts
│   │   │   └── notification-center.css  # Notifications UI
│   │   │
│   │   ├── js/               # Modular JavaScript (ES6+, event delegation)
│   │   │   ├── core.js       # Core utilities and API client
│   │   │   ├── components.js # UI component logic
│   │   │   ├── app.js        # Main application initialization
│   │   │   ├── health-tracker.js    # Health tracking functionality
│   │   │   ├── forum.js            # Forum interactions
│   │   │   ├── ai-assistant.js     # AI chat interface
│   │   │   ├── analytics-dashboard.js  # Chart.js integration
│   │   │   ├── notifications-center.js # Notification management
│   │   │   ├── question-detail.js      # Forum voting system
│   │   │   └── liver-3d.js        # 3D liver visualization
│   │   │
│   │   └── images/           # Image assets
│   │       ├── liver-logo.svg
│   │       └── favicon-32x32.png
│   │
│   └── templates/            # Jinja2 templates (clean, no inline styles/scripts)
│       ├── base.html         # Base template with navigation
│       ├── index.html        # Homepage with hero and features
│       ├── auth/             # Authentication templates
│       │   ├── login.html
│       │   ├── register.html
│       │   └── profile.html
│       ├── forum/            # Forum templates
│       │   └── index.html
│       ├── health/           # Health tracking templates
│       │   └── tracker.html
│       ├── analytics/        # Analytics templates
│       │   └── dashboard.html
│       ├── notifications/    # Notification templates
│       │   └── center.html
│       └── ...
│
├── liverwatch_agents/        # AI Agent System (Google ADK)
│   ├── __init__.py           # Package initialization
│   ├── agent.py              # Base agent architecture
│   ├── tools.py              # Agent tools and capabilities
│   ├── shared/               # Shared utilities
│   └── sub_agents/           # Specialized agents
│       ├── diet_agent.py           # Nutrition advisor
│       ├── health_educator_agent.py # Health education
│       ├── healthcare_finder_agent.py # Facility locator
│       ├── lab_agent.py            # Lab result interpreter
│       └── symptom_agent.py        # Symptom analyzer
│
├── tests/                    # Comprehensive test suite
│   ├── conftest.py           # Pytest fixtures
│   ├── test_auth.py          # Authentication tests
│   ├── test_api.py           # API endpoint tests
│   ├── test_models.py        # Database model tests
│   ├── test_security.py      # Security feature tests
│   ├── test_integration.py   # Integration tests
│   └── test_agents.py        # AI agent tests
│
├── migrations/               # Database migrations (Alembic)
│   ├── env.py
│   └── versions/
│
└── docs/                     # Documentation
    ├── AGENTS_DOCUMENTATION.md  # AI agent architecture guide
    └── TEST_RESULTS.md         # Test coverage report
```

### 🎨 Code Quality Highlights

- **Zero Inline Code**: All CSS and JavaScript fully external and modular
- **Event Delegation**: Efficient event handling patterns throughout
- **CSS Variables**: Consistent theming with custom properties
- **Blueprint Architecture**: Organized routes with proper separation of concerns
- **Type Safety**: Comprehensive form validation with WTForms
- **Security**: Rate limiting, CSRF protection, password hashing (pbkdf2:sha256)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/liverwatch.git
cd liverwatch
```

2. **Create a virtual environment**

```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS/Linux
python3 -m venv env
source env/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

```bash
# Create .env file with:
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///liverwatch.db
GOOGLE_MAPS_API_KEY=your-api-key
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password
```

5. **Initialize the database**

```bash
flask db upgrade
```

6. **Run the development server**

```bash
python run.py
```

The application will be available at `http://localhost:5000`

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key | Yes |
| `DATABASE_URL` | Database connection string | Yes |
| `GOOGLE_MAPS_API_KEY` | For healthcare finder | No |
| `MAIL_SERVER` | SMTP server | No |
| `MAIL_USERNAME` | Email username | No |
| `MAIL_PASSWORD` | Email password | No |

---

## 📡 API Documentation

### REST API Endpoints

#### Authentication
```
POST /auth/register         - Create new account
POST /auth/login           - User login
GET  /auth/logout          - User logout
GET  /auth/profile         - View profile
POST /auth/profile/edit    - Update email
POST /auth/change-password - Change password
```

#### Health Tracking
```
GET  /api/health/logs              - Get user's health logs
POST /api/health/log               - Add health log entry
GET  /api/health/recommendations   - Get AI-generated recommendations
GET  /api/health/trends            - Get trend analysis
```

#### Forum
```
GET  /api/forum/posts      - List forum posts with pagination
POST /api/forum/post       - Create new post
POST /api/forum/vote       - Vote on post or answer
POST /api/forum/comment    - Add comment
GET  /api/forum/search     - Search posts by keyword
```

#### AI Agents
```
POST /api/agents/chat      - Send message to AI agent
GET  /api/agents/history   - Get conversation history
POST /api/agents/diet      - Get diet recommendations
POST /api/agents/symptom   - Analyze symptoms
```

---

## 🧪 Testing

Run the complete test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

Test coverage includes:
- ✅ Authentication and authorization flows
- ✅ API endpoint responses and error handling
- ✅ Database model relationships and constraints
- ✅ Form validation and CSRF protection
- ✅ Security features (rate limiting, password hashing)
- ✅ AI agent integrations

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards

- Follow PEP 8 style guide for Python code
- Write semantic HTML5 with proper accessibility
- Use CSS custom properties for theming
- Implement event delegation for JavaScript
- Add tests for new features
- Update documentation as needed

---

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

© 2026 Kweezi Perez Christopher. All rights reserved.

---

## 🙏 Acknowledgments

### Data Sources

- **WHO** (World Health Organization) - Global liver health statistics
- **CDC** (Centers for Disease Control and Prevention) - Disease information
- **NIH** (National Institutes of Health) - Research articles
- **American Liver Foundation** - Patient resources
- **Hepatitis B Foundation** - Hepatitis-specific guidance

### Technologies

- Google AI for Agent Development Kit (ADK)
- Flask and Pallets Projects team
- Chart.js for data visualization
- Font Awesome for iconography

---

<div align="center">

**Made with ❤️ for Uganda**

Empowering Ugandans with liver health knowledge and comprehensive care tools.

[Report Bug](https://github.com/yourusername/liverwatch/issues) · [Request Feature](https://github.com/yourusername/liverwatch/issues)

</div>
