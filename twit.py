import tweepy
from config import *
import datetime

client = tweepy.Client(
    TWITTER_BEARER_TOKEN,
    TWITTER_API_KEY,
    TWITTER_SECRET_KEY,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
)

ct = datetime.datetime.now()
market_open = datetime.datetime.now().replace(hour=5, minute=0, second=0, microsecond=0)


def tweet(message):
    try:
        client.create_tweet(text=message)

    except Exception as e:
        print(e)
        return False


def open_notification():
    try:
        if ct == market_open:
            client.create_tweet(text="Market is open!")
        else:
            client.create_tweet(text="Market is closed.")
    except Exception as e:
        print(e)
        return False


def main():
    open_notification()
    return client


if __name__ == "__main__":
    main()
