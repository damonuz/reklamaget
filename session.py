from telethon.sync import TelegramClient

api_id = 26967266      # <<< o'z API_ID'ingizni yozing (https://my.telegram.org)
api_hash = '403845141439d1515cc66a35af026694'  # <<< o'z API_HASH'ingizni yozing
phone = '+998331645757'     # <<< akkaunt raqamingiz

client = TelegramClient('user_session', api_id, api_hash)
client.start(phone=phone)

print("✅ Session yaratildi. Endi `main.py` faylini ishga tushiring.")
