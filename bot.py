import os
import discord
from dotenv import load_dotenv
import hashlib

BAD_HASHES = {
    "20BD050CF409A23A516DE47493D1691E8E9ADB0BDF93CC1A4FE1914B378689BA ",
}

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")

ALLOWED = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

DANGEROUS = {
    ".exe", ".scr", ".bat", ".cmd", ".com", ".msi", ".jar", ".lnk",
    ".vbs", ".js", ".ps1", ".apk", ".dll", ".zip", ".rar", ".7z",
}

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def send_log(guild, text):
    if not LOG_CHANNEL_ID:
        return
    channel = guild.get_channel(int(LOG_CHANNEL_ID))
    if channel:
        try:
            await channel.send(text)
        except discord.HTTPException:
            pass


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    if not message.attachments:
        return

    perms = message.author.guild_permissions
    if perms.administrator or perms.manage_messages:
        return

    for a in message.attachments:
        ext = os.path.splitext(a.filename.lower())[1]

        if ext in DANGEROUS:
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            try:
                await message.author.ban(
                    reason=f"ملف خبيث: {a.filename}",
                    delete_message_seconds=3600,
                )
                await send_log(
                    message.guild,
                    f"تم حظر {message.author} ({message.author.id}) بسبب الملف {a.filename}",
                )
            except discord.HTTPException:
                await send_log(
                    message.guild,
                    f"ما قدرت أحظر {message.author} (تأكد إن رتبة البوت فوق رتبته). الملف: {a.filename}",
                )
            return

        if ext in ALLOWED and a.size < 8_000_000:
            data = await a.read()
            if hashlib.sha256(data).hexdigest() in BAD_HASHES:
                try:
                    await message.delete()
                    await message.author.ban(
                        reason="صورة نصب معروفة",
                        delete_message_seconds=3600,
                    )
                    await send_log(message.guild, f"تم حظر {message.author} بسبب صورة نصب")
                except discord.HTTPException:
                    pass
                return
 
        if ext not in ALLOWED:
            try:
                await message.delete()
                await send_log(
                    message.guild,
                    f"حذفت ملف {a.filename} من {message.author} (بدون حظر)",
                )
            except discord.HTTPException:
                pass
            return


if not TOKEN:
    raise SystemExit("ما لقيت DISCORD_TOKEN في ملف .env")

client.run(TOKEN)