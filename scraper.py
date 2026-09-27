import os
import psycopg2
import requests
import telebot
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv

connection = None

def run_scraper():
    try:
        load_dotenv()
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        db_url = os.getenv("DATABASE_URL")
        bot = telebot.TeleBot(token)

        # Initialize Database Connection
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()

        # Fetch all monitored feeds from the database
        cursor.execute("SELECT id, url, feed_type FROM feeds")
        sources = cursor.fetchall()

        news = []

        for source in sources:

            feed_id = source[0]
            url = source[1]
            feed_type = source[2]

            if feed_type == 'youtube_rss':
                print(f"[{feed_id}] A request is being sent to the YouTube RSS feed: {url}")

                response = requests.get(url)

                if response.status_code == 200:
                    # 'xml' parser is technically safer for RSS feeds than 'html.parser'
                    print("Downloaded data:", response.text[:300])
                    soup = BeautifulSoup(response.text, "html.parser")

                    all_links = soup.find_all("entry")

                    # Limit to first 5 items to optimize performance
                    for link in all_links[:5]:
                        guid = link.find("id").text
                        title = link.find("title").text
                        published = link.find("published").text

                        url_link = link.find("link")
                        url = url_link.get("href")

                        print(f"Found: {title} - {guid}")

                        insert_query = """
                        INSERT INTO items (feed_id, guid, title, url, published_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO NOTHING RETURNING id;
                        """
                        cursor.execute(insert_query, (feed_id, guid, title, url, published))
                        result = cursor.fetchone()

                        # If a new video is found, notify subscribers
                        if result:
                            news.append({"title": title, "url": url})

                            # Find subscribers for this specific feed
                            cursor.execute("""
                                    SELECT u.telegram_chat_id FROM user_subscriptions us
                                    JOIN users u ON us.user_id = u.id
                                    WHERE us.feed_id = %s AND u.is_active = TRUE
                                """, (feed_id,))

                            subscribers = cursor.fetchall()

                            for sub in subscribers:
                                try:
                                    bot.send_message(sub[0], f"🎥 Yeni Video:\n{title}\n{url}")
                                except Exception as e:
                                    print(f"Failed to send Telegram message to {sub[0]}: {e}")

            elif feed_type == 'klu_web':
                print(f"[{feed_id}] A request is being sent to the KLU website: {url}")

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    print("Downloaded KLU data successfully.")
                    soup = BeautifulSoup(response.text, "html.parser")

                    all_links = soup.find_all("td")

                    # Limit to first 10 to optimize performance
                    for link in all_links[:10]:
                        a_tag = link.find("a")

                        # If an anchor tag exists inside the cell
                        if a_tag:
                            announcement_url = a_tag.get("href")
                            title = a_tag.text.strip()
                            guid = announcement_url 

                            print(f"Found: {title}")

                            # Use CURRENT_TIMESTAMP for published_at since HTML lacks a date tag
                            insert_query = """
                            INSERT INTO items (feed_id, guid, title, url, published_at)
                            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (guid) DO NOTHING RETURNING id;
                            """
                            
                            cursor.execute(insert_query, (feed_id, guid, title, announcement_url))

                            # Catch the returning ID to identify brand new announcements
                            result = cursor.fetchone()
                            if result:
                                absolute_url = urljoin(url, announcement_url)
                                news.append({"title": title, "url": absolute_url})

                            # Find subscribers for this specific feed
                                cursor.execute("""
                                    SELECT u.telegram_chat_id FROM user_subscriptions us
                                    JOIN users u ON us.user_id = u.id
                                    WHERE us.feed_id = %s AND u.is_active = TRUE
                                """, (feed_id,))

                                subscribers = cursor.fetchall()

                                for sub in subscribers:
                                    try:
                                        bot.send_message(sub[0], f"📌 Yeni KLU Duyurusu:\n{title}\n{absolute_url}")
                                    except Exception as e:
                                        print(f"Failed to send Telegram message to {sub[0]}: {e}")
                                
                else:
                    print(f"Failed to fetch KLU data. Status code: {response.status_code}")

        connection.commit()
        print("New data has been stored!")

    except (Exception, psycopg2.Error) as error:
        print("PostgreSQL connection error", error)

    finally:
    # Close the connections securely
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection has been closed")


if __name__ == "__main__":
    print("GitHub Actions triggered the scraper. Scanning started...")
    run_scraper() 
    print("Scanning complete. Terminating script.")

