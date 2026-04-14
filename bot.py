import discord
from discord.ext import commands
import sqlite3
import random
from datetime import datetime
import os

# ===== 設定 =====

BOT_TOKEN = os.getenv("BOT_TOKEN")
ORDER_CHANNEL_ID = 123456789012345678  # あとで数字を変える

ITEMS = ["商品A（レア）", "商品B（ノーマル）"]
WEIGHTS = [1, 4]

# ===== Bot初期化 =====

intents = discord.Intents.default()
bot = commands.Bot(intents=intents)

# ===== DB =====

conn = sqlite3.connect("orders.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT,
    quantity INTEGER,
    results TEXT,
    status TEXT,
    created_at TEXT
)
""")
conn.commit()

# ===== 抽選 =====

def draw_items(quantity: int):
    return [random.choices(ITEMS, weights=WEIGHTS, k=1)[0] for _ in range(quantity)]

# ===== モーダル =====

class OrderModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="ランダム商品BOX 注文")

        self.quantity = discord.ui.InputText(
            label="数量",
            placeholder="例：1"
        )

        self.add_item(self.quantity)

    async def callback(self, interaction: discord.Interaction):
        qty = int(self.quantity.value)
        results = draw_items(qty)

        c.execute("""
        INSERT INTO orders (user_id, user_name, quantity, results, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            interaction.user.id,
            str(interaction.user),
            qty,
            ", ".join(results),
            "pending",
            datetime.now().isoformat()
        ))
        conn.commit()

        channel = interaction.guild.get_channel(ORDER_CHANNEL_ID)
        if channel:
            await channel.send(
                f"🛒 新規注文\n"
                f"ユーザー: {interaction.user}\n"
                f"数量: {qty}\n\n"
                f"🎲 抽選結果\n" +
                "\n".join(f"・{r}" for r in results)
            )

        await interaction.response.send_message(
            "✅ 注文を受け付けました！",
            ephemeral=True
        )

# ===== コマンド =====

@bot.slash_command(name="order", description="ランダム商品を注文します")
async def order(ctx):
    await ctx.send_modal(OrderModal())

@bot.event
async def on_ready():
    print(f"Bot起動完了: {bot.user}")

bot.run(BOT_TOKEN)
