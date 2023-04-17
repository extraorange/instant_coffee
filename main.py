import instaloader
import asyncio
import requests
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

authname = "mistergpro"
password = "a1s2d3f4g5h6"
token = "6284621532:AAFOmyQEglLwVYgqRAK4tkqqnpd5nYWW7_o"

### INSTALOADER SCRIPT

async def inst_parser(chat_id, context):
    L = instaloader.Instaloader()
    L.login(authname, password)

    if L.context.is_logged_in: 
        print(f"Logged in as @{authname}.")

    account = instaloader.Profile.from_username(L.context, authname)
    followees = [user.username for user in account.get_followees()]
    last_posts_check = {username: None for username in followees}

    while True:
        try:
            for username in followees:
                followee = instaloader.Profile.from_username(L.context, username)
                latest_post = followee.get_posts().__next__()
                if latest_post.shortcode != last_posts_check[username]:
                    
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
            await asyncio.sleep(300)
        except instaloader.exceptions.LoginRequiredException:
            L.login(authname, password)

### TELEGRAM BOT

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global inst_parser_on

    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                   text="Your coffee will begin to drip here.\n"
                                        "Once you don't want me brewing anymore - use <b>/stop</b> command.",
                                   parse_mode=constants.ParseMode.HTML)
    inst_parser_on = True
    while inst_parser_on:
        await inst_parser(update.effective_chat.id, context)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global inst_parser_on

    inst_parser_on = False
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text="Coffee brewer stoped. \n"
                                         "Set <b>/start</b> if thirsty.",
                                    parse_mode=constants.ParseMode.HTML)

def main():
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))
    application.run_polling()

if __name__ == '__main__':
    main()