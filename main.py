import instaloader
import asyncio
import requests
import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

authname = "YOUR AUTHNAME"
password = "YOUR PASSWORD"
token = "YOUR TOKEN"

### LOGGING SETUP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

### INSTALOADER FUNC's

async def inst_authorize_account(authname: str, password: str) -> None:
    global followees, last_posts_check

    try:
        L.login(authname, password)
        logger.info(f"Logged in as @{authname}")

    except instaloader.exceptions.LoginRequiredException:
        logger.error(f"Failed to log in: username '{authname}' doesn't exist.")
    except instaloader.exceptions.BadCredentialsException:
        logger.error(f"Failed to log in: incorrect password for '{authname}'.")
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        logger.error(f"Failed to log in: 2FA is not supported.")
    except instaloader.exceptions.ConnectionException:
        logger.error(f"Failed to connect to Instagram.")

    account = instaloader.Profile.from_username(L.context, authname)
    followees = [user.username for user in account.get_followees()]
    last_posts_check = {username: None for username in followees}
    logger.info(f"Initialized account instance, ({len(followees)}) followees.")

async def inst_parse_post(chat_id, context) -> None:
    await inst_authorize_account(authname, password)

    while inst_parser_on:
        try:
            for username in followees:
                logger.info(f"Parsing @{username}")
                followee = instaloader.Profile.from_username(L.context, username)
                latest_post = followee.get_posts().__next__()
                if latest_post.shortcode != last_posts_check[username]:
                    logger.info(f"New post by @{username}!")
                    # Processing message:
                    with open("media.jpg", "wb") as f: 
                        f.write(requests.get(latest_post.url).content)
                    inline_open = InlineKeyboardMarkup([[InlineKeyboardButton(text="Open", url=f"https://instagram.com/p/{latest_post.shortcode}")]])
                    message = f"<code>{username} poured:</code>\n\n" \
                              f"{latest_post.caption}"
                    
                    # Calling message:
                    await context.bot.send_photo(chat_id=chat_id,
                                                 photo=open("media.jpg", "rb"),
                                                 caption=message,
                                                 reply_markup=inline_open,
                                                 parse_mode=constants.ParseMode.HTML)
                    
                    # Storing the latest post ID per username & image cleanup:
                    last_posts_check[username] = latest_post.shortcode
                    os.remove("media.jpg")
                await asyncio.sleep(15)

            await asyncio.sleep(600)
        except instaloader.exceptions.LoginRequiredException:
            logger.warning("Attempting relogin...")
            await inst_authorize_account(authname, password)

### TELEGRAM BOT

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                   text=f"Hi, {update.effective_user.first_name}! Let's brew some coffee for you! \n\n"
                                        "Use /brew to launch parser. \n\n"
                                        "<code>Note: using throwaway, side account is always good idea.</code>",
                                   parse_mode=constants.ParseMode.HTML)

async def brew(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global inst_parser_on

    inst_parser_on = True
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                text="Your coffee will begin to drip here.\n"
                                     "Once you don't want me brewing anymore - use <b>/stop</b> command.",
                                parse_mode=constants.ParseMode.HTML)

    await inst_parse_post(update.effective_chat.id, context)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global inst_parser_on

    inst_parser_on = False
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text="Coffee brewer stoped. \n"
                                         "Set <b>/start</b> if thirsty.",
                                    parse_mode=constants.ParseMode.HTML)

def main():
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("brew", brew))
    application.add_handler(CommandHandler("stop", stop))
    application.run_polling()

if __name__ == "__main__":
    L = instaloader.Instaloader()
    main()