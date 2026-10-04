# KLU & YouTube Tracker Bot
#### Video Demo:  <URL HERE>
#### Description:

My final project for CS50 is a serverless, microservice-based Telegram Bot. I built this system to automatically monitor selected YouTube channels and Kırklareli University (KLU) websites, and notify me instantly when new videos or announcements are published. 

As a software engineering student, I constantly need to track my university's faculty announcements alongside educational YouTube channels. Doing this manually every day takes a lot of time. I wanted to build my own personalized RSS tracking system, but my main goal was to achieve this with a completely zero-cost architecture. Because of this goal, the project is not just a simple script, but a split-system design that balances free cloud tiers to run 24/7.

### Project Architecture

To keep the project free, I had to divide the system into two independent modules:
1. **The Interface (Bot):** This handles user registrations, adding new channels, and communicating with the Telegram API. It needs to run constantly.
2. **The Worker (Scraper):** This is the heavy-lifting script that downloads HTML/XML data, checks for new content, and writes to the database. It only needs to run periodically.

### File-by-File Breakdown

Here is a detailed explanation of what each file in my project contains and does:

*   **`bot.py`**: This is the main interface of the project. It uses the `telebot` library to communicate with Telegram. It includes command handlers like `/start` (to register a user to the database) and `/add_youtube` or `/add_klu` (to add specific links to track). It connects directly to my PostgreSQL database to verify if a user has exceeded their subscription limits (e.g., maximum 10 YouTube channels and 3 university URLs). To keep this file running 24/7 for free, I deployed it on Render. Since Render puts free web services to sleep after 15 minutes of inactivity, I implemented a lightweight Flask server inside this file. This creates a fake HTTP port that UptimeRobot pings every 5 minutes to keep the bot awake.

*   **`scraper.py`**: This is the background worker of the project. Instead of running continuously and consuming server memory, this file is executed by a GitHub Actions cron job every few hours. When it runs, it connects to the database, fetches all the monitored URLs, and uses the `requests` library to download their content. It parses the data to find the newest 2 items, compares them with the database, and if a new item is found, it triggers the Telegram bot token to send a message to the subscribed users.

*   **`requirements.txt`**: This file contains all the Python dependencies required to run the project. It includes `pyTelegramBotAPI` for the bot, `psycopg2-binary` for the PostgreSQL connection, `beautifulsoup4` and `lxml` for parsing web data, and `Flask` for the keep-alive server.

*   **`.env`** (Not uploaded to GitHub for security): This file stores my sensitive environment variables, specifically the `TELEGRAM_BOT_TOKEN` and the `DATABASE_URL`.

### Key Design Choices & Trade-offs

During the development of this project, I made several important design choices to handle real-world constraints:

**1. The URL Interceptor (UX Optimization)**
Normally, to track a YouTube channel via RSS, a user must find the hidden XML channel ID (e.g., `https://www.youtube.com/feeds/videos.xml?channel_id=UC...`). Expecting users to find this is terrible for user experience. I decided to write a background URL Interceptor in `bot.py`. Now, a user can just send a standard YouTube link. The bot fetches the channel's raw HTML, uses Regex (`re` module) to extract the hidden channel ID, and converts it into a pure XML link before saving it to the database. 

**2. Choosing `lxml` over HTML Parsing**
Initially, I tried scraping YouTube videos by parsing the HTML structure. However, YouTube is heavily JavaScript-based and its HTML changes often. I decided to switch my strategy in `scraper.py` to use `lxml` and parse YouTube's native XML RSS feeds instead. This guarantees long-term stability even if YouTube completely redesigns its website.

**3. Idempotent Database Architecture**
Since the `scraper.py` file might be triggered multiple times, or multiple users might subscribe to the same channel, I had to prevent the bot from sending duplicate spam messages. I designed my PostgreSQL database using `ON CONFLICT DO NOTHING` and `DO UPDATE` constraints. This ensures that every video or announcement is only recorded once using its unique GUID, keeping the system safe from race conditions.

**4. The Zero-Cost Latency Trade-off**
Using GitHub Actions as a free cron job server comes with a cost: time. GitHub's shared runners do not guarantee exact minute-level execution. Sometimes my scraper runs every 3 hours, and sometimes every 8 hours depending on global server traffic. I debated using a paid VPS for instant notifications, but I decided that for my specific needs (university news and videos), a few hours of delay is a perfectly acceptable trade-off to keep the entire infrastructure completely free and maintenance-free.

### Database Schema
- `users`: Stores unique Telegram Chat IDs and active status.
- `feeds`: Stores the monitored URLs (converted to RSS) and feed types.
- `user_subscriptions`: Connects users to their feeds.
- `items`: Logs previously fetched announcements and videos via unique GUIDs.

### Setup and Installation
1. Clone the repository to your local machine.
2. Create a `.env` file in the root directory and add your `TELEGRAM_BOT_TOKEN` and `DATABASE_URL` (Supabase recommended).
3. Install the required libraries using `pip install -r requirements.txt`.
4. Run the bot interface using `python bot.py`.
5. Run the background worker manually using `python scraper.py` or set it up with GitHub Actions.

### Acknowledgements
As permitted by the CS50 Final Project guidelines, AI tools (Gemini) were used to amplify productivity. The AI acted as a pair-programmer for syntax generation, debugging SQL queries, and refining Regex patterns. The overall system architecture, the split-module design, the database idempotency, and the URL Interceptor logic are entirely my own original work.

### Author
Kaan E. - Kırklareli/Türkiye
