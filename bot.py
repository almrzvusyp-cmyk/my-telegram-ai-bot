
import os
import base64
import tempfile
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

async def ask_ai(text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Ты дружелюбный помощник. Отвечай на русском языке."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        answer = await ask_ai(update.message.text)
        await update.message.reply_text(answer)
    except Exception:
        await update.message.reply_text("Не удалось получить ответ. Попробуй позже.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()
        encoded = base64.b64encode(image_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": update.message.caption or "Опиши эту фотографию."},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded}"
                    }}
                ]}
            ]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception:
        await update.message.reply_text("Не удалось обработать фотографию.")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice = await update.message.voice.get_file()
        audio_bytes = await voice.download_as_bytearray()

        with tempfile.NamedTemporaryFile(suffix=".ogg") as audio:
            audio.write(audio_bytes)
            audio.flush()
            with open(audio.name, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=audio_file
                )

        answer = await ask_ai(transcription.text)
        await update.message.reply_text(
            f"Ты сказал: {transcription.text}\n\n{answer}"
        )
    except Exception:
        await update.message.reply_text("Не удалось распознать голосовое сообщение.")

async def main():
    app = Application.builder().token(
        os.environ["TELEGRAM_BOT_TOKEN"]
    ).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

import asyncio
asyncio.run(main())
