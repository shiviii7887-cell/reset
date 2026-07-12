"""
RACHIT x RUCHIKA - AI Chat Bot (ChatGPT-style)
- Dual backend: Anthropic (Claude) + OpenAI (ChatGPT) with auto-fallback
- SQLite based per-user conversation memory
- Vision support (send a photo, bot samajhta hai)
- Deploy: Railway (python-telegram-bot v21.6)
"""

import os
import re
import time
import sqlite3
import logging
import base64
import asyncio
import tempfile
from datetime import datetime

import httpx
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

BOT_TOKEN = os.environ["BOT_TOKEN"]

# Primary backend to try first: "anthropic" or "openai"
AI_BACKEND = os.environ.get("AI_BACKEND", "anthropic").lower()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# Image generation (OpenAI only - Anthropic has no image-gen API)
OPENAI_IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1024x1024")

# Railway volume mount path recommended -> set DB_PATH=/data/bot.db and attach a Volume at /data
DB_PATH = os.environ.get("DB_PATH", "bot.db")

# Force-subscribe channel (public channel username without @, e.g. "myupdates")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "")

# Bot's own username (without @) - needed to build referral deep links
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")

# Minutes of unlimited access granted per successful referral
REFERRAL_MINUTES = int(os.environ.get("REFERRAL_MINUTES", "10"))

# Stop allowing NEW messages this many seconds before access actually expires
# (10 min access -> default 60s buffer means last 1 minute is a "cooldown", so
# only ~9 minutes of the window can start new requests, avoiding mid-reply cutoffs)
SEND_CUTOFF_BUFFER_SECONDS = int(os.environ.get("SEND_CUTOFF_BUFFER_SECONDS", "60"))

# Bot owner's Telegram username (without @) - shown when a request is too big for Telegram
OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "")

# Telegram bot API hard limit for uploaded documents is 50MB. We use a safety
# margin well below that since a single AI reply generating this much text
# would already be unusual.
MAX_FILE_BYTES = int(os.environ.get("MAX_FILE_BYTES", str(45 * 1024 * 1024)))

MAX_HISTORY_MESSAGES = int(os.environ.get("MAX_HISTORY_MESSAGES", "20"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "1024"))

DISCLAIMER_TEXT = (
    "⚠️ Zaroori Notice\n\n"
    "Ye bot SIRF education aur user-help ke purpose se bana hai. Illegal, "
    "harmful, ya kisi ko nuksaan pahunchane wale kaam ke liye is bot ka "
    "misuse na karein. Jimmedari se use karein. 🙏"
)

SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    "Tum ek helpful, friendly AI assistant ho jo Hinglish aur English dono me "
    "clearly jawab de sakta hai. User ki har tarah ki madad karo - coding, "
    "writing, doubts, general knowledge, sab kuch. Jawab concise aur useful rakho.\n\n"
    "FILE GENERATION RULE: Agar user koi bot, script, code, ya document maange "
    "jo ek complete file ke roop me dena banta hai (jaise 'ek bot bana do', "
    "'python script chahiye', 'html file do'), to us poore content ko ek "
    "fenced code block me do jiski PEHLI LINE me filename comment ho, is format me:\n"
    "```python\n"
    "# FILENAME: my_bot.py\n"
    "<actual code yahan>\n"
    "```\n"
    "Filename hamesha extension ke saath do (.py, .js, .html, .txt, .json, etc). "
    "Code block ke bahar ek chhota sa explanation likho ki file me kya hai - "
    "poora code chat me dubara mat likhna, sirf code block ke andar ek baar do. "
    "Agar user sirf normal baat kar raha hai (file nahi maang raha), to normal "
    "jawab do, code block ya filename marker use mat karo.\n\n"
    "IMAGE GENERATION RULE: Agar user koi image/photo/wallpaper/drawing banane "
    "ko kahe (jaise 'ek sunset ki image banado', 'draw a cat', 'wallpaper chahiye'), "
    "to reply me exactly ek line is format me do:\n"
    "IMAGE_REQUEST: <ek detailed, descriptive English prompt jo image-generation "
    "model ke liye clear ho>\n"
    "Us line ke bahar ek chhota Hinglish note likho ki image banayi ja rahi hai. "
    "Ye sirf tab use karo jab user genuinely ek image/picture maang raha ho - "
    "normal baaton me kabhi use mat karo.\n\n"
    "BIG PROJECT RULE: Agar user itna bada/complex 'pura project' maange jisme "
    "bohot saari files, thousands of lines, ya poora application (jaise 'poora "
    "ecommerce website bana do', 'is app ka clone bana do', 'poora SaaS product "
    "bana do') chahiye ho, to aisa banane ki koshish MAT karo - koi FILENAME "
    "marker mat do. Iske bajaye politely bata do ki itna bada project ek chat "
    "message me practical nahi hai aur Telegram itni lambi file bhejne ki "
    "permission nahi deta, aur user ko bot owner se directly baat karne ko "
    f"kaho{f' (@{OWNER_USERNAME})' if OWNER_USERNAME else ''} taki custom "
    "development discuss ho sake. Chhote/medium scripts, single-file bots, ya "
    "normal size ke tools is rule me nahi aate - unke liye normal FILE "
    "GENERATION RULE follow karo.\n\n"
    "SAFETY / LEGAL RULE: Kisi bhi illegal, harmful, ya privacy-violating kaam me "
    "madad mat karo - jaise kisi ki personal details (Aadhaar, PAN, phone number, "
    "address) unauthorized tareeke se nikaalna, doosron ka data scrape/leak karna, "
    "stalking, harassment, spam/bulk-unsolicited-messaging tools, hacking, ya kisi "
    "ko target karke fraud karna. Aise request pe politely mana karo aur bata do "
    "ye illegal hai, ye kaam nahi kar sakte - koi legal alternative ho to suggest "
    "karo. Lekin ye mat samjho ki har cheez suspicious hai - genuine, legal "
    "requests me poori tarah madad karo, jaise: exam preparation timelines "
    "(NEET, JEE, etc - clear day-wise/week-wise plan do), kisi scam ka shikar "
    "hua ho to complaint kaise karein iski clear steps do (cybercrime.gov.in, "
    "helpline 1930, bank ko turant inform karna, etc), ya koi legitimate bot/tool "
    "banane me (jaise apne khud ke subscribers ko broadcast message bhejne wala "
    "bot) - iske liye poora code FILENAME marker ke saath do jaise upar bataya.\n\n"
    "HOSTING / FILE-DECODE RULE: Bot/website hosting sikhaane me (Railway, Render, "
    "VPS, environment variables, deployment steps, general concepts) poori tarah "
    "madad karo - ye purely educational hai. LEKIN kisi bhi user-provided encoded, "
    "obfuscated, encrypted, ya minified file/code ko decode, deobfuscate, decrypt, "
    "ya reverse-engineer karne me KABHI madad mat karo (jaise base64/hex se kisi "
    "suspicious payload ko decode karna, obfuscated malware/script samjhna, cracked/"
    "pirated software unlock karna) - chahe user ise 'seekhne' ke liye maange. Aisa "
    "request aaye to politely mana karo aur bata do ye is bot ke scope se bahar hai.",
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("ai_chat_bot")

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_user_id ON messages(user_id)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            access_until INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS referrals (
            referred_id INTEGER PRIMARY KEY,
            referrer_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn


def ensure_user(user_id: int):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO users (user_id, access_until) VALUES (?, 0)", (user_id,))
    conn.commit()
    conn.close()


def get_access_until(user_id: int) -> int:
    conn = get_conn()
    row = conn.execute("SELECT access_until FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row[0] if row else 0


def has_access(user_id: int) -> tuple[bool, int]:
    """Returns (has_access, remaining_seconds). This is the real/hard expiry."""
    remaining = get_access_until(user_id) - int(time.time())
    return remaining > 0, max(remaining, 0)


def can_start_request(user_id: int) -> tuple[bool, int]:
    """
    Returns (can_start, remaining_seconds). Stricter than has_access - blocks
    NEW requests once we're within the last SEND_CUTOFF_BUFFER_SECONDS of the
    access window (e.g. last 1 minute of a 10-minute grant), so an in-flight
    reply always has room to finish before the hard expiry hits.
    """
    remaining = get_access_until(user_id) - int(time.time())
    can_start = remaining > SEND_CUTOFF_BUFFER_SECONDS
    return can_start, max(remaining, 0)


def grant_access_minutes(user_id: int, minutes: int):
    """Stacks access on top of whatever time the user already has left."""
    ensure_user(user_id)
    now = int(time.time())
    current = get_access_until(user_id)
    new_until = max(current, now) + minutes * 60
    conn = get_conn()
    conn.execute("UPDATE users SET access_until = ? WHERE user_id = ?", (new_until, user_id))
    conn.commit()
    conn.close()


def register_referral(referrer_id: int, referred_id: int) -> bool:
    """
    Registers a referral if valid (no self-referral, referred user not
    already credited to someone before). Returns True if newly registered.
    """
    if referrer_id == referred_id:
        return False
    conn = get_conn()
    existing = conn.execute(
        "SELECT 1 FROM referrals WHERE referred_id = ?", (referred_id,)
    ).fetchone()
    if existing:
        conn.close()
        return False
    conn.execute(
        "INSERT INTO referrals (referred_id, referrer_id, created_at) VALUES (?, ?, ?)",
        (referred_id, referrer_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return True


def format_remaining(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}m {secs}s"


def with_expiry_note(user_id: int, text: str) -> str:
    """If access ran out while this reply was being generated, append a note."""
    active, _ = has_access(user_id)
    if active:
        return text
    return (
        f"{text}\n\n"
        f"⏰ Tumhara 10-minute access is beech me khatam ho gaya. "
        f"Agla message bhejne se pehle /refer <code> se access unlock karo."
    )


def add_message(user_id: int, role: str, content: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (user_id, role, content, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_history(user_id: int, limit: int = MAX_HISTORY_MESSAGES):
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    rows.reverse()
    return [{"role": r, "content": c} for r, c in rows]


def reset_history(user_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# AI BACKENDS
# ---------------------------------------------------------------------------

async def call_anthropic(history: list, image_b64: str | None, image_mime: str | None) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY missing")

    messages = []
    for i, m in enumerate(history):
        is_last = i == len(history) - 1
        if is_last and m["role"] == "user" and image_b64:
            content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_mime,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": m["content"]},
            ]
        else:
            content = m["content"]
        messages.append({"role": m["role"], "content": content})

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages", json=payload, headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        parts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        return "\n".join(parts).strip() or "..."


async def call_openai(history: list, image_b64: str | None, image_mime: str | None) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for i, m in enumerate(history):
        is_last = i == len(history) - 1
        if is_last and m["role"] == "user" and image_b64:
            content = [
                {"type": "text", "text": m["content"]},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_mime};base64,{image_b64}"},
                },
            ]
        else:
            content = m["content"]
        messages.append({"role": m["role"], "content": content})

    payload = {
        "model": OPENAI_MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": messages,
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions", json=payload, headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


async def get_ai_reply(history: list, image_b64: str | None = None, image_mime: str | None = None) -> str:
    """Try primary backend first, auto-fallback to the other one if it fails."""
    backends = {"anthropic": call_anthropic, "openai": call_openai}
    order = [AI_BACKEND] + [b for b in backends if b != AI_BACKEND]

    last_err = None
    for name in order:
        try:
            return await backends[name](history, image_b64, image_mime)
        except Exception as e:  # noqa: BLE001
            logger.warning("Backend %s failed: %s", name, e)
            last_err = e
            continue

    raise last_err or RuntimeError("Both AI backends failed")


# ---------------------------------------------------------------------------
# FILE GENERATION (extract code blocks from AI reply -> real files)
# ---------------------------------------------------------------------------

# fallback extension if AI doesn't give a filename marker
LANG_EXT = {
    "python": "py", "py": "py", "javascript": "js", "js": "js",
    "typescript": "ts", "html": "html", "css": "css", "json": "json",
    "bash": "sh", "sh": "sh", "sql": "sql", "yaml": "yaml", "yml": "yaml",
    "txt": "txt", "markdown": "md", "md": "md", "java": "java",
    "c": "c", "cpp": "cpp", "php": "php",
}

CODE_BLOCK_RE = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
FILENAME_MARKER_RE = re.compile(r"^\s*(?:#|//|<!--)\s*FILENAME:\s*(\S+)\s*(?:-->)?\s*\n", re.IGNORECASE)


def extract_files_from_reply(reply_text: str):
    """
    Scans the AI reply for fenced code blocks. If a block starts with a
    FILENAME marker, treats it as a file to send. Returns:
      (clean_text, [(filename, content), ...])
    clean_text has the file code blocks stripped out (short note left instead).
    """
    files = []
    clean_text = reply_text

    for i, match in enumerate(CODE_BLOCK_RE.finditer(reply_text)):
        lang = (match.group(1) or "").lower()
        body = match.group(2)

        fname_match = FILENAME_MARKER_RE.match(body)
        if not fname_match:
            continue  # not marked as a file -> leave as a normal code block in chat

        filename = fname_match.group(1)
        content = body[fname_match.end():]
        files.append((filename, content))
        clean_text = clean_text.replace(match.group(0), f"📎 ({filename} niche bheji hai)")

    return clean_text.strip(), files


def owner_contact_text() -> str:
    who = f"@{OWNER_USERNAME}" if OWNER_USERNAME else "bot owner"
    return (
        "⚠️ Ye file itni badi hai ki Telegram bhejne ki permission nahi deta "
        f"(50MB se zyada file bots bhej nahi sakte). Aise bade/pure projects ke liye "
        f"seedhe {who} se baat karo custom development discuss karne ke liye."
    )


async def send_generated_files(update: Update, context: ContextTypes.DEFAULT_TYPE, files):
    for filename, content in files:
        file_bytes = content.encode("utf-8")
        if len(file_bytes) > MAX_FILE_BYTES:
            await update.message.reply_text(owner_contact_text())
            continue

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_" + filename, delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            with open(tmp_path, "rb") as f:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id, document=f, filename=filename
                )
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to send file %s: %s", filename, e)
            await update.message.reply_text(owner_contact_text())
        finally:
            os.remove(tmp_path)


# ---------------------------------------------------------------------------
# IMAGE GENERATION (OpenAI images API)
# ---------------------------------------------------------------------------

IMAGE_REQUEST_RE = re.compile(r"^\s*IMAGE_REQUEST:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


def extract_image_request(reply_text: str):
    """Finds an IMAGE_REQUEST: <prompt> marker line, strips it from the text."""
    match = IMAGE_REQUEST_RE.search(reply_text)
    if not match:
        return reply_text, None
    prompt = match.group(1).strip()
    clean = IMAGE_REQUEST_RE.sub("🎨 (image bana raha hoon, thoda ruko...)", reply_text, count=1)
    return clean.strip(), prompt


async def generate_image(prompt: str) -> bytes:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing - image generation OpenAI key maangta hai")

    payload = {"model": OPENAI_IMAGE_MODEL, "prompt": prompt, "size": IMAGE_SIZE, "n": 1}
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "content-type": "application/json"}

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.openai.com/v1/images/generations", json=payload, headers=headers
        )
        resp.raise_for_status()
        item = resp.json()["data"][0]

        if "b64_json" in item:
            return base64.b64decode(item["b64_json"])
        if "url" in item:
            img_resp = await client.get(item["url"])
            img_resp.raise_for_status()
            return img_resp.content

        raise RuntimeError("Image API se koi image data nahi mila")


async def send_generated_image(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO
    )
    try:
        image_bytes = await generate_image(prompt)
    except Exception as e:  # noqa: BLE001
        logger.error("Image generation failed: %s", e)
        await update.message.reply_text(
            "⚠️ Image generate nahi ho payi. OPENAI_API_KEY set hai ya nahi check karo."
        )
        return
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=InputFile(image_bytes, filename="generated.png"),
        caption=prompt[:1000],
    )


async def edit_image(source_bytes: bytes, prompt: str) -> bytes:
    """Actually edits the uploaded photo using OpenAI's image edit endpoint."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing - image edit OpenAI key maangta hai")

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    files = {"image": ("input.png", source_bytes, "image/png")}
    data = {"model": OPENAI_IMAGE_MODEL, "prompt": prompt, "size": IMAGE_SIZE}

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.openai.com/v1/images/edits", headers=headers, files=files, data=data
        )
        resp.raise_for_status()
        item = resp.json()["data"][0]

        if "b64_json" in item:
            return base64.b64decode(item["b64_json"])
        if "url" in item:
            img_resp = await client.get(item["url"])
            img_resp.raise_for_status()
            return img_resp.content

        raise RuntimeError("Edit API se koi image data nahi mila")


# ---------------------------------------------------------------------------
# CHANNEL JOIN CHECK + REFERRAL HELPERS
# ---------------------------------------------------------------------------

async def is_channel_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    if not CHANNEL_USERNAME:
        return True  # no channel configured -> skip gate
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:  # noqa: BLE001
        logger.warning("Channel membership check failed: %s", e)
        return False


def join_channel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📢 Channel Join Karo", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton("✅ Maine Join Kar Liya", callback_data="check_join")],
        ]
    )


def referral_link(user_id: int) -> str:
    if BOT_USERNAME:
        return f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    return str(user_id)  # fallback: raw code for manual /refer


async def prompt_for_access(update_or_query, user_id: int):
    """Shown when the user has no active access - tells them how to unlock it."""
    text = (
        "🔒 Chat karne ke liye tumhare paas access nahi hai.\n\n"
        f"Apna referral link kisi dost ko bhejo — jab wo bot join karega, "
        f"tumhe {REFERRAL_MINUTES} minutes ka unlimited access mil jayega:\n"
        f"{referral_link(user_id)}\n\n"
        "Ya agar kisi ne tumhe apna referral CODE diya hai (link nahi), to bhejo:\n"
        "/refer <code>"
    )
    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(text)
    else:
        await update_or_query.edit_message_text(text)


async def prompt_for_cutoff(update: Update, remaining: int):
    """Shown during the last SEND_CUTOFF_BUFFER_SECONDS of an active window."""
    await update.message.reply_text(
        f"⏳ Tumhara access {format_remaining(remaining)} me poora khatam ho raha hai "
        "(last 1 minute me naya message allow nahi hai, taaki koi reply beech me na kate). "
        "Thoda wait karo, phir /refer se naya access lena."
    )


async def gate_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Runs the full access gate: channel-join check, then the 9-minute send
    cutoff, then real access check. Returns True if the handler should proceed.
    """
    user_id = update.effective_user.id

    if not await is_channel_member(context, user_id):
        await show_start_flow(update, context, user_id)
        return False

    can_start, remaining = can_start_request(user_id)
    if not can_start:
        if remaining > 0:
            await prompt_for_cutoff(update, remaining)
        else:
            await prompt_for_access(update, user_id)
        return False

    return True


# ---------------------------------------------------------------------------
# HANDLERS
# ---------------------------------------------------------------------------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    await update.message.reply_text(DISCLAIMER_TEXT)

    # Handle referral deep link: /start ref_<referrer_id>
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0][4:])
            if register_referral(referrer_id, user_id):
                grant_access_minutes(referrer_id, REFERRAL_MINUTES)
                try:
                    await context.bot.send_message(
                        referrer_id,
                        f"🎉 Tumhare referral se koi naya user aaya! "
                        f"Tumhe {REFERRAL_MINUTES} minutes ka unlimited access mila hai.",
                    )
                except Exception:  # noqa: BLE001
                    pass  # referrer may have blocked the bot
        except ValueError:
            pass

    await show_start_flow(update, context, user_id)


async def show_start_flow(update_or_query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Shared by /start and the 'check join' button: gate on channel, then show access status."""
    joined = await is_channel_member(context, user_id)
    if not joined:
        text = (
            "👋 Namaste! Main tumhara AI assistant hoon (RACHIT x RUCHIKA)\n\n"
            "Bot use karne se pehle humara channel join karo, phir neeche button dabao."
        )
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text(text, reply_markup=join_channel_keyboard())
        else:
            await update_or_query.edit_message_text(text, reply_markup=join_channel_keyboard())
        return

    active, remaining = has_access(user_id)
    if active:
        text = (
            f"✅ Channel join confirm! Tumhare paas {format_remaining(remaining)} ka "
            "unlimited access hai. Kuch bhi pucho — coding, doubts, image, file, sab kuch!\n\n"
            f"Tumhara referral link (share karke aur access kamao):\n{referral_link(user_id)}"
        )
    else:
        text = (
            "✅ Channel join confirm!\n\n"
            f"Ab {REFERRAL_MINUTES} minutes ka unlimited chat access unlock karne ke liye:\n"
            f"apna referral link kisi ko bhejo:\n{referral_link(user_id)}\n\n"
            "Ya agar kisi ne tumhe apna code diya hai:\n/refer <code>"
        )

    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(text)
    else:
        await update_or_query.edit_message_text(text)


async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_start_flow(query, context, query.from_user.id)


async def refer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    if not context.args:
        await update.message.reply_text(
            f"Code bhi do! Jaise: /refer 123456\n\nYa apna link share karo: {referral_link(user_id)}"
        )
        return

    code = context.args[0].replace("ref_", "").strip()
    try:
        referrer_id = int(code)
    except ValueError:
        await update.message.reply_text("⚠️ Ye valid referral code nahi lag raha.")
        return

    if referrer_id == user_id:
        await update.message.reply_text("⚠️ Apna khud ka code use nahi kar sakte.")
        return

    if register_referral(referrer_id, user_id):
        grant_access_minutes(referrer_id, REFERRAL_MINUTES)
        grant_access_minutes(user_id, REFERRAL_MINUTES)
        await update.message.reply_text(
            f"🎉 Referral successful! Tumhe {REFERRAL_MINUTES} minutes ka unlimited "
            "access mil gaya. Ab kuch bhi pucho!"
        )
        try:
            await context.bot.send_message(
                referrer_id,
                f"🎉 Tumhare referral code se koi naya user aaya! "
                f"Tumhe bhi {REFERRAL_MINUTES} minutes mile hain.",
            )
        except Exception:  # noqa: BLE001
            pass
    else:
        await update.message.reply_text(
            "⚠️ Ye referral pehle hi use ho chuka hai, ya invalid hai."
        )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Commands:\n"
        "/start - bot start karo / access status dekho\n"
        "/refer <code> - kisi ka referral code use karke access unlock karo\n"
        "/image <prompt> - image generate karo (jaise: /image ek sherni sunset me)\n"
        "/reset - purani chat history clear karo\n"
        "/help - ye message\n\n"
        "Chat karne ke liye channel join + referral access chahiye (/start me link milega). "
        "Access hone ke baad: normal text bhejo, photo bhejo (samajh ke describe karta hoon), "
        "photo caption me 'edit: <kya karna hai>' likho to actually edit karke bhejta hoon, "
        "ya bolo 'ek bot bana do' / 'ek image banado' - file ya naya image bana ke bhej dunga."
    )


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_history(update.effective_user.id)
    await update.message.reply_text("🧹 Memory clear ho gayi. Fresh start!")


async def image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await gate_access(update, context):
        return

    prompt = " ".join(context.args).strip()
    if not prompt:
        await update.message.reply_text(
            "Prompt bhi do! Jaise: /image ek sunset over mountains, realistic style"
        )
        return

    status_msg = await update.message.reply_text("🎨 Image bana raha hoon, thoda ruko...")
    await send_generated_image(update, context, prompt)
    await status_msg.delete()


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if not await gate_access(update, context):
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    status_msg = await update.message.reply_text("🤔 Soch raha hoon...")

    add_message(user_id, "user", text)
    history = get_history(user_id)

    try:
        reply = await get_ai_reply(history)
    except Exception as e:  # noqa: BLE001
        logger.error("AI call failed: %s", e)
        await status_msg.edit_text("⚠️ Abhi AI se connect nahi ho pa raha. Thodi der me try karo.")
        return

    add_message(user_id, "assistant", reply)

    clean_text, image_prompt = extract_image_request(reply)
    clean_text, files = extract_files_from_reply(clean_text)

    if image_prompt:
        await status_msg.edit_text("🎨 Reply taiyar hai, ab image bana raha hoon...")
        await send_generated_image(update, context, image_prompt)
    if files:
        await status_msg.edit_text("📎 Reply taiyar hai, ab file bana raha hoon...")
        await send_generated_files(update, context, files)

    await status_msg.edit_text(with_expiry_note(user_id, clean_text or "✅ Ho gaya."))


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    caption = update.message.caption or "Is image me kya hai? Detail me batao."

    if not await gate_access(update, context):
        return

    photo = update.message.photo[-1]  # highest resolution
    file = await photo.get_file()
    photo_bytes = bytes(await file.download_as_bytearray())

    # Explicit edit trigger: caption starts with "edit:" or "/edit"
    edit_match = re.match(r"^\s*/?edit[:\s]+(.+)$", caption, re.IGNORECASE | re.DOTALL)
    if edit_match:
        edit_prompt = edit_match.group(1).strip()
        status_msg = await update.message.reply_text("🖌️ Photo edit kar raha hoon...")
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO
        )
        try:
            edited_bytes = await edit_image(photo_bytes, edit_prompt)
        except Exception as e:  # noqa: BLE001
            logger.error("Image edit failed: %s", e)
            await status_msg.edit_text(
                "⚠️ Image edit nahi ho payi. OPENAI_API_KEY check karo ya thodi der me try karo."
            )
            return
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=InputFile(edited_bytes, filename="edited.png"),
            caption=f"✅ Edit ho gaya: {edit_prompt[:900]}",
        )
        await status_msg.delete()
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    status_msg = await update.message.reply_text("👀 Photo dekh raha hoon...")

    image_b64 = base64.b64encode(photo_bytes).decode("utf-8")
    image_mime = "image/jpeg"

    add_message(user_id, "user", caption)
    history = get_history(user_id)

    try:
        reply = await get_ai_reply(history, image_b64=image_b64, image_mime=image_mime)
    except Exception as e:  # noqa: BLE001
        logger.error("AI vision call failed: %s", e)
        await status_msg.edit_text("⚠️ Image process nahi ho payi. Thodi der me try karo.")
        return

    add_message(user_id, "assistant", reply)

    clean_text, image_prompt = extract_image_request(reply)
    clean_text, files = extract_files_from_reply(clean_text)

    if image_prompt:
        await status_msg.edit_text("🎨 Reply taiyar hai, ab image bana raha hoon...")
        await send_generated_image(update, context, image_prompt)
    if files:
        await status_msg.edit_text("📎 Reply taiyar hai, ab file bana raha hoon...")
        await send_generated_files(update, context, files)

    await status_msg.edit_text(with_expiry_note(user_id, clean_text or "✅ Ho gaya."))


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Any raw file upload is blocked - this bot doesn't decode/process files."""
    if not await gate_access(update, context):
        return
    await update.message.reply_text(
        "⚠️ Ye bot files receive/decode nahi karta. Koi bhi file upload karke "
        "usse process/decode/unlock karwana is bot ke scope se bahar hai.\n\n"
        "Agar coding ya kisi cheez me help chahiye, seedha text me poocho - "
        "main poori madad karunga."
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Update %s caused error: %s", update, context.error)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    get_conn().close()  # ensure DB + table exist on boot

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("image", image_cmd))
    app.add_handler(CommandHandler("refer", refer_cmd))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    logger.info("Bot starting... primary backend = %s", AI_BACKEND)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
