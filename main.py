import asyncio
from telethon import TelegramClient, events
import sqlite3
import time
import sys

# --- Konfiguratsiya ---
api_id = 26967266
api_hash = '403845141439d1515cc66a35af026694'
channel_id = -1002555517149  # Kanal ID

target_usernames = [
    'reak_papka_jild_reklama',
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
    'reak_papka_jild_reklama',
    'tekin_rekklama_chat',
    'uz_rubil',
    'uzfornet_rubI',
    'admnreklama',
    'Tekin_Rekklama_chat',
    'Garant_Savdo_Uzfor',
    'SAMAKE_VZ_REK',
    'tekin_reklama_rek_vz_grm',
    'reklama_pubg_tekin_chat',
    'tekin_reklamax',
    'Rek_jild_vz1',
    'Vz_rek_gtv',
    'fire_chat_free',
    'eng_katta_tekin_reklama',
    'ortada_turib_berish_uz_forum',
    'Pubg_Mobile_Chat_uz11',
    'SAMAKE_REK',
    'tekin_reklama_vp_prasmovtr',
    'ortada_turib_berish_guruhi',
    'Reklama_ortada_turish_admin',
    'Rek_reak_tekin_reklama',
    'vzIIzn',
    'vz_gr_tekin_reklama',
    'tekin_reklama_tekinku',
    'BESEDA_WENIKS',
    'reklama_pubg_tekin_chat'
]

client = TelegramClient('user_session', api_id, api_hash)

# Bazaga ulanadi
conn = sqlite3.connect("posts.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY)")
conn.commit()

target_peers = {}

# Guruhlarni olish
async def setup_target_peers():
    for username in target_usernames:
        try:
            entity = await client.get_entity(username)
            target_peers[username] = entity
            print(f"✅ Entity olindi: {username}")
        except Exception as e:
            print(f"❌ Entity olinmadi: {username} — {e}")

# Forward qilishni 10 bosqichli 5 daqiqa oraliqli qilish
async def forward_post_10_times(msg_id):
    original_msg = await client.get_messages(channel_id, ids=msg_id)

    if not original_msg:
        print(f"❌ Post {msg_id} kanalda topilmadi!")
        return

    # Guruhlangan postmi yoki yo‘q
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

    # Vaqt va forward manbasini chiqarish
    for msg in grouped_msgs:
        print(f"🕒 {msg.date.strftime('%Y-%m-%d %H:%M:%S')} — {msg.id} raqamli xabar")
        if msg.forward:
            if msg.forward.chat:
                from_chat = msg.forward.chat.title or msg.forward.chat.username or 'Nomaʼlum kanal/guruh'
                print(f"   📤 Forward qilingan joy: {from_chat}")
            elif msg.forward.sender:
                sender = (msg.forward.sender.first_name or '') + ' ' + (msg.forward.sender.last_name or '')
                print(f"   👤 Forward qilingan foydalanuvchi: {sender.strip()}")
            else:
                print("   ℹ️ Forward manbasi topilmadi")
        else:
            print("   🔄 Bu post forward qilingan emas")

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
            next_time = start_time + (i + 1) * 360  # 6 daqiqa oraliq
            wait_time = next_time - time.time()
            if wait_time > 0:
                print(f"⏳ {round(wait_time)} sekund kutilmoqda (keyingi davra)")
                await asyncio.sleep(wait_time)

    cursor.execute("INSERT OR IGNORE INTO posts (id) VALUES (?)", (msg_id,))
    conn.commit()

# Yangi post tushganda avtomatik forward qilish
@client.on(events.NewMessage(chats=channel_id))
async def handler(event):
    msg_id = event.message.id
    cursor.execute("SELECT id FROM posts WHERE id = ?", (msg_id,))
    if cursor.fetchone():
        print(f"⚠️ Post {msg_id} allaqachon yuborilgan")
        return
    asyncio.create_task(forward_post_10_times(msg_id))

# Buyruqlarni cmd oynadan qabul qilish uchun funksiya
async def command_listener():
    print("📥 Buyruqlar uchun kutilyapti... (Misol: forward <msg_id> yoki forward oxirgi)")
    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, ">> ")
        parts = user_input.strip().split()

        if len(parts) == 0:
            continue

        cmd = parts[0].lower()

        if cmd == 'forward':
            if len(parts) == 1 or parts[1].lower() == 'oxirgi':
                # Oxirgi postni olish
                msgs = await client.get_messages(channel_id, limit=1)
                if not msgs:
                    print("❌ Kanalda hech qanday xabar topilmadi")
                    continue
                msg_id = msgs[0].id
            else:
                try:
                    msg_id = int(parts[1])
                except ValueError:
                    print("❌ Noto'g'ri xabar ID kiritildi")
                    continue

            print(f"⏳ Post {msg_id} ni 10 marta forward qilaman...")
            try:
                await forward_post_10_times(msg_id)
                print(f"✅ Post {msg_id} forward qilindi.")
            except Exception as e:
                print(f"❌ Xatolik yuz berdi: {e}")

        elif cmd in ('exit', 'quit'):
            print("Bot to‘xtatildi.")
            await client.disconnect()
            break

        else:
            print("❌ Nomaʼlum buyruq. Faqat 'forward <msg_id|oxirgi>', 'exit' yoki 'quit' buyruqlari mavjud.")

# Asosiy ishga tushirish
async def main():
    await setup_target_peers()
    print("🚀 Bot tayyor. Kanalga kelgan har bir yangi post avtomatik 10 martalik yuboriladi.")
    # Asyncio da ikkita ishni bir vaqtning o'zida bajarish uchun:
    await asyncio.gather(
        client.run_until_disconnected(),
        command_listener()
    )

with client:
    client.loop.run_until_complete(main())
