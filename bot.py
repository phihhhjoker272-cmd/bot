import telebot
from telebot import types
import json
from datetime import datetime, timedelta

TOKEN = "8539833844:AAECNRQTyIOGWbVA1JowHzE1Ojf-Zgii0OM"
OWNER_ID = 5632595117

AUTO_MUTE_MIN = 5
WARN_LIMIT = 3

bot = telebot.TeleBot(TOKEN)

FILES = {
    "roles": "roles.json",
    "warns": "warns.json"
}


def load(name):
    try:
        with open(FILES[name], "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save(name, data):
    with open(FILES[name], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===== ROLES =====

ROLE_POWER = {
    "owner": 100,
    "status": 90,
    "elite": 70,
    "helper": 50,
    "middle": 30,
    "user": 10
}


def get_role(user):
    if user.id == OWNER_ID:
        return "owner"
    return load("roles").get(str(user.id), "user")


def can_touch(actor, target):
    if actor.id == OWNER_ID:
        return True
    return ROLE_POWER[get_role(actor)] > ROLE_POWER[get_role(target)]


# ===== PROMOTE / DEMOTE (ONLY OWNER) =====

@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower().startswith("повысить"))
def promote(m):
    if m.from_user.id != OWNER_ID:
        return

    role_map = {
        "статус": "status",
        "элита": "elite",
        "хелпер": "helper",
        "средний": "middle"
    }

    try:
        role = role_map[m.text.lower().split(" ", 1)[1]]
    except:
        bot.reply_to(m, "повысить статус / элита / хелпер / средний")
        return

    uid = m.reply_to_message.from_user.id
    roles = load("roles")
    roles[str(uid)] = role
    save("roles", roles)

    try:
        bot.promote_chat_member(
            m.chat.id, uid,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True
        )
    except:
        pass

    bot.reply_to(m, "✅ повышен")


@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower() == "понизить")
def demote(m):
    if m.from_user.id != OWNER_ID:
        return

    uid = m.reply_to_message.from_user.id
    roles = load("roles")
    roles.pop(str(uid), None)
    save("roles", roles)

    bot.reply_to(m, "⬇️ понижен")


# ===== WARN =====

@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower() == "варн")
def warn(m):
    if not can_touch(m.from_user, m.reply_to_message.from_user):
        bot.reply_to(m, "❌ нельзя трогать админа")
        return

    warns = load("warns")
    uid = str(m.reply_to_message.from_user.id)
    warns[uid] = warns.get(uid, 0) + 1
    save("warns", warns)

    if warns[uid] >= WARN_LIMIT:
        bot.kick_chat_member(m.chat.id, int(uid))
        warns.pop(uid, None)
        save("warns", warns)
        bot.reply_to(m, "⛔ 3 варна — БАН")
    else:
        bot.reply_to(m, f"⚠️ варн {warns[uid]}/3")


@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower() == "снять варн")
def unwarn(m):
    if not can_touch(m.from_user, m.reply_to_message.from_user):
        return

    warns = load("warns")
    uid = str(m.reply_to_message.from_user.id)
    warns[uid] = max(0, warns.get(uid, 0) - 1)
    save("warns", warns)
    bot.reply_to(m, "✅ варн снят")


# ===== MUTE =====

@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower().startswith("мут"))
def mute(m):
    if not can_touch(m.from_user, m.reply_to_message.from_user):
        bot.reply_to(m, "❌ нельзя трогать админа")
        return

    try:
        mins = int(m.text.split(" ", 1)[1])
    except:
        mins = AUTO_MUTE_MIN

    until = datetime.now() + timedelta(minutes=mins)
    bot.restrict_chat_member(
        m.chat.id, m.reply_to_message.from_user.id,
        until_date=until,
        permissions=types.ChatPermissions(can_send_messages=False)
    )

    bot.reply_to(m, f"🔇 мут {mins} мин")


@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower() == "говори")
def unmute(m):
    if not can_touch(m.from_user, m.reply_to_message.from_user):
        return

    bot.restrict_chat_member(
        m.chat.id, m.reply_to_message.from_user.id,
        permissions=types.ChatPermissions(can_send_messages=True)
    )
    bot.reply_to(m, "🔊 мут снят")


# ===== BAN / UNBAN =====

@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower() == "бан")
def ban(m):
    if not can_touch(m.from_user, m.reply_to_message.from_user):
        bot.reply_to(m, "❌ нельзя трогать админа")
        return

    bot.kick_chat_member(m.chat.id, m.reply_to_message.from_user.id)
    bot.reply_to(m, "⛔ забанен")


@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("разбан"))
def unban(m):
    if m.from_user.id != OWNER_ID:
        return
    try:
        uid = int(m.text.split(" ", 1)[1])
        bot.unban_chat_member(m.chat.id, uid)
        bot.reply_to(m, "✅ разбанен")
    except:
        bot.reply_to(m, "разбан ID")


bot.infinity_polling()
