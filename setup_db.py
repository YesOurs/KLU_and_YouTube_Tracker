import os
import psycopg2
from dotenv import load_dotenv

connection = None

try:
    # Load variables from .env file
    load_dotenv()

    # Access environment variables
    db_url = os.getenv("DATABASE_URL")
    connection = psycopg2.connect(db_url)

    # Make cursor
    cursor = connection.cursor()

    # Creating the tables
    create_table_users = """CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_chat_id BIGINT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    subscription_limit INTEGER DEFAULT 10,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );"""

    cursor.execute(create_table_users)

    create_table_feeds = """CREATE TABLE IF NOT EXISTS feeds (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    feed_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );"""

    cursor.execute(create_table_feeds)

    create_table_items = """CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    feed_id INTEGER REFERENCES feeds(id) ON DELETE CASCADE,
    guid TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );"""

    cursor.execute(create_table_items)

    create_table_user_subscriptions = """CREATE TABLE IF NOT EXISTS user_subscriptions (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    feed_id INTEGER REFERENCES feeds(id) ON DELETE CASCADE,
    last_notified_item_id INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, feed_id)
    );"""

    cursor.execute(create_table_user_subscriptions)

    connection.commit()

except (Exception, psycopg2.Error) as error:
    print("PostgreSQL connection error", error)

finally:
    # Close the connections securely
    if connection:
        cursor.close()
        connection.close()
        print("Database successfuly created!")
        print("PostgreSQL connection has been closed")