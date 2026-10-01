# KLU & YouTube Tracker Bot
#### Video Demo:  
#### Description:

This project is a fully serverless, microservice-based Telegram Bot developed as a final project for CS50. The system is designed to monitor selected YouTube channels and Kırklareli University (KLU) websites, notifying users instantly when new content or announcements are published. 

The architecture is deliberately split into two independent modules to achieve a zero-cost deployment model:
1. **The Bot (`bot.py`)**: A continuous polling service that handles user registration, subscription limits (max 10 YouTube channels, max 2 university URLs), and direct Telegram API communication.
2. **The Scraper (`scraper.py`)**: A stateless, ephemeral script triggered via GitHub Actions cron jobs (running hourly). It fetches RSS feeds and parses HTML (using BeautifulSoup) to find new items.

### Technologies Used
- **Python 3.10**: Core logic, `telebot` for Telegram API integration, `BeautifulSoup` for HTML parsing.
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
5. (Optional) Run the scraper manually: `python scraper.py`

### Author
YesOurs - Kırklareli/Türkiye
