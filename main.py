import asyncio
from telethon import TelegramClient, events
import sqlite3
import time

# --- Konfiguratsiya ---
api_id = 26967266
api_hash = '403845141439d1515cc66a35af026694'
channel_id = -1002555517149  # Forward qilinadigan kanal ID

# Forward qilish uchun kanallar/guruhlar ro'yxati
target_usernames = [
    'reak_papka_jild_reklama',
    'Garant_savdo_vz',
    'rek_vz_jild_rek_vz_grdde_papka',
    'Rek_jild_vz1',
    'Tekin_Reklama_Vz_01',
    'ortada_turib_berish_uz_forum',
    'Vz_rek_gtv',
    'vz_gr_tekin_reklama',
    'tekin_reklama_vp_prasmovtr',
    'uzforg',
    'Rek_reak_tekin_reklama',
    'tekin_reklama_tekinku',
    'eng_katta_tekin_reklama',
    'rek_vz_grde',
    'Tekin_Reklama_Offcial',
    'tekin_rekklama_chat',
    'uzfornet_rubI',
    'admnreklama',
    'Tekin_Rekklama_chat',
    'Garant_Savdo_Uzfor',
    'SAMAKE_VZ_REK',
    'tekin_reklama_rek_vz_grm',
    'reklama_pubg_tekin_chat',
    'tekin_reklamax',
    'fire_chat_free',
    'Pubg_Mobile_Chat_uz11',
    'SAMAKE_REK',
    'ortada_turib_berish_guruhi',
    'Reklama_ortada_turish_admin',
    'vzIIzn'
]

# Admin user id - buyruqlarni faqat shu userdan qabul qiladi
ADMIN_USER_ID = 123456789  # o'zingizning Telegram user ID'ingizni kiriting

client = TelegramClient('user_session', api_id, api_hash)

# SQLite bazaga ulanadi va posts jadval yaratadi
conn = sqlite3.connect("posts.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY)")
conn.commit()

target_peers = {}

async def setup_target_peers():
    for username in target_usernames:
        try:
            entity = await client.get_entity(username)
            target_peers[username] = entity
            print(f"✅ Entity olindi: {username}")
        except Exception as e:
            print(f"❌ Entity olinmadi: {username} — {e}")

async def forward_post_10_times(msg_id):
    original_msg = await client.get_messages(channel_id, ids=msg_id)
    if not original_msg:
        print(f"❌ Post topilmadi: {msg_id}")
        return

    if original_msg.grouped_id:
        all_msgs = await client.get_messages(channel_id, limit=20)
        grouped_msgs = [
            msg for msg in all_msgs
            if msg.grouped_id == original_msg.grouped_id and msg.id <= original_msg.id
        ]
        grouped_msgs = sorted(grouped_msgs, key=lambda m: m.id)
    else:
        grouped_msgs = [original_msg]

    msg_ids = [msg.id for msg in grouped_msgs]

    for msg in grouped_msgs:
        print(f"🕒 {msg.date.strftime('%Y-%m-%d %H:%M:%S')} — {msg.id} raqamli xabar")

    start_time = time.time()

    for i in range(10):
        print(f"\n🔁 [{i+1}/10] Post {msg_id} yuborilmoqda... ({len(msg_ids)} xabar)")
        for username, peer in target_peers.items():
            try:
                await client.forward_messages(
                    entity=peer,
                    messages=msg_ids,
                    from_peer=channel_id
                )
                print(f"✅ Post {msg_id} → {username} ga yuborildi")
            except Exception as e:
                print(f"❌ Post {msg_id} → {username} ga yuborilmadi: {e}")
        if i < 9:
            next_time = start_time + (i + 1) * 360  # 6 minut oraliq
            wait_time = next_time - time.time()
            if wait_time > 0:
                print(f"⏳ {round(wait_time)} sekund kutilmoqda (keyingi davra)")
                await asyncio.sleep(wait_time)

    cursor.execute("INSERT OR IGNORE INTO posts (id) VALUES (?)", (msg_id,))
    conn.commit()

@client.on(events.NewMessage(chats=channel_id))
async def auto_forward_handler(event):
    msg_id = event.message.id
    cursor.execute("SELECT id FROM posts WHERE id = ?", (msg_id,))
    if cursor.fetchone():
        print(f"⚠️ Post {msg_id} allaqachon yuborilgan")
        return
    print(f"🚀 Yangi post topildi: {msg_id}, avtomatik forward boshlanmoqda")
    await forward_post_10_times(msg_id)

@client.on(events.NewMessage(from_users=ADMIN_USER_ID))
async def command_listener(event):
    text = event.message.text
    if not text:
        return

    args = text.strip().split()
    if len(args) == 0:
        return

    if args[0].lower() == "forward":
        # Buyruq: forward <msg_id> yoki forward oxirgi
        if len(args) == 2:
            if args[1].lower() == "oxirgi":
                # Oxirgi postni olish
                messages = await client.get_messages(channel_id, limit=1)
                if messages:
                    msg_id = messages[0].id
                    await forward_post_10_times(msg_id)
                    await event.reply(f"Oxirgi post {msg_id} ga forward qilindi.")
                else:
                    await event.reply("Kanalda post topilmadi.")
            else:
                try:
                    msg_id = int(args[1])
                    await forward_post_10_times(msg_id)
                    await event.reply(f"Post {msg_id} ga forward qilindi.")
                except ValueError:
                    await event.reply("Xato: msg_id raqam bo‘lishi kerak.")
        else:
            await event.reply("Buyruq formati: forward <msg_id> yoki forward oxirgi")

async def main():
    await client.start()
    print("Bot ishga tushdi.")
    await setup_target_peers()
    print("Target peerlar tayyor.")
    print("Buyruqlarni Telegram orqali yuboring (faqat admin foydalanuvchi).")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
