# KLU & YouTube Tracker Bot
#### Video Demo:  COMING SOON
#### Description:

This project is a fully serverless, microservice-based Telegram Bot developed as a final project for CS50. The system is designed to monitor selected YouTube channels and Kırklareli University (KLU) websites, notifying users instantly when new content or announcements are published.

The architecture is deliberately split into two independent modules to achieve a zero-cost deployment model:
1. **The Bot (`bot.py`)**: A continuous polling service that handles user registration, subscription limits (max 10 YouTube channels, max 3 university URLs), and direct Telegram API communication.
2. **The Scraper (`scraper.py`)**: A stateless, ephemeral script triggered via GitHub Actions cron jobs (running hourly). It fetches RSS feeds and parses HTML/XML to find new items.

### How It Works & Technical Details
- **URL Conversion:** Normal YouTube URLs don't work for RSS. Instead of asking users to find the hidden XML links, the bot takes standard YouTube links and uses Regex to extract the channel ID in the background. 
- **XML Parsing:** I used `lxml` to parse YouTube feeds instead of standard HTML scraping. It is much more stable if YouTube changes its website design.
- **Database:** I used a PostgreSQL database with `ON CONFLICT DO NOTHING` constraints. This prevents duplicate notifications if the scraper runs multiple times.
- **Free Hosting Setup:** To keep the project free, I separated the logic. The main bot runs on Render (kept awake by UptimeRobot), and the scraper is scheduled to run every 3 hours using GitHub Actions (though real-world execution depends on GitHub's server load).

### Technologies Used
- **Python 3.10**: Core logic, `telebot` for Telegram API integration, `BeautifulSoup` and `lxml` for HTML/XML parsing, `re` (Regex) for URL interception.
- **Flask (Render)**: A lightweight fake web server implementation to keep the bot alive via external pings.
- **PostgreSQL (Supabase)**: Cloud database serving as the central bridge between the bot and the scraper.
- **GitHub Actions**: CI/CD pipeline used as a serverless cron scheduler.

### Database Architecture
The database employs a relational model utilizing `ON CONFLICT` statements to ensure data integrity and prevent duplicate notifications.
- `users`: Stores unique Telegram Chat IDs.
- `feeds`: Stores monitored URLs (YouTube RSS or KLU web pages).
- `user_subscriptions`: A mapping table linking users to their specific feed limits.
- `items`: Logs previously fetched announcements/videos (via unique GUIDs) to prevent flood messaging.

### Setup and Installation
To run this project locally:
1. Clone the repository.
2. Create a `.env` file in the root directory with your `TELEGRAM_BOT_TOKEN` and `DATABASE_URL`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run the bot: `python bot.py`
5. Run the scraper manually: `python scraper.py`

### Acknowledgements & AI Usage
As permitted by the CS50 Final Project guidelines, AI tools (Gemini) were utilized to amplify productivity. The AI acted as a coding assistant for syntax generation and debugging. The core concepts, including the zero-cost deployment architecture, the URL Interceptor logic, and the idempotent database design, are my original work.

### Author
Kaan E. - Kırklareli/Türkiye
