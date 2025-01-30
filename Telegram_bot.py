import tweepy
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, timedelta

# Replace these with your actual Twitter API credentials
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAN0gygEAAAAALhNhPiyigWLtAhRA8qHFBHyjwzo%3DYdP47pAj6HXPuKOujHSIl74PpRAg88MtueK4f1zsimtGAQmxvb'

# Telegram bot token
telegram_token = '7589194100:AAEkADr396PO6WZ_aPjlE3IrGsZouiJRYa0'

# Authenticate Twitter API using v2
client = tweepy.Client(bearer_token=bearer_token)

# Store the last time a user requested tweets (user_id -> last_request_time)
user_last_request_time = {}

# Function to get latest 5 tweets using Twitter API v2
def get_latest_tweets(username: str):
    try:
        user = client.get_user(username=username)
        user_id = user.data['id']
        tweets = client.get_users_tweets(user_id, max_results=5)
        if tweets.data:
            return [tweet.text for tweet in tweets.data]
        else:
            return "No tweets found for this username."
    except tweepy.TooManyRequests:
        return "Rate limit exceeded. Please try again later."
    except tweepy.TweepyException as e:
        return f"Error fetching tweets: {e}"

# Command handler for /start in Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Get the latest tweets from any Twitter user. "
        "You can only request once every 15 minutes. Example: /tweets TheRock"
    )

# Command handler for /tweets in Telegram
async def tweets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = ' '.join(context.args)  # Get the username from command arguments
    if not username:
        await update.message.reply_text("Please provide a Twitter username. Example: /tweets TheRock")
        return

    user_id = update.message.from_user.id
    current_time = datetime.now()

    # If the user has made a previous request, check the time difference
    if user_id in user_last_request_time:
        last_request = user_last_request_time[user_id]
        time_left = timedelta(minutes=15) - (current_time - last_request)

        if time_left > timedelta(0):  # If the user has to wait
            minutes_left = time_left.seconds // 60
            seconds_left = time_left.seconds % 60
            await update.message.reply_text(f"You can only make one request in {minutes_left} minute(s) and {seconds_left} second(s). Please try again later.")
            return
    # If the user hasn't made a request before, they can proceed
    else:
        # Proceed with fetching tweets
        tweets = get_latest_tweets(username)

        if tweets == "Rate limit exceeded. Please try again later.":
            await update.message.reply_text(tweets)
            return

        if isinstance(tweets, str):  # If there's an error message
            await update.message.reply_text(tweets)
        else:
            tweet_text = "\n\n".join(f"{i+1}. {tweet}" for i, tweet in enumerate(tweets))
            await update.message.reply_text(tweet_text)

            # Update the time of the last request
            user_last_request_time[user_id] = current_time

        await update.message.reply_text("Thank you for using.")

# Command handler for /end in Telegram
async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_last_request_time:
        del user_last_request_time[user_id]
        await update.message.reply_text("Your session has been ended and data cleared.")
    else:
        await update.message.reply_text("You don't have an active session to end.")

# Main function to run the Telegram bot
def main():
    application = Application.builder().token(telegram_token).build()

    # Add the command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('tweets', tweets))
    application.add_handler(CommandHandler('end', end))  # End session

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
