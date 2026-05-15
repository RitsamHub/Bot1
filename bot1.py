import logging
import os
import sqlite3
import random
import string
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatMember,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import TelegramError

class CBtn(InlineKeyboardButton):
    def __init__(self, text, callback_data=None, url=None, style=None, emoji_id=None, **kwargs):
        super().__init__(text=text, callback_data=callback_data, url=url, **kwargs)
        self._style = style
        self._emoji_id = emoji_id

    def to_dict(self, *args, **kwargs):
        d = super().to_dict(*args, **kwargs)
        if self._style:
            d["style"] = self._style
        if self._emoji_id:
            d["icon_custom_emoji_id"] = self._emoji_id
        return d

# ══════════════════════════════════════════════════
BOT_TOKEN      = "8617578553:AAE4OI--26rJERQeWgaEHOeSwcKRNGjy4fI"
BOT_USERNAME   = "TgElite_Bot"
SUPER_ADMIN_ID = 8064493735
ADMIN_USERNAME = "xvghfsy"

DEVELOPER_ID       = 5260776753
DEVELOPER_USERNAME = "CypherRaaz"
DEVELOPER_NAME     = "𓆩 ＧＯＤ ✘ ＧＥＮＳＨＩＮ ⏤͟͟͞͞『 𓆪』᭄"

# ── Payout Channel ─────────────────────────────
PAYOUT_CHANNEL = "@tg_payout"
PAYOUT_IMAGE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payout.jpeg")

# ── Force Join — exactly 5 channels ───────────
# Format: ("chat_id_or_@username", "invite_url", "Name")
FORCE_CHANNELS = [
    ("-1002401456024",  "https://t.me/+M7kxNIGQYdEwOWY1",  "Channel 1"),
    ("-1003332091257", "https://t.me/+yHYIzPYxgE9mYjVl",       "Channel 2"),
    ("@teamsterniters",  "https://t.me/teamsterniters",   "Channel 3"),
    ("-1002865265233",  "https://t.me/+mC4b8CPNqbIzNGU1",  "Channel 4"),
    ("@OSINTERA_1",  "https://t.me/OSINTERA_1",   "Channel 5"),
]

# ── Optional suggested channels ─────────────────
OPTIONAL_CHANNELS = [
    ("📢 Channel 1", "https://t.me/+v1Jg0WD22sRmY2Vl"),
    ("🎮 Channel 2", "https://t.me/+ofP9DHGpIeo1NjU1"),
    ("💬 Channel 3", "https://t.me/+Esm0C3hIK8I1ZDg1"),
    ("💬 FOLDER ", "https://t.me/addlist/okJLUEyA1CI2YmNl"),
]

START_PHOTO     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img.jpeg")
XP_PER_REFERRAL = 1
WITHDRAW_AT_XP  = 30

EMOJI_ID = "5474667187258006816"

# ══════════════════════════════════════════════════
logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

import time
import os
BOT_VERSION = "v2.0 Elite UI"
BOT_START_TIME = time.time()

import datetime
ADM_LOGS = []
def add_adm_log(uname, text):
    t = datetime.datetime.now().strftime("%H:%M:%S")
    ADM_LOGS.append(f"[{t}] {uname} used {text}")
    if len(ADM_LOGS) > 3:
        ADM_LOGS.pop(0)




# ══════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════
def get_db():
    conn = sqlite3.connect("xpbot.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        role TEXT DEFAULT 'admin', added_by INTEGER,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        xp INTEGER DEFAULT 0, referred_by INTEGER DEFAULT NULL,
        ref_xp_given INTEGER DEFAULT 0,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER,
        referred_id INTEGER, xp_credited INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        code TEXT, status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""INSERT OR IGNORE INTO admins (user_id, username, first_name, role, added_by)
        VALUES (?, ?, ?, 'developer', ?)""",
        (DEVELOPER_ID, DEVELOPER_USERNAME, DEVELOPER_NAME, DEVELOPER_ID))
    c.execute("UPDATE admins SET username=?, first_name=?, role='developer' WHERE user_id=?",
              (DEVELOPER_USERNAME, DEVELOPER_NAME, DEVELOPER_ID))
    c.execute("""INSERT OR IGNORE INTO admins (user_id, username, first_name, role, added_by)
        VALUES (?, ?, 'Super Admin', 'superadmin', ?)""",
        (SUPER_ADMIN_ID, ADMIN_USERNAME, DEVELOPER_ID))
    c.execute("UPDATE admins SET username=? WHERE user_id=? AND role='superadmin'",
              (ADMIN_USERNAME, SUPER_ADMIN_ID))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════
#  ROLE HELPERS
# ══════════════════════════════════════════════════
def get_admin_ids():
    conn = get_db()
    rows = conn.execute("SELECT user_id FROM admins").fetchall()
    conn.close()
    return [r["user_id"] for r in rows]

def get_role(user_id):
    conn = get_db()
    row = conn.execute("SELECT role FROM admins WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row["role"] if row else None

def is_developer(user_id):   return user_id == DEVELOPER_ID
def is_super_admin(user_id): return get_role(user_id) in ("superadmin", "developer")
def is_admin(user_id):       return get_role(user_id) in ("admin", "superadmin", "developer")

def add_admin_db(user_id, username, first_name, added_by):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO admins (user_id, username, first_name, role, added_by) VALUES (?,?,?,'admin',?)",
                 (user_id, username or "", first_name or "", added_by))
    conn.commit(); conn.close()

def remove_admin_db(user_id):
    conn = get_db()
    conn.execute("DELETE FROM admins WHERE user_id=? AND role NOT IN ('superadmin','developer')", (user_id,))
    conn.commit(); conn.close()

def get_all_admins_info():
    conn = get_db()
    rows = conn.execute("""SELECT * FROM admins ORDER BY CASE role
        WHEN 'developer' THEN 1 WHEN 'superadmin' THEN 2 WHEN 'admin' THEN 3 ELSE 4 END""").fetchall()
    conn.close()
    return rows


# ══════════════════════════════════════════════════
#  USER HELPERS
# ══════════════════════════════════════════════════
def get_user(user_id):
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close(); return u

def register_user(user_id, username, first_name, referred_by=None):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, referred_by) VALUES (?,?,?,?)",
                 (user_id, username or "", first_name or "", referred_by))
    if referred_by:
        conn.execute("INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?,?)",
                     (referred_by, user_id))
    conn.commit(); conn.close()

def get_xp(user_id):
    conn = get_db()
    row = conn.execute("SELECT xp FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row["xp"] if row else 0

def add_xp(user_id, amount):
    conn = get_db()
    conn.execute("UPDATE users SET xp = xp + ? WHERE user_id=?", (amount, user_id))
    conn.commit(); conn.close()

def deduct_xp(user_id, amount):
    conn = get_db()
    conn.execute("UPDATE users SET xp = MAX(0, xp - ?) WHERE user_id=?", (amount, user_id))
    conn.commit(); conn.close()

def set_xp(user_id, amount):
    conn = get_db()
    conn.execute("UPDATE users SET xp = ? WHERE user_id=?", (amount, user_id))
    conn.commit(); conn.close()

def get_referral_count(user_id):
    conn = get_db()
    cnt = conn.execute("SELECT COUNT(*) as n FROM referrals WHERE referrer_id=?", (user_id,)).fetchone()["n"]
    conn.close(); return cnt

def get_top_users(limit=10):
    conn = get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY xp DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return rows

def try_credit_referral_xp(referred_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (referred_id,)).fetchone()
    if not user or not user["referred_by"] or user["ref_xp_given"] == 1:
        conn.close(); return None
    referrer_id = user["referred_by"]
    conn.execute("UPDATE users SET xp = xp + ? WHERE user_id=?", (XP_PER_REFERRAL, referrer_id))
    conn.execute("UPDATE users SET ref_xp_given = 1 WHERE user_id=?", (referred_id,))
    conn.execute("UPDATE referrals SET xp_credited = 1 WHERE referrer_id=? AND referred_id=?",
                 (referrer_id, referred_id))
    conn.commit(); conn.close()
    return referrer_id


# ══════════════════════════════════════════════════
#  WITHDRAWAL HELPERS
# ══════════════════════════════════════════════════
def create_withdrawal(user_id):
    code = "".join(random.choices(string.digits, k=4))
    conn = get_db()
    conn.execute("INSERT INTO withdrawals (user_id, code) VALUES (?,?)", (user_id, code))
    conn.commit(); conn.close()
    return code

def get_pending_withdrawal(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM withdrawals WHERE user_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
        (user_id,)).fetchone()
    conn.close(); return row

def get_all_pending_withdrawals():
    conn = get_db()
    rows = conn.execute("""
        SELECT w.*, u.first_name, u.username FROM withdrawals w
        LEFT JOIN users u ON w.user_id = u.user_id
        WHERE w.status = 'pending' ORDER BY w.created_at ASC
    """).fetchall()
    conn.close(); return rows

def verify_withdrawal(user_id, code):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM withdrawals WHERE user_id=? AND code=? AND status='pending'",
        (user_id, code)).fetchone()
    if row:
        conn.execute("UPDATE withdrawals SET status='verified' WHERE id=?", (row["id"],))
        conn.execute("UPDATE users SET xp = MAX(0, xp - ?) WHERE user_id=?", (WITHDRAW_AT_XP, user_id))
        conn.commit()
    conn.close()
    return row is not None

def reject_withdrawal(user_id, code):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM withdrawals WHERE user_id=? AND code=? AND status='pending'",
        (user_id, code)).fetchone()
    if row:
        conn.execute("UPDATE withdrawals SET status='rejected' WHERE id=?", (row["id"],))
        conn.commit()
    conn.close()
    return row is not None


# ══════════════════════════════════════════════════
#  PAYOUT CHANNEL — use plain text caption (no MarkdownV2)
# ══════════════════════════════════════════════════
async def post_payout_announcement(bot, user_first_name, user_username, user_id, code):
    uname_display = f"@{user_username}" if user_username else f"ID {user_id}"
    now = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Plain text caption — NO markdown, no special chars to escape
    caption = (
        "💸 WITHDRAWAL SUCCESS!\n\n"
        f"✅ Withdrawal Completed!\n\n"
        f"👤 User   : {user_first_name}\n"
        f"🔗 Handle : {uname_display}\n"
        f"💰 Amount : {WITHDRAW_AT_XP} XP\n"
        f"⏰ Time   : {now}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Earn XP & Withdraw Too!\n"
        f"▶ @{BOT_USERNAME}"
    )

    log.info(f"[PAYOUT] Channel: {PAYOUT_CHANNEL}")
    log.info(f"[PAYOUT] Image  : {PAYOUT_IMAGE}")
    log.info(f"[PAYOUT] Exists : {os.path.isfile(PAYOUT_IMAGE)}")

    try:
        if os.path.isfile(PAYOUT_IMAGE):
            with open(PAYOUT_IMAGE, "rb") as img:
                await bot.send_photo(
                    chat_id=PAYOUT_CHANNEL,
                    photo=img,
                    caption=caption
                    # No parse_mode — plain text, zero risk of formatting error
                )
            log.info("[PAYOUT] ✅ Photo + caption sent!")
        else:
            log.warning(f"[PAYOUT] Image not found: {PAYOUT_IMAGE}")
            log.warning("[PAYOUT] Place payout.jpeg next to bot1.py in D:\\projects\\")
            await bot.send_message(chat_id=PAYOUT_CHANNEL, text=caption)
            log.info("[PAYOUT] ✅ Text-only sent (no image found)")
    except Exception as e:
        log.error(f"[PAYOUT] Error: {e}")
        # Last resort
        try:
            await bot.send_message(
                chat_id=PAYOUT_CHANNEL,
                text=f"Withdrawal: {user_first_name} ({uname_display}) — {WITHDRAW_AT_XP} XP — {now}"
            )
            log.info("[PAYOUT] ✅ Minimal fallback sent")
        except Exception as e2:
            log.error(f"[PAYOUT] All failed: {e2}")
            log.error("[PAYOUT] Is bot admin in the payout channel?")


# ══════════════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════════════
def xp_progress_bar(xp, total=None):
    total = total or WITHDRAW_AT_XP
    filled = int(min(xp, total) / total * 10)
    return f"[{'█'*filled}{'░'*(10-filled)}] {int(min(xp,total)/total*100)}%"

def ref_link(user_id):
    return f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"

def wa_share_link(user_id):
    return f"https://wa.me/?text=🎮 Join XP Earn Bot and earn real rewards!%0A%0A👉 {ref_link(user_id)}"


# ══════════════════════════════════════════════════
#  HOME KEYBOARD — 2-column layout throughout
# ══════════════════════════════════════════════════
def home_keyboard(user_id):
    return InlineKeyboardMarkup([
        # Row 1
        [CBtn("📊 My Profile",       callback_data="profile", style="primary"),
         CBtn("👥 Referral Link",    callback_data="refer", style="success")],
        # Row 2
        [CBtn("📤 Share Telegram",
             url=f"https://t.me/share/url?url={ref_link(user_id)}&text=Join+XP+Earn+Bot!", style="primary"),
         CBtn("💬 Share WhatsApp",   url=wa_share_link(user_id), style="success")],
        # Row 3
        [CBtn("💸 Withdraw XP",      callback_data="withdraw", style="danger"),
         CBtn("🏆 Leaderboard",      callback_data="leaderboard", style="primary")],
        # Row 4
        [CBtn("ℹ️ Help",             callback_data="help", style="primary"),
         CBtn("🔴 Contact Admin",    url=f"https://t.me/{ADMIN_USERNAME}", style="danger")],
        # Row 5 — Developer (full width)
        [CBtn(
            "👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ ⚡ ʙᴏᴛ ʙᴀɴᴡᴀɴᴀ ʜᴏ? 🤙",
            url=f"https://t.me/{DEVELOPER_USERNAME}", style="primary"
        )],
    ])


# ══════════════════════════════════════════════════
#  JOIN KEYBOARD — Alternating columns
# ══════════════════════════════════════════════════
def join_keyboard():
    rows = []

    fc_buttons = [
        CBtn("💫Rᴇᴅɪʀᴇᴄᴛ💫", url=url, style="primary")
        for _, url, _ in FORCE_CHANNELS
    ]
    
    opt_buttons = [
        CBtn(name, url=url, style="success")
        for name, url in OPTIONAL_CHANNELS
    ]

    all_buttons = fc_buttons + opt_buttons
    random.shuffle(all_buttons)

    # Place them 2 per row
    for i in range(0, len(all_buttons), 2):
        rows.append(all_buttons[i:i+2])

    # Continue button
    rows.append([CBtn("🔓 Continue", callback_data="check_join", style="danger")])
    return InlineKeyboardMarkup(rows)


async def smart_edit(query, text, reply_markup=None, parse_mode="Markdown"):
    try:
        if query.message and query.message.photo:
            await query.edit_message_caption(
                caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await query.edit_message_text(
                text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await query.message.reply_text(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode)


# ══════════════════════════════════════════════════
#  FORCE JOIN CHECKER (only FORCE_CHANNELS)
# ══════════════════════════════════════════════════
async def user_has_joined_all(bot, user_id: int) -> bool:
    for chat_id, _, name in FORCE_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in (ChatMember.LEFT, ChatMember.BANNED):
                return False
        except TelegramError as e:
            log.warning(f"Could not check {chat_id}: {e}")
            return False
    return True

async def send_force_join(update: Update):
    text = (
        "🔐 *Access Locked*\n\n"
        "To use this bot, join the channels below\n"
        "then press *Continue*."
    )
    kb = join_keyboard()
    if update.callback_query:
        try:
            await smart_edit(update.callback_query, text, reply_markup=kb)
        except Exception:
            await update.effective_chat.send_message(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await update.effective_chat.send_message(text, reply_markup=kb, parse_mode="Markdown")

async def gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if is_admin(user_id):
        return True
    if not await user_has_joined_all(context.bot, user_id):
        if update.callback_query:
            await update.callback_query.answer()
        await send_force_join(update)
        return False
    return True


# ══════════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    user_id  = user.id
    args     = context.args
    existing = get_user(user_id)
    referred_by = None

    if not existing:
        if args and args[0].startswith("ref_"):
            try:
                rid = int(args[0].replace("ref_", ""))
                if rid != user_id and get_user(rid):
                    referred_by = rid
            except ValueError:
                pass
        register_user(user_id, user.username, user.first_name, referred_by)

        uname    = f"@{user.username}" if user.username else "No username"
        ref_info = ""
        if referred_by:
            ref_u    = get_user(referred_by)
            ref_name = ref_u["first_name"] if ref_u else str(referred_by)
            ref_info = f"\n🔗 Referred by: *{ref_name}* (`{referred_by}`)"

        admin_msg = (
            "🔔 *New User Alert!*\n──────────────────────\n"
            f"👤 Name     : *{user.first_name}*\n"
            f"🔗 Username : {uname}\n"
            f"🆔 User ID  : `{user_id}`\n"
            f"📅 Time     : {datetime.datetime.now().strftime('%d %b %Y, %I:%M %p')}"
            f"{ref_info}"
        )
        for aid in get_admin_ids():
            try:
                await context.bot.send_message(aid, admin_msg, parse_mode="Markdown")
            except Exception:
                pass

    if not is_admin(user_id) and not await user_has_joined_all(context.bot, user_id):
        await send_force_join(update)
        return

    referrer_id = try_credit_referral_xp(user_id)
    if referrer_id:
        new_xp = get_xp(referrer_id)
        try:
            await context.bot.send_message(
                referrer_id,
                f"🎉 *+{XP_PER_REFERRAL} XP Earned!*\n\n"
                f"👤 *{user.first_name}* joined via your link!\n"
                f"💰 Your XP is now: *{new_xp}*\n{xp_progress_bar(new_xp)}",
                parse_mode="Markdown")
        except Exception:
            pass

    xp = get_xp(user_id)
    caption = (
        "╔══════════════════════════╗\n"
        "║     ⚡  XP EARN BOT  ⚡    ║\n"
        "╚══════════════════════════╝\n\n"
        f"Welcome, *{user.first_name}*! 👋\n\n"
        "📌 *How It Works:*\n"
        f"┣ 🔗 Share your referral link\n"
        f"┣ ✅ When they join → *+{XP_PER_REFERRAL} XP*\n"
        f"┣ 💎 Reach *{WITHDRAW_AT_XP} XP* → Withdraw\n"
        f"┗ 📤 Share on Telegram & WhatsApp!\n\n"
        "──────────────────────────\n"
        f"💰 *Your XP : {xp}*\n"
        f"{xp_progress_bar(xp)}  ({xp} / {WITHDRAW_AT_XP})"
    )

    if os.path.isfile(START_PHOTO):
        with open(START_PHOTO, "rb") as f:
            await update.effective_chat.send_photo(
                photo=f, caption=caption,
                reply_markup=home_keyboard(user_id), parse_mode="Markdown")
    else:
        await update.effective_chat.send_message(
            caption, reply_markup=home_keyboard(user_id), parse_mode="Markdown")


# ══════════════════════════════════════════════════
#  CHECK JOIN CALLBACK
# ══════════════════════════════════════════════════
async def cb_check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    user    = query.from_user
    user_id = user.id

    if not await user_has_joined_all(context.bot, user_id):
        await query.answer("❌ Join all channels first!", show_alert=True)
        return

    await query.answer("✅ Verified!")

    referrer_id = try_credit_referral_xp(user_id)
    if referrer_id:
        new_xp = get_xp(referrer_id)
        try:
            await context.bot.send_message(
                referrer_id,
                f"🎉 *+{XP_PER_REFERRAL} XP Earned!*\n\n"
                f"👤 *{user.first_name}* just joined all channels!\n"
                f"💰 Your XP: *{new_xp}*\n{xp_progress_bar(new_xp)}",
                parse_mode="Markdown")
        except Exception:
            pass

    xp = get_xp(user_id)
    await smart_edit(query,
        "╔══════════════════════════╗\n"
        "║     ⚡  XP EARN BOT  ⚡    ║\n"
        "╚══════════════════════════╝\n\n"
        f"✅ *Verified! Welcome, {user.first_name}!*\n\n"
        f"💰 *Your XP : {xp}*\n"
        f"{xp_progress_bar(xp)}  ({xp} / {WITHDRAW_AT_XP})",
        reply_markup=home_keyboard(user_id))


# ══════════════════════════════════════════════════
#  ALL CALLBACKS
# ══════════════════════════════════════════════════
async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    data    = query.data
    user    = query.from_user
    user_id = user.id

    if data == "check_join":
        await cb_check_join(update, context); return
    if data == "noop":
        await query.answer(); return

    if not await gate(update, context):
        return

    await query.answer()

    # ── HOME ──────────────────────────────────────
    if data == "home":
        xp = get_xp(user_id)
        await smart_edit(query,
            "╔══════════════════════════╗\n"
            "║     ⚡  XP EARN BOT  ⚡    ║\n"
            "╚══════════════════════════╝\n\n"
            f"Welcome back, *{user.first_name}*! 👋\n\n"
            f"💰 *Your XP : {xp}*\n"
            f"{xp_progress_bar(xp)}  ({xp} / {WITHDRAW_AT_XP})",
            reply_markup=home_keyboard(user_id))

    # ── PROFILE ───────────────────────────────────
    elif data == "profile":
        db_u  = get_user(user_id)
        xp    = db_u["xp"] if db_u else 0
        refs  = get_referral_count(user_id)
        uname = f"@{db_u['username']}" if db_u and db_u["username"] else "—"
        need  = max(0, WITHDRAW_AT_XP - xp)
        await smart_edit(query,
            "╔══════════════════════════╗\n"
            "║       📊  MY PROFILE      ║\n"
            "╠══════════════════════════╣\n"
            f"║  👤 Name      : *{user.first_name}*\n"
            f"║  🔗 Username  : {uname}\n"
            f"║  🆔 User ID   : `{user_id}`\n║\n"
            f"║  💰 XP        : *{xp}*\n"
            f"║  {xp_progress_bar(xp)}\n"
            f"║  🎯 Need      : *{need} more XP*\n║\n"
            f"║  👥 Referrals : *{refs}*\n"
            "╚══════════════════════════╝",
            reply_markup=InlineKeyboardMarkup([
                [CBtn("🔙 Back to Home", callback_data="home", style="danger")]
            ]))

    # ── REFER ─────────────────────────────────────
    elif data == "refer":
        xp   = get_xp(user_id)
        refs = get_referral_count(user_id)
        link = ref_link(user_id)
        await smart_edit(query,
            f"👥 *Your Referral Link*\n\n`{link}`\n\n"
            f"📊 *Your Stats:*\n"
            f"┣ 👥 Total Referrals : *{refs}*\n"
            f"┣ 💰 Your XP         : *{xp}*\n"
            f"┗ 📊 Progress        : {xp_progress_bar(xp)}\n\n"
            "⚠️ *Note:* XP credited only after friend joins *all channels.*",
            reply_markup=InlineKeyboardMarkup([
                [CBtn("📤 Telegram",
                     url=f"https://t.me/share/url?url={link}&text=Join+XP+Bot!", style="primary"),
                 InlineKeyboardButton("💬 WhatsApp", url=wa_share_link(user_id))],
                [CBtn("🔙 Back to Home", callback_data="home", style="danger")]
            ]))

    # ── WITHDRAW ──────────────────────────────────
    elif data == "withdraw":
        xp = get_xp(user_id)
        if xp < WITHDRAW_AT_XP:
            await query.answer("❌ Not enough XP!", show_alert=False)
            await smart_edit(query,
                f"❌ *Not Enough XP!*\n\nYou have *{xp} XP*.\nNeed *{WITHDRAW_AT_XP - xp} more XP* to withdraw.\n{xp_progress_bar(xp)}",
                reply_markup=InlineKeyboardMarkup([[CBtn("🔙 Back", callback_data="home", style="danger")]]))
            return
        if get_pending_withdrawal(user_id):
            p = get_pending_withdrawal(user_id)
            await query.answer(f"⏳ Pending! Code: {p['code']}", show_alert=True); return
        await smart_edit(query,
            f"💸 *Confirm Withdrawal*\n\n"
            f"💰 Current XP    : *{xp}*\n"
            f"📤 XP deducted   : *{WITHDRAW_AT_XP}*\n"
            f"💵 Remaining XP  : *{xp - WITHDRAW_AT_XP}*\n\n"
            "A *4-digit code* will be generated.\n"
            "Show it to the admin to claim reward.",
            reply_markup=InlineKeyboardMarkup([
                [CBtn("✅ Confirm", callback_data="confirm_wd", style="success"),
                 CBtn("❌ Cancel",  callback_data="home", style="danger")]
            ]))

    # ── CONFIRM WITHDRAWAL ────────────────────────
    elif data == "confirm_wd":
        xp = get_xp(user_id)
        if xp < WITHDRAW_AT_XP:
            await query.answer("❌ Not enough XP!", show_alert=True); return
        if get_pending_withdrawal(user_id):
            await query.answer("Already pending!", show_alert=True); return

        code  = create_withdrawal(user_id)
        db_u  = get_user(user_id)
        uname = f"@{db_u['username']}" if db_u and db_u["username"] else "No username"

        await smart_edit(query,
            "╔══════════════════════════╗\n"
            "║   💸  WITHDRAWAL REQUEST   ║\n"
            "╚══════════════════════════╝\n\n"
            "✅ *Your withdrawal code is ready!*\n\n"
            f"🔑 *Your Code :* `{code}`\n\n"
            "📋 *Next Steps:*\n"
            f"1️⃣ DM @{ADMIN_USERNAME} using button below\n"
            "2️⃣ Tell them you want to withdraw\n"
            f"3️⃣ Share your code : `{code}`\n"
            "4️⃣ Admin verifies & sends reward ✅\n\n"
            "⚠️ *Do NOT share this code with anyone else!*",
            reply_markup=InlineKeyboardMarkup([
                [CBtn(f"💬 DM @{ADMIN_USERNAME}",
                     url=f"https://t.me/{ADMIN_USERNAME}", style="primary")],
                [CBtn("🏠 Back to Home", callback_data="home", style="danger")]
            ]))

        for aid in get_admin_ids():
            try:
                await context.bot.send_message(aid,
                    "💸 *New Withdrawal Request!*\n──────────────────────────\n"
                    f"👤 Name     : *{db_u['first_name']}*\n"
                    f"🔗 Username : {uname}\n"
                    f"🆔 User ID  : `{user_id}`\n"
                    f"🔑 Code     : `{code}`\n"
                    f"💰 XP       : {WITHDRAW_AT_XP}\n"
                    f"⏰ Time     : {datetime.datetime.now().strftime('%d %b %Y, %I:%M %p')}\n"
                    "──────────────────────────\n"
                    f"✅ `/verify {user_id} {code}`\n"
                    f"❌ `/reject {user_id} {code}`",
                    parse_mode="Markdown")
            except Exception:
                pass

    # ── LEADERBOARD ───────────────────────────────
    elif data == "leaderboard":
        top    = get_top_users(10)
        medals = ["🥇","🥈","🥉"] + ["🏅"]*7
        text   = "🏆 *Top 10 Leaderboard*\n──────────────────────\n"
        for i, row in enumerate(top):
            text += f"{medals[i]} *{(row['first_name'] or 'User')[:15]}* — {row['xp']} XP\n"
        text += f"\n──────────────────────\n💰 *Your XP :* {get_xp(user_id)}"
        await smart_edit(query, text,
            reply_markup=InlineKeyboardMarkup([
                [CBtn("🔙 Back to Home", callback_data="home", style="danger")]
            ]))

    # ── HELP ──────────────────────────────────────
    elif data == "help":
        await smart_edit(query,
            "ℹ️ *XP Earn Bot — Help*\n══════════════════════\n\n"
            "📌 *Commands:*\n"
            "• /start — Open main menu\n"
            "• /profile — View your profile\n"
            "• /refer — Get your referral link\n"
            "• /balance — Check your XP\n"
            "• /withdraw — Withdraw your XP\n"
            "• /leaderboard — Top 10 users\n\n"
            "══════════════════════\n"
            "🔗 *Referral Rules:*\n"
            "• Share your unique link\n"
            f"• Friend must join all *{len(FORCE_CHANNELS)} channels*\n"
            f"• You get *+{XP_PER_REFERRAL} XP* after they verify\n\n"
            "══════════════════════\n"
            "💸 *Withdrawal Process:*\n"
            f"1. Collect *{WITHDRAW_AT_XP} XP*\n"
            "2. Press Withdraw\n"
            "3. Get your 4-digit code\n"
            f"4. DM @{ADMIN_USERNAME} with the code\n"
            "5. Admin verifies & sends reward ✅",
            reply_markup=InlineKeyboardMarkup([
                [CBtn("🔙 Back to Home", callback_data="home", style="danger")]
            ]))


# ══════════════════════════════════════════════════
#  USER COMMANDS
# ══════════════════════════════════════════════════
async def cmd_balance(update, context):
    if not await gate(update, context): return
    xp = get_xp(update.effective_user.id)
    await update.message.reply_text(
        f"💰 *Your XP Balance*\n\nXP : *{xp}* / {WITHDRAW_AT_XP}\n{xp_progress_bar(xp)}\n\n"
        + ("✅ You can withdraw! /withdraw" if xp >= WITHDRAW_AT_XP
           else f"⏳ Need *{WITHDRAW_AT_XP - xp} more XP*."),
        parse_mode="Markdown")

async def cmd_profile(update, context):
    if not await gate(update, context): return
    user  = update.effective_user
    db_u  = get_user(user.id)
    xp    = db_u["xp"] if db_u else 0
    refs  = get_referral_count(user.id)
    uname = f"@{db_u['username']}" if db_u and db_u["username"] else "—"
    await update.message.reply_text(
        "╔══════════════════════════╗\n║       📊  MY PROFILE      ║\n╠══════════════════════════╣\n"
        f"║  👤 Name      : *{user.first_name}*\n║  🔗 Username  : {uname}\n║  🆔 User ID   : `{user.id}`\n║\n"
        f"║  💰 XP        : *{xp}*\n║  {xp_progress_bar(xp)}\n║\n║  👥 Referrals : *{refs}*\n╚══════════════════════════╝",
        parse_mode="Markdown")

async def cmd_refer(update, context):
    if not await gate(update, context): return
    user = update.effective_user
    link = ref_link(user.id)
    await update.message.reply_text(
        f"👥 *Your Referral Link:*\n\n`{link}`\n\n"
        f"When your friend joins all *{len(FORCE_CHANNELS)} channels*, you earn *+{XP_PER_REFERRAL} XP*!",
        parse_mode="Markdown")

async def cmd_leaderboard(update, context):
    if not await gate(update, context): return
    top    = get_top_users(10)
    medals = ["🥇","🥈","🥉"] + ["🏅"]*7
    text   = "🏆 *Top 10 Leaderboard*\n──────────────────────\n"
    for i, row in enumerate(top):
        text += f"{medals[i]} *{(row['first_name'] or 'User')[:15]}* — {row['xp']} XP\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_withdraw(update, context):
    if not await gate(update, context): return
    xp = get_xp(update.effective_user.id)
    if xp < WITHDRAW_AT_XP:
        await update.message.reply_text(
            f"❌ *Not Enough XP!*\n\nYou have *{xp} XP*.\nNeed *{WITHDRAW_AT_XP - xp} more XP*.\n{xp_progress_bar(xp)}",
            parse_mode="Markdown"); return
    await update.message.reply_text(
        f"💸 *Withdraw Confirmation*\n\nYou have *{xp} XP*. Confirm?",
        reply_markup=InlineKeyboardMarkup([
            [CBtn("✅ Confirm", callback_data="confirm_wd", style="success"),
             CBtn("❌ Cancel",  callback_data="home", style="danger")]
        ]), parse_mode="Markdown")


# ══════════════════════════════════════════════════
#  ADMIN COMMANDS
# ══════════════════════════════════════════════════
async def cmd_pending(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not an admin!"); return
    rows = get_all_pending_withdrawals()
    if not rows:
        await update.message.reply_text("✅ *No pending withdrawals!* 🎉", parse_mode="Markdown"); return
    text = f"⏳ *Pending Withdrawals ({len(rows)})*\n══════════════════════\n\n"
    for i, row in enumerate(rows, 1):
        uname = f"@{row['username']}" if row["username"] else "No username"
        text += (
            f"*{i}.* 👤 *{row['first_name'] or 'User'}* ({uname})\n"
            f"   🆔 `{row['user_id']}`  🔑 `{row['code']}`\n"
            f"   ⏰ {row['created_at'][:16]}\n"
            f"   ✅ `/verify {row['user_id']} {row['code']}`\n"
            f"   ❌ `/reject {row['user_id']} {row['code']}`\n\n"
        )
    if len(text) > 4000:
        text = text[:4000] + "\n_...more entries exist_"
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_verify(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not an admin!"); return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/verify <user_id> <code>`", parse_mode="Markdown"); return
    try:
        uid = int(context.args[0]); code = context.args[1].strip()
    except ValueError:
        await update.message.reply_text("❌ Invalid input!"); return
    msg = await update.message.reply_text("🔍 Verifying...")
    if verify_withdrawal(uid, code):
        await msg.edit_text(
            f"✅ *Verified!*\n🆔 `{uid}` | 🔑 `{code}` | 💰 {WITHDRAW_AT_XP} XP deducted.",
            parse_mode="Markdown")
        db_u    = get_user(uid)
        u_name  = db_u["first_name"] if db_u else "User"
        u_uname = db_u["username"]   if db_u else ""
        try:
            await context.bot.send_message(uid,
                "╔══════════════════════════╗\n║  ✅  WITHDRAWAL VERIFIED!  ║\n╚══════════════════════════╝\n\n"
                f"🔑 Code `{code}` verified!\nAdmin will send your reward shortly. 🎁",
                parse_mode="Markdown")
        except Exception:
            await update.message.reply_text("⚠️ Could not DM the user.")
        await post_payout_announcement(context.bot, u_name, u_uname, uid, code)
    else:
        await msg.edit_text(
            f"❌ *Failed!* Code `{code}` for `{uid}` invalid or already used.",
            parse_mode="Markdown")

async def cmd_reject(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not an admin!"); return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/reject <user_id> <code>`", parse_mode="Markdown"); return
    try:
        uid = int(context.args[0]); code = context.args[1].strip()
    except ValueError:
        await update.message.reply_text("❌ Invalid input!"); return
    if reject_withdrawal(uid, code):
        await update.message.reply_text(f"❌ *Rejected!*\n🆔 `{uid}` | 🔑 `{code}`", parse_mode="Markdown")
        try:
            await context.bot.send_message(uid,
                f"❌ *Withdrawal Rejected!*\n\nCode `{code}` rejected by admin.\n"
                "Contact admin if you think this is a mistake.", parse_mode="Markdown")
        except Exception: pass
    else:
        await update.message.reply_text(
            f"❌ Not found. Code `{code}` for `{uid}` invalid/processed.", parse_mode="Markdown")

async def cmd_addadmin(update, context):
    if not is_super_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only Super Admin or Developer!"); return
    if not context.args:
        await update.message.reply_text("Usage: `/addadmin <user_id>`", parse_mode="Markdown"); return
    try:
        new_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!"); return
    if new_id == DEVELOPER_ID:
        await update.message.reply_text("❌ Developer is already above all!"); return
    uname = fname = ""
    try:
        chat = await context.bot.get_chat(new_id)
        uname = chat.username or ""; fname = chat.first_name or ""
    except Exception: pass
    add_admin_db(new_id, uname, fname, update.effective_user.id)
    display = f"@{uname}" if uname else str(new_id)
    await update.message.reply_text(f"✅ *{display}* added as admin! ID: `{new_id}`", parse_mode="Markdown")
    try:
        await context.bot.send_message(new_id,
            "🛡️ *You've been made an Admin!*\n\n"
            "• `/pending` • `/verify` • `/reject`\n"
            "• `/addxp` • `/broadcast` • `/adminstats`",
            parse_mode="Markdown")
    except Exception: pass

async def cmd_removeadmin(update, context):
    if not is_super_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only Super Admin or Developer!"); return
    if not context.args:
        await update.message.reply_text("Usage: `/removeadmin <user_id>`", parse_mode="Markdown"); return
    try:
        rem_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!"); return
    if rem_id == DEVELOPER_ID:
        await update.message.reply_text("❌ Cannot remove Developer!"); return
    if rem_id == SUPER_ADMIN_ID and not is_developer(update.effective_user.id):
        await update.message.reply_text("❌ Only Developer can remove Super Admin!"); return
    remove_admin_db(rem_id)
    await update.message.reply_text(f"✅ `{rem_id}` removed.", parse_mode="Markdown")

async def cmd_admins(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not an admin!"); return
    rows = get_all_admins_info()
    text = "🛡️ *Admin List*\n──────────────────\n"
    for r in rows:
        icon  = {"developer":"👨‍💻 Developer","superadmin":"👑 Super Admin"}.get(r["role"],"🛡️ Admin")
        uname = f"@{r['username']}" if r["username"] else "—"
        text += f"{icon}\n  *{r['first_name'] or '—'}* | {uname} | `{r['user_id']}`\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_addxp(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not an admin!"); return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/addxp <user_id> <amount>`", parse_mode="Markdown"); return
    try:
        uid = int(context.args[0]); amt = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid input!"); return
    if amt <= 0:
        await update.message.reply_text("❌ Amount > 0!"); return
    add_xp(uid, amt); new_xp = get_xp(uid)
    await update.message.reply_text(f"✅ +*{amt} XP* to `{uid}`. New: *{new_xp} XP*", parse_mode="Markdown")
    try:
        await context.bot.send_message(uid,
            f"🎁 *{amt} XP Added!*\n💰 New balance: *{new_xp} XP*\n{xp_progress_bar(new_xp)}",
            parse_mode="Markdown")
    except Exception: pass

async def cmd_setxp(update, context):
    if not is_developer(update.effective_user.id):
        await update.message.reply_text("❌ Developer only!"); return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/setxp <user_id> <amount>`", parse_mode="Markdown"); return
    try:
        uid = int(context.args[0]); amt = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid input!"); return
    set_xp(uid, amt)
    await update.message.reply_text(f"⚙️ XP set to *{amt}* for `{uid}`.", parse_mode="Markdown")

async def cmd_deductxp(update, context):
    if not is_developer(update.effective_user.id):
        await update.message.reply_text("❌ Developer only!"); return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/deductxp <user_id> <amount>`", parse_mode="Markdown"); return
    try:
        uid = int(context.args[0]); amt = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid input!"); return
    deduct_xp(uid, amt)
    await update.message.reply_text(f"⚙️ -{amt} XP from `{uid}`. New: *{get_xp(uid)}*", parse_mode="Markdown")

async def cmd_broadcast(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not an admin!"); return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Usage: `/broadcast <message>`", parse_mode="Markdown"); return
    conn  = get_db()
    users = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    status = await update.message.reply_text(f"📡 Sending to {len(users)} users...")
    sent = failed = 0
    for u in users:
        try:
            await context.bot.send_message(u["user_id"], f"📢 *Announcement*\n\n{text}", parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
    await status.edit_text(f"📡 Done!\n✅ Sent: {sent} | ❌ Failed: {failed}", parse_mode="Markdown")

async def cmd_adminstats(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not an admin!"); return
    conn  = get_db()
    t_usr = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    t_xp  = conn.execute("SELECT COALESCE(SUM(xp),0) as s FROM users").fetchone()["s"]
    t_ref = conn.execute("SELECT COUNT(*) as c FROM referrals").fetchone()["c"]
    p_wd  = conn.execute("SELECT COUNT(*) as c FROM withdrawals WHERE status='pending'").fetchone()["c"]
    d_wd  = conn.execute("SELECT COUNT(*) as c FROM withdrawals WHERE status='verified'").fetchone()["c"]
    r_wd  = conn.execute("SELECT COUNT(*) as c FROM withdrawals WHERE status='rejected'").fetchone()["c"]
    t_adm = conn.execute("SELECT COUNT(*) as c FROM admins").fetchone()["c"]
    conn.close()
    await update.message.reply_text(
        "📊 *Bot Statistics*\n══════════════════\n"
        f"👥 Total Users         : *{t_usr}*\n"
        f"💰 Total XP in bot     : *{t_xp}*\n"
        f"🔗 Total Referrals     : *{t_ref}*\n"
        f"⏳ Pending Withdrawals : *{p_wd}*\n"
        f"✅ Done Withdrawals    : *{d_wd}*\n"
        f"❌ Rejected            : *{r_wd}*\n"
        f"🛡️ Total Admins        : *{t_adm}*\n"
        "══════════════════\n"
        "• `/pending` • `/verify` • `/reject`\n"
        "• `/addadmin` • `/removeadmin` • `/admins`\n"
        "• `/addxp` • `/broadcast` • `/adminstats`\n"
        "👨‍💻 Dev: `/setxp` `/deductxp`",
        parse_mode="Markdown")


# ══════════════════════════════════════════════════
#  CONSOLE DASHBOARD (ASYNC LOOP)
# ══════════════════════════════════════════════════
import asyncio

async def console_dashboard_loop(application):
    while True:
        try:
            t0 = time.time()
            await application.bot.get_me()
            ping = f"{round((time.time() - t0) * 1000)}ms"
        except Exception:
            ping = "ERR"

        uptime_s = int(time.time() - BOT_START_TIME)
        uptime_h = uptime_s // 3600
        uptime_m = (uptime_s % 3600) // 60

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM users")
        t_users = c.fetchone()["cnt"]

        c.execute("SELECT COUNT(*) as cnt FROM admins")
        t_admins = c.fetchone()["cnt"]

        c.execute("SELECT COALESCE(SUM(xp), 0) as s FROM users")
        t_xp = c.fetchone()["s"]

        c.execute("SELECT COUNT(*) as cnt FROM users WHERE DATE(joined_at) = DATE('now')")
        daily = c.fetchone()["cnt"]

        conn.close()

        C_RST = '\033[0m'; C_RED = '\033[91m'; C_GRN = '\033[92m'
        C_YEL = '\033[93m'; C_BLU = '\033[94m'; C_MAG = '\033[95m'; C_CYN = '\033[96m'

        os.system('cls' if os.name == 'nt' else 'clear')
        
        giant_art = f"""{C_RED}
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣤⠶⠶⠶⠶⢦⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡾⠛⠁⠀⠀⠀⠀⠀⠀⠈⠙⢷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠸⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⣠⡴⠞⠛⠉⠉⣩⣍⠉⠉⠛⠳⢦⣄⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡀⠀⣴⡿⣧⣀⠀⢀⣠⡴⠋⠙⢷⣄⡀⠀⣀⣼⢿⣦⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣧⡾⠋⣷⠈⠉⠉⠉⠉⠀⠀⠀⠀⠉⠉⠋⠉⠁⣼⠙⢷⣼⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣇⠀⢻⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡟⠀⣸⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣹⣆⠀⢻⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡟⠀⣰⣏⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣴⠞⠋⠁⠙⢷⣄⠙⢷⣀⠀⠀⠀⠀⠀⠀⢀⡴⠋⢀⡾⠋⠈⠙⠻⢦⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡾⠋⠀⠀⠀⠀⠀⠀⠹⢦⡀⠙⠳⠶⢤⡤⠶⠞⠋⢀⡴⠟⠀⠀⠀⠀⠀⠀⠙⠻⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣼⠋⠀⠀⢀⣤⣤⣤⣤⣤⣤⣤⣿⣦⣤⣤⣤⣤⣤⣤⣴⣿⣤⣤⣤⣤⣤⣤⣤⡀⠀⠀⠙⣧⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣸⠏⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⢠⣴⠞⠛⠛⠻⢦⡄⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠸⣇⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢠⡟⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⣿⣿⢶⣄⣠⡶⣦⣿⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⢻⡄⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣾⠁⠀⠀⠀⠀⠘⣇⠀⠀⠀⠀⠀⠀⠀⢻⣿⠶⠟⠻⠶⢿⡿⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠈⣿⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢰⡏⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⢾⣄⣹⣦⣀⣀⣴⢟⣠⡶⠀⠀⠀⠀⠀⠀⣼⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠈⠛⠿⣭⣭⡿⠛⠁⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠘⣧⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⢿⡀⠀⠀⠀⠀⠀⠀⣀⡴⠞⠋⠙⠳⢦⣀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⢰⡏⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠈⢿⣄⣀⠀⠀⢀⣤⣼⣧⣤⣤⣤⣤⣤⣿⣭⣤⣤⣤⣤⣤⣤⣭⣿⣤⣤⣤⣤⣤⣼⣿⣤⣄⠀⠀⣀⣠⡾⠁⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⠉⠛⠛⠻⢧⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠼⠟⠛⠛⠉⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣷⣶⣶⣶⣶⣶⣶⣿⣷⣶⣿⣿⣾⣿⣶⣶⣿⣿⣷⣿⣿⣿⣿⣿⣿⣾⣿⣿⣿⣿⣷⣷⣿⣷⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣷⣶⣿⣿{C_RST}
"""
        print(giant_art)
        
        print(f"{C_CYN}╔══════════════════════════════════════════════════════════════════════════════════════════════{C_RST}")
        print(f"{C_CYN}║{C_RST}")
        print(f"{C_CYN}║{C_RST}       {C_GRN}🚀 XP EARN BOT LIVE STATUS {C_MAG}| {C_YEL}{BOT_VERSION:<28}{C_RST}")
        print(f"{C_CYN}║{C_RST}       {C_CYN}────────────────────────────────────────────────────────────────────────────{C_RST}")
        print(f"{C_CYN}║{C_RST}       {C_RST}⏱️ Uptime      : {C_GRN}{uptime_h}h {uptime_m}m{C_RST:<14} {C_YEL}🏓 Latency   : {ping}{C_RST}")
        print(f"{C_CYN}║{C_RST}       {C_RST}👥 Total Users : {C_BLU}{t_users:<19} {C_RST}🛡️ Admins    : {C_YEL}{t_admins}{C_RST}")
        print(f"{C_CYN}║{C_RST}       {C_RST}📈 Today Joins : {C_GRN}{daily:<19} {C_RST}💰 Total XP  : {C_GRN}{t_xp}{C_RST}")
        print(f"{C_CYN}║{C_RST}       {C_RST}👑 Server King : {C_MAG}{DEVELOPER_NAME} [ Telegram: {DEVELOPER_ID} ]{C_RST}")
        print(f"{C_CYN}║{C_RST}")
        
        # Display Admin Logs
        if ADM_LOGS:
            print(f"{C_CYN}║{C_RST}       {C_YEL}🚨 LATEST ADMIN ACTIONS:{C_RST}")
            for l in ADM_LOGS:
                print(f"{C_CYN}║{C_RST}           - {l}")
            print(f"{C_CYN}║{C_RST}")
            
        print(f"{C_CYN}╚══════════════════════════════════════════════════════════════════════════════════════════════{C_RST}\n")
        
        await asyncio.sleep(10)

async def post_init(application):
    asyncio.create_task(console_dashboard_loop(application))

# ══════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════
def main():
    init_db()
    log.info("XP Earn Bot starting...")
    log.info(f"START_PHOTO  : {START_PHOTO}  | exists={os.path.isfile(START_PHOTO)}")
    log.info(f"PAYOUT_IMAGE : {PAYOUT_IMAGE} | exists={os.path.isfile(PAYOUT_IMAGE)}")

    application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start",       cmd_start))
    application.add_handler(CommandHandler("balance",     cmd_balance))
    application.add_handler(CommandHandler("profile",     cmd_profile))
    application.add_handler(CommandHandler("refer",       cmd_refer))
    application.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
    application.add_handler(CommandHandler("withdraw",    cmd_withdraw))
    application.add_handler(CommandHandler("pending",     cmd_pending))
    application.add_handler(CommandHandler("verify",      cmd_verify))
    application.add_handler(CommandHandler("reject",      cmd_reject))
    application.add_handler(CommandHandler("addadmin",    cmd_addadmin))
    application.add_handler(CommandHandler("removeadmin", cmd_removeadmin))
    application.add_handler(CommandHandler("admins",      cmd_admins))
    application.add_handler(CommandHandler("addxp",       cmd_addxp))
    application.add_handler(CommandHandler("broadcast",   cmd_broadcast))
    application.add_handler(CommandHandler("adminstats",  cmd_adminstats))
    application.add_handler(CommandHandler("setxp",       cmd_setxp))
    application.add_handler(CommandHandler("deductxp",    cmd_deductxp))
    application.add_handler(CallbackQueryHandler(cb_handler))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()