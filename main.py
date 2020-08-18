from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from functools import partial
from pydub import AudioSegment
from io import BytesIO
import threading
import requests
import numpy as np
import math
import os

TOKEN = os.environ['TOKEN']
LOGS_CHANNEL_ID = os.environ['LOGS_CHANNEL_ID']


def non_blocking(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=partial(func, *args, **kwargs))
        thread.start()
    return wrapper

class BoostBastedBot:
    def __init__(self, token, logs_channel_id):
        self.logs_channel_id = logs_channel_id
        self.updater = Updater(token, use_context=True)
        self.dp = self.updater.dispatcher
        self.bot = self.dp.bot

        self.dp.add_handler(CommandHandler('start', self.start_handler))
        self.dp.add_handler(MessageHandler(Filters.audio, self.process_audio_handler), group=1)
        self.dp.add_handler(MessageHandler(Filters.voice, self.process_audio_handler), group=1)

        self.updater.start_polling()
        self.updater.idle()

        self.bot_started()
        self.health_checker()

    def start_handler(self, update, context):
        self.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Send me audio or voice!'
        )

    @non_blocking
    def process_audio_handler(self, update, context):
        chat_id = update.effective_chat.id
        try:
            audio = update.message.audio or update.message.effective_attachment
            audio_format = get_audio_format(audio.mime_type)
            self.log_msg('Full name: {full_name}; Nickname: {name}; Url: {url}'.format(
                full_name=update.effective_user.full_name,
                name=update.effective_user.name,
                url=audio.get_file().file_path
            ))
            self.send_msg(chat_id, 'Unholy transformation started!')
            if not audio_format:
                self.send_msg(chat_id, 'Unsupported audio format!')
                return
            boosted_audio = self.boost_audio(audio, audio_format)
            self.response_audio(chat_id, audio, audio_format, boosted_audio)
        except Exception as e:
            self.send_msg(chat_id, 'Sorry, something went wrong!')
            self.log_msg(e)

    def boost_audio(self, audio, audio_format):
        tags = self.get_audio_tags()
        file_url = audio.get_file().file_path
        req = requests.get(file_url, stream=True)
        fake_file_in = BytesIO(req.content)
        fake_file_out = BytesIO()

        if audio_format == 'oga':
            attenuate_db = 35
            accentuate_db = 35
            audio_in = AudioSegment.from_ogg(fake_file_in)
        else:
            attenuate_db = 25
            accentuate_db = 25
            audio_in = AudioSegment.from_file(fake_file_in, format=audio_format)

        track_raw = audio_in.get_array_of_samples()
        track_raw = list(track_raw)
        est_mean = np.mean(track_raw)
        est_std = 3.0 * np.std(track_raw) / (math.sqrt(2))
        bass_factor = int(round((est_std - est_mean) * 0.005))
        filtered = audio_in.low_pass_filter(bass_factor)
        audio_out = (audio_in - attenuate_db).overlay(filtered + accentuate_db)
        return audio_out.export(fake_file_out, format=audio_format, tags=tags)

    def get_audio_format(self, audio_format):
        supported_audio_format = {
            "audio/mp3": "mp3",
            "audio/mpeg3": "mp3",
            "audio/x-mpeg-3": "mp3",
            "audio/mpeg": "mp3",
            "audio/ogg": "oga",
        }
        return supported_audio_format[audio_format]

    def get_audio_tags(self):
        bot_link = 'https://t.me/{bot}'.format(bot=self.bot.username)
        return {
            'composer': bot_link,
            'service_name': bot_link,
            'genre': 'Boooosted',
            'encoder': bot_link,
            'encoded_by': bot_link
        }

    def response_audio(self, chat_id, audio, audio_format, boosted_audio):
        if audio_format == 'oga':
            response_msg = self.bot.send_voice(
                chat_id=chat_id,
                voice=boosted_audio,
                duration=audio.duration
            )
            self.bot.forward_message(self.logs_channel_id, chat_id, response_msg.message_id)
        else:
            response_msg = self.bot.send_audio(
                chat_id=chat_id,
                audio=boosted_audio,
                title='{title} BASS_BOOSTED by @boost_bassted_bot'.format(title=audio.title or 'untitled'),
                thumb=open('thumb.jpg', 'rb')
            )
            self.bot.forward_message(self.logs_channel_id, chat_id, response_msg.message_id)

    def health_checker(self):
        self.log_msg('Bot alive!')
        threading.Timer(43200, self.health_checker).start()

    def bot_started(self):
        self.log_msg('Bot started!')

    def send_msg(self, chat_id, msg):
        self.bot.send_message(chat_id=chat_id, text=msg)

    def log_msg(self, msg):
        print(msg)
        self.send_msg(self.logs_channel_id, msg)


def main():
    BoostBastedBot(TOKEN, LOGS_CHANNEL_ID)


if __name__ == '__main__':
    main()
