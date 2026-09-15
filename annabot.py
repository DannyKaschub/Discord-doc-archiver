import os
from datetime import datetime
import discord
from discord.ext import commands
import asyncio
import config
from pathlib import Path

# ==================== EINSTELLUNGEN ====================
DEINE_DISCORD_ID = config.DEINE_DISCORD_ID
ARCHIV_ORDNER = Path(config.ARCHIV_ORDNER)
BOT_TOKEN = config.BOT_TOKEN
# =======================================================


intents = discord.Intents.default()
intents.message_content = True

class AnnaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents) 

    async def setup_hook(self):
        # Registriert den Button persistent beim Start
        self.add_view(AuftragsView())

bot = AnnaBot()


# =======================================================
# HILFSFUNKTION: PDF FISCHEN & SPEICHERN
# =======================================================
async def speichere_pdf_aus_nachicht(message):
    if not message.attachments:
        return None

    pdf_anhaenge = [a for a in message.attachments if a.filename.lower().endswith(".pdf")]

    if not pdf_anhaenge:
        return None

# Ordner automatisch anlegen, falls er nicht existiert
    ARCHIV_ORDNER.mkdir(parents=True, exist_ok=True)

    heute_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    pdf_anhang = pdf_anhaenge[0]
    pdf_name = f"{heute_str}_Dokument.pdf"
    
    # Pfad per pathlib verbinden (mit dem / Operator)
    finaler_speicherpfad = ARCHIV_ORDNER / pdf_name

    # Speichern mit Fehlerabfang
    try:
        await pdf_anhang.save(finaler_speicherpfad)
        return pdf_name
    except Exception as e:
        print(f"Fehler beim Speichern der PDF: {e}")
        return None


# =======================================================
# BUTTONS & VIEWS
# =======================================================
class RechnungsButtons(discord.ui.View):
    def __init__(self, autor_id):
        super().__init__(timeout=60)
        self.autor_id = autor_id
        self.abgebrochen = False

    @discord.ui.button(label="Keine Rechnung / Abbrechen", style=discord.ButtonStyle.danger, emoji="❌")
    async def abbrechen(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("Finger weg! 💅", ephemeral=True)
            return
        self.abgebrochen = True
        self.stop()
        await interaction.response.edit_message(content="Alles klar, PDF wurde ohne Rechnungsdaten archiviert! 👍", view=None)


class AuftragsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Als bezahlt markieren", style=discord.ButtonStyle.success, emoji="✅", custom_id="persistent_abbuchen_btn")
    async def erledigt(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != DEINE_DISCORD_ID:
            await interaction.response.send_message("Du hast hier nichts zu bezahlen! 💅", ephemeral=True)
            return

        alter_inhalt = interaction.message.content
        neuer_inhalt = f"~~{alter_inhalt}~~\n\n🎉 **Erledigt & Bezahlt am {datetime.now().strftime('%d.%m.%Y um %H:%M')}**"
        await interaction.response.edit_message(content=neuer_inhalt, view=None)


# =======================================================
# BOT EVENTS
# =======================================================
@bot.event
async def on_ready():
    print(f"=== {bot.user.name} ist online und bereit! ===")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.author.id != DEINE_DISCORD_ID:
        if isinstance(message.channel, discord.DMChannel) or bot.user.mentioned_in(message):
            await message.channel.send("Entschuldige, wer warst du noch gleich? 💅")
        return

    # PDF verarbeiten
    pdf_name = await speichere_pdf_aus_nachicht(message)

    if not pdf_name:
        return

    # KORREKTUR: Einrückung gefixt & Bestätigung angepasst
    await message.channel.send(f"✅ **PDF archiviert als `{pdf_name}`**")

    view = RechnungsButtons(autor_id=message.author.id)
    frage_msg = await message.channel.send(
        "📋 **Rechnungsdaten erfassen?**\n"
        "Antworte direkt auf diese Nachricht im Format:\n"
        "`Wer | Betrag | Datum` (z.B. `Vodafone | 45,90 | 31.07.2026`)",
        view=view
    )

    def check_antwort(m):
        return m.author.id == message.author.id and m.channel == message.channel

    try:
        done, pending = await asyncio.wait(
            [
                asyncio.create_task(bot.wait_for("message", check=check_antwort), name="text"),
                asyncio.create_task(view.wait(), name="button")
            ],
            return_when=asyncio.FIRST_COMPLETED,
            timeout=60.0
        )

        for task in pending:
            task.cancel()

        if view.abgebrochen:
            return

        for task in done:
            if task.get_name() == "text":
                antwort_msg = task.result()
                info_text = antwort_msg.content.strip()
                
                await frage_msg.delete()
                try:
                    await antwort_msg.delete()
                except:
                    pass

                try:
                    teile = [t.strip() for t in info_text.split("|")]
                    schuldner = teile[0] if len(teile) > 0 else "Unbekannt"
                    betrag = teile[1] if len(teile) > 1 else "Unbekannt"
                    frist_str = teile[2] if len(teile) > 2 else "Unbekannt"

                    auftrags_text = (
                        f"📌 **OFFENER AUFTRAG / RECHNUNG**\n"
                        f"📁 Datei: `{pdf_name}`\n"
                        f"👤 Wer: **{schuldner}**\n"
                        f"💰 Betrag: **{betrag} €**\n"
                        f"📅 Frist: **{frist_str}**"
                    )
                    
                    await message.channel.send(auftrags_text, view=AuftragsView())
                    
                except Exception:
                    await message.channel.send("Fehler beim Aufteilen der Daten.")

    except asyncio.TimeoutError:
        await frage_msg.edit(content="⏳ Abfrage abgelaufen. Keine Rechnungsdaten erfasst.", view=None)

    except Exception as e:
        await message.channel.send(f"Fehler: {e}")


# Bot starten
bot.run(BOT_TOKEN)