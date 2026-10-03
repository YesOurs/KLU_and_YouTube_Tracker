import os
import re
import requests
import telebot
import psycopg2
from dotenv import load_dotenv
import threading
from flask import Flask

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
db_url = os.getenv("DATABASE_URL")
bot = telebot.TeleBot(token)

# --- FAKE WEB SERVER FOR RENDER ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is awake and running!"

def run_web():
    # Get the port assigned by Render dynamically, default to 8080 if not found
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
# ----------------------------------


# Router Layer: Catch incoming /start commands
@bot.message_handler(commands=['start'])
def handle_start(message):

    chat_id = message.chat.id
    
    connection = None

    try:
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()
        
        # Idempotent insert query to store the user
        insert_query = """
        INSERT INTO users (telegram_chat_id)
        VALUES (%s)
        ON CONFLICT (telegram_chat_id) DO NOTHING;
        """
        cursor.execute(insert_query, (chat_id,))
        connection.commit()
        
        print(f"User registered to database successfully. Chat ID: {chat_id}")
        
    except (Exception, psycopg2.Error) as error:
        print("Database error:", error)
        
    finally:
        # Close the connection securely after the operation
        if connection:
            cursor.close()
            connection.close()

    # Send a confirmation message to the user
    welcome_text = (
        "🤖 *KLU ve YouTube Takip Botuna Hoş Geldin!*\n\n"
        "Sistemi kullanmak için aşağıdaki komutları kullanabilirsin:\n\n"
        "📺 *YouTube Kanalı Eklemek İçin:*\n"
        "`/add_youtube <RSS_LINKI>`\n"
        "_(Maks. 10 kanal izni)_\n\n"
        "🎓 *Üniversite/Fakülte Duyurusu Eklemek İçin:*\n"
        "`/add_uni <WEBSITE_LINKI>`\n"
        "_(Maks. 3 site izni)_\n\n"
        "🗑️ *Takip Listesinden Çıkarmak İçin:*\n"
        "`/sil <LINK>`\n\n"
        "Linkleri ekledikten sonra sistem periyodik olarak tarama yapacak ve yeni bir veri bulduğunda sana anında mesaj atacaktır."
    )
    
    bot.send_message(chat_id, welcome_text, parse_mode='Markdown')


# /add_youtube command
@bot.message_handler(commands=['add_youtube'])
def handle_add_youtube(message):
    chat_id = message.chat.id
    text_parts = message.text.split()
    
    if len(text_parts) < 2:
        bot.send_message(chat_id, "Kullanım: /add_youtube <RSS_LINKI>")
        return

    url = text_parts[1]

    # Check if the URL is a standard YouTube link and not already an XML feed
    if "youtube.com" in url or "youtu.be" in url:

        if "feeds/videos.xml" not in url:
            # Notify the user that the channel is being analyzed and converted to RSS format
            bot.send_message(chat_id, "🔍 Kanal analiz ediliyor...")

            try:
                # Disguise as a standard web browser to fetch the page content securely
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=10)

                # Search for the channel ID starting with "UC" inside the raw HTML using Regex
                match = re.search(r'"channelId":"(UC[\w-]+)"', response.text)

                # If a match is found, extract the ID and overwrite the url variable with the pure XML format
                if match:
                    channel_id = match.group(1)
                    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

                else:
                    bot.send_message(chat_id, "Kanal bulunamadı.")
                    return
                
            except Exception as e:
                bot.send_message(chat_id, "Link çözümlenirken hata oluştu")
                return

    # Simple connection management (Can be upgraded to connection pool for performance)
    connection = psycopg2.connect(db_url)
    cursor = connection.cursor()

    try:
        # Get User ID
        cursor.execute("SELECT id FROM users WHERE telegram_chat_id = %s", (chat_id,))
        user_row = cursor.fetchone()
        if not user_row:
            bot.send_message(chat_id, "Önce /start komutu ile sisteme kaydolmalısın.")
            return
        
        user_id = user_row[0]

        # Limit check (Max 10)
        cursor.execute("""
            SELECT COUNT(*) FROM user_subscriptions us
            JOIN feeds f ON us.feed_id = f.id
            WHERE us.user_id = %s AND f.feed_type = 'youtube_rss'
        """, (user_id,))
        
        youtube_count = cursor.fetchone()[0]
        if youtube_count >= 10:
            bot.send_message(chat_id, "Maksimum limit olan 10 YouTube kanalına zaten abonesin.")
            return

        # Add link to feeds table (or get ID if it exists via UPSERT)
        cursor.execute("""
            INSERT INTO feeds (name, url, feed_type)
            VALUES (%s, %s, 'youtube_rss')
            ON CONFLICT (url) DO UPDATE SET url = EXCLUDED.url RETURNING id;
        """, ("YouTube Channel", url))
        
        feed_id = cursor.fetchone()[0]

        # Create the subscription mapping
        cursor.execute("""
            INSERT INTO user_subscriptions (user_id, feed_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user_id, feed_id))

        connection.commit()
        bot.send_message(chat_id, "YouTube kanalı başarıyla takip listene eklendi.")

    except Exception as e:
        print("Error:", e)
        bot.send_message(chat_id, "Eklenirken bir hata oluştu.")
    finally:
        cursor.close()
        connection.close()


# /add_uni command
@bot.message_handler(commands=['add_uni'])
def handle_add_uni(message):
    chat_id = message.chat.id
    text_parts = message.text.split()
    
    if len(text_parts) < 2:
        bot.send_message(chat_id, "Kullanım: /add_uni <RSS_LINKI>")
        return

    url = text_parts[1]
    
    connection = psycopg2.connect(db_url)
    cursor = connection.cursor()

    try:
        # Get User ID
        cursor.execute("SELECT id FROM users WHERE telegram_chat_id = %s", (chat_id,))
        user_row = cursor.fetchone()
        if not user_row:
            bot.send_message(chat_id, "Önce /start komutu ile sisteme kaydolmalısın.")
            return
        
        user_id = user_row[0]

        # Limit check (Max 10)
        cursor.execute("""
            SELECT COUNT(*) FROM user_subscriptions us
            JOIN feeds f ON us.feed_id = f.id
            WHERE us.user_id = %s AND f.feed_type = 'klu_web'
        """, (user_id,))
        
        youtube_count = cursor.fetchone()[0]
        if youtube_count >= 3:
            bot.send_message(chat_id, "Daha fazla websitesini takip edemezsin.")
            return

        # Add link to feeds table
        cursor.execute("""
            INSERT INTO feeds (name, url, feed_type)
            VALUES (%s, %s, 'klu_web')
            ON CONFLICT (url) DO UPDATE SET url = EXCLUDED.url RETURNING id;
        """, ("KLU Website", url))
        
        feed_id = cursor.fetchone()[0]

        # Create the subscription mapping
        cursor.execute("""
            INSERT INTO user_subscriptions (user_id, feed_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user_id, feed_id))

        connection.commit()
        bot.send_message(chat_id, "Fakülte başarıyla takip listene eklendi.")

    except Exception as e:
        print("Error:", e)
        bot.send_message(chat_id, "Eklenirken bir hata oluştu.")
    finally:
        cursor.close()
        connection.close()


# /sil command to delete an existing subscription
@bot.message_handler(commands=['sil'])
def handle_remove(message):
    chat_id = message.chat.id
    text_parts = message.text.split()

    if len(text_parts) < 2:
        bot.send_message(chat_id, "Kullanım: /sil <RSS_LINKI>")
        return

    url = text_parts[1]
    
    connection = psycopg2.connect(db_url)
    cursor = connection.cursor()

    try:
        # Get User ID
        cursor.execute("SELECT id FROM users WHERE telegram_chat_id = %s", (chat_id,))
        user_row = cursor.fetchone()
        if not user_row:
            bot.send_message(chat_id, "Önce /start komutu ile sisteme kaydolmalısın.")
            return
        
        user_id = user_row[0]

        # Get Feed ID from the provided URL
        cursor.execute("SELECT id FROM feeds WHERE url = %s", (url,))
        feed_row = cursor.fetchone()

        if not feed_row:
            bot.send_message(chat_id, "Sistemde böyle bir link bulunamadı.")
            return

        feed_id = feed_row[0]

        # Delete the specific subscription mapping
        cursor.execute("""
            DELETE FROM user_subscriptions 
            WHERE user_id = %s AND feed_id = %s
            RETURNING user_id;
        """, (user_id, feed_id))
        
        deleted_row = cursor.fetchone()
        
        if deleted_row:
            connection.commit()
            bot.send_message(chat_id, "Link başarıyla takip listenden çıkarıldı ve limitin açıldı.")
        else:
            bot.send_message(chat_id, "Bu link zaten takip listende bulunmuyor.")

    except Exception as e:
        print("Error:", e)
        bot.send_message(chat_id, "Silinirken bir hata oluştu.")
    finally:
        cursor.close()
        connection.close()


# Keep the bot running in continuous listening mode (Polling)
if __name__ == "__main__":
    # Start the web server in a separate thread so it doesn't block the bot
    threading.Thread(target=run_web).start()
    
    # Start the bot
    print("System online: Bot is listening...")
    bot.infinity_polling()
