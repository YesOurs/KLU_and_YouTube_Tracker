# KLU & YouTube Tracker Bot
#### Video Demo:  COMING SOON
#### Description:

This project is a fully serverless, microservice-based Telegram Bot developed as a final project for CS50. The system is designed to monitor selected YouTube channels and Kırklareli University (KLU) websites, notifying users instantly when new content or announcements are published.

The architecture is deliberately split into two independent modules to achieve a zero-cost deployment model:
1. **The Bot (`bot.py`)**: A continuous polling service that handles user registration, subscription limits (max 10 YouTube channels, max 3 university URLs), and direct Telegram API communication.
2. **The Scraper (`scraper.py`)**: A stateless, ephemeral script triggered via GitHub Actions cron jobs (running hourly). It fetches RSS feeds and parses HTML/XML to find new items.

### Key Engineering Decisions & Trade-offs
- **URL Interceptor (UX Optimization):** Expecting users to manually find and format YouTube's hidden XML feeds is poor UX. The bot implements a background Regex interceptor that automatically fetches the channel's raw HTML, extracts the hidden `channelId`, and converts standard YouTube URLs (e.g., `@ChannelName`) into pure RSS endpoints seamlessly before database insertion.
- **Robust XML Parsing:** Instead of relying on brittle HTML scraping for dynamic JavaScript-heavy sites like YouTube, the scraper utilizes `lxml` to parse YouTube's native XML feeds. This ensures absolute long-term stability even if YouTube completely changes its frontend UI.
- **Idempotency & UPSERT Architecture:** To handle network race conditions and prevent redundant data when multiple users subscribe to the same channel, the database uses a Many-to-Many relationship with `ON CONFLICT DO UPDATE` and `DO NOTHING` constraints. This guarantees a single-source-of-truth for feeds and keeps memory consumption strictly horizontal.
- **Zero-Cost Infrastructure vs. Latency Trade-off:** The system operates entirely on free-tier cloud services. While GitHub Actions shared runners do not guarantee exact minute-level cron execution (introducing asynchronous latency during peak global hours), this was consciously accepted as an architectural trade-off. For university announcements and YouTube videos, a slight delay is perfectly acceptable in exchange for a serverless, maintenance-free, and zero-cost pipeline.

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
5. (Optional) Run the scraper manually: `python scraper.py`

### Author
YesOurs - Kırklareli/Türkiye
