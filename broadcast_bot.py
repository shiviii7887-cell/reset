import os
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ── CONFIG ────────────────────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN")

CH1_ID   = os.getenv("CH1_ID")    
CH1_LINK = os.getenv("CH1_LINK")  

CH2_ID   = os.getenv("CH2_ID")
CH2_LINK = os.getenv("CH2_LINK")



AUTO_DELETE_SECONDS = 5 * 60  # 5 minutes

# Owner ka set kiya hua message yahan store hoga
current_message = {"text": None}

# ── JOIN CHECK ────────────────────────────────────────────────────────────────

async def is_user_joined(bot, user_id: int) -> bool:
    """Check karta hai ki user teeno channels mein join hai ya nahi."""
    for channel_id in [CH1_ID, CH2_ID]:
        if not channel_id:
            continue
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception:
            return False
    return True

def join_markup() -> InlineKeyboardMarkup:
    """Teen channels ke join buttons + Try Again button."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/ruchika_ownss"),
            
            InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/backupvnsh"),
        ],
        [InlineKeyboardButton("♻️ Try Again", callback_data="verify_join")],
    ])

# ── AUTO DELETE ───────────────────────────────────────────────────────────────

async def schedule_delete(bot, chat_id, message_id, delay=AUTO_DELETE_SECONDS):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

# ── SEND OWNER MESSAGE TO USER ────────────────────────────────────────────────

async def send_owner_message(bot, chat_id):
    if not current_message["text"]:
        return
    sent = await bot.send_message(
        chat_id=chat_id,
        text=current_message["text"],
        parse_mode="Markdown"
    )
    asyncio.create_task(schedule_delete(bot, chat_id, sent.message_id))

# ── START ─────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user   = update.effective_user
    joined = await is_user_joined(context.bot, user.id)

    if not joined:
        await update.message.reply_text(
            f"Hey {user.first_name} 👋\n\n"
            "Please Join All My Update Channels To Use Me! 🔒",
            reply_markup=join_markup()
        )
        return

    # Join ho gaya → owner ka message dikhao
    if current_message["text"]:
        await send_owner_message(context.bot, update.effective_chat.id)
    else:
        await update.message.reply_text(
            f"👋 Hello *{user.first_name}*!\n\n✅ Bot active hai. Owner ka message aane ka wait karo.",
            parse_mode="Markdown"
        )

# ── VERIFY JOIN CALLBACK ──────────────────────────────────────────────────────

async def verify_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    user   = query.from_user
    joined = await is_user_joined(context.bot, user.id)

    if joined:
        await query.answer(
            "☬ ᴀᴜᴛʜᴇɴᴛɪᴄᴀᴛɪᴏɴ ᴄᴏᴍᴘʟᴇᴛᴇ ☬\n🔓 ᴀᴄᴄᴇss ɢʀᴀɴᴛᴇᴅ",
            show_alert=True
        )
        try:
            await query.message.delete()
        except Exception:
            pass

        granted = await context.bot.send_message(
            query.message.chat.id,
            "┏━━━「 ᴀᴄᴄᴇss ɢʀᴀɴᴛᴇᴅ 🎉 」━━━┓\n"
            "┃\n"
            "┃ 🔓 *ʙᴏᴛ sᴜᴄᴄᴇssғᴜʟʟʏ ᴜɴʟᴏᴄᴋᴇᴅ!*\n"
            "┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━┛",
            parse_mode="Markdown"
        )
        asyncio.create_task(
            schedule_delete(context.bot, granted.chat.id, granted.message_id)
        )

        # Owner ka message bhi bhejo
        await send_owner_message(context.bot, query.message.chat.id)

    else:
        await query.answer(
            "❌ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ғᴀɪʟᴇᴅ • ᴊᴏɪɴ ʙᴏᴛʜ ᴄʜᴀɴɴᴇʟs ғɪʀsᴛ",
            show_alert=True
        )

# ── OWNER: SET MESSAGE ────────────────────────────────────────────────────────

async def setmsg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setmsg <text>
    Owner jo message set karega, join karne waale users ko dikhega + 5 min auto-delete
    """
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only owner can use this.")
        return

    if not context.args:
        cur = current_message["text"] or "_(not set)_"
        await update.message.reply_text(
            f"❌ Usage: `/setmsg <message>`\n\n*Current message:*\n{cur}",
            parse_mode="Markdown"
        )
        return

    current_message["text"] = " ".join(context.args)
    await update.message.reply_text(
        f"✅ Message set!\n\n📢 *Preview:*\n{current_message['text']}\n\n"
        "Ab jo bhi user join karega, use yeh message milega aur 5 min baad delete ho jayega.",
        parse_mode="Markdown"
    )

# ── OWNER: CLEAR MESSAGE ──────────────────────────────────────────────────────

async def clearmsg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    current_message["text"] = None
    await update.message.reply_text("🗑️ Message cleared.")

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CallbackQueryHandler(verify_join_callback, pattern="^verify_join$"))
    app.add_handler(CommandHandler("setmsg",   setmsg))
    app.add_handler(CommandHandler("clearmsg", clearmsg))
    
    print("✅ Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
