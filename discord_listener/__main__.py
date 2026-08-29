import json
import os
import re
from pathlib import Path
import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNELS = {
    int(x.strip()) for x in os.getenv("DISCORD_CHANNEL_IDS", "").split(",")
    if x.strip().isdigit()
}
OUT = Path("data/discord-discoveries.json")
CODE_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9]{5,15})(?![A-Za-z0-9])")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def save(item):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = []
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = []
    data.append(item)
    OUT.write_text(json.dumps(data[-1000:], ensure_ascii=False, indent=2), encoding="utf-8")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if CHANNELS and message.channel.id not in CHANNELS:
        return

    text = message.content.upper()
    for code in sorted(set(CODE_RE.findall(text))):
        save({
            "code": code,
            "channel_id": message.channel.id,
            "message_id": message.id,
            "url": message.jump_url,
        })
        print("DISCOVERED", code, message.jump_url)

if not TOKEN:
    raise SystemExit("DISCORD_BOT_TOKEN is required")

client.run(TOKEN)
