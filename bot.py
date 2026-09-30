import os
import telebot
import psycopg2
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
db_url = os.getenv("DATABASE_URL")
bot = telebot.TeleBot(token)

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
        "_(Maks. 2 site izni)_\n\n"
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
        print("Hata:", e)
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
        print("Hata:", e)
        bot.send_message(chat_id, "Eklenirken bir hata oluştu.")
    finally:
        cursor.close()
        connection.close()


# Keep the bot running in continuous listening mode (Polling)
print("System is online: Bot is listening to Telegram servers...")
bot.infinity_polling()