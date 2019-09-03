from time import time

from utelegram import Message
from evernotebot.bot.core import EvernoteBot
from evernotebot.bot.commands import start_command
from evernotebot.bot.shortcuts import evernote_oauth_callback, OauthParams

from tests.util.base import TestCase
from tests.util.mocks import TelegramApiMock, EvernoteApiMock


class TestSaveToEvernote(TestCase):
    def setUp(self):
        bot = EvernoteBot(self.config)
        bot.api = TelegramApiMock()
        bot.evernote = EvernoteApiMock()
        message = Message(
            message_id=1,
            date=time(),
            from_user={"id": 6, "is_bot": False, "first_name": "test"},
            chat={"id": 1, "type": "private"}
        )
        start_command(bot, message)
        oauth_data =  bot.evernote._oauth_data
        evernote_oauth_callback(bot, OauthParams(oauth_data["callback_key"], "oauth_verifier", "basic"))
        # creating new mocks because we want get a clean picture
        bot.api = TelegramApiMock()
        bot.evernote = EvernoteApiMock()
        self.bot = bot

    def test_save_text(self):
        user_id = 6
        update_data = {
            "update_id": 1,
            "message": {
                "message_id": 2,
                "date": time(),
                "text": 'Hello, World!',
                "from_user": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "test",
                },
                "chat": {"id": 2, "type": "private"},
            },
        }
        self.bot.process_update(update_data)
        self.assertEqual(self.bot.evernote.create_note.call_count, 1)
        call = self.bot.evernote.create_note.calls[0]
        self.assertEqual(call["args"][0], "guid")
        self.assertEqual(call["args"][1], "Hello, World!")


    def test_save_photo(self):
        user_id = 6
        update_data = {
            "update_id": 1,
            "message": {
                "message_id": 2,
                "date": time(),
                "caption": 'Selfie',
                "from_user": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "test",
                },
                "chat": {"id": 2, "type": "private"},
                "photo": [
                    {
                        "file_id": "qwe",
                        "width": 100,
                        "height": 100,
                        "file_size": 100,
                    }
                ],
            },
        }
        self.bot.process_update(update_data)
        self.assertEqual(self.bot.api.getFile.call_count, 1)
        self.assertEqual(self.bot.api.sendMessage.call_count, 1)
        self.assertEqual(self.bot.api.sendMessage.calls[0]["args"][1], "Photo accepted")
        self.assertEqual(self.bot.api.editMessageText.call_count, 1)
        self.assertEqual(self.bot.api.editMessageText.calls[0]["args"][2], "Saved")
        self.assertEqual(self.bot.evernote.create_note.call_count, 1)
        call = self.bot.evernote.create_note.calls[0]
        self.assertEqual(call["args"][2], "Selfie")
        self.assertEqual(len(call["kwargs"]["files"]), 1)
        self.assertEqual(call["kwargs"]["files"][0]["name"], "robots.txt")

    def test_save_voice(self):
        user_id = 6
        update_data = {
            "update_id": 1,
            "message": {
                "message_id": 2,
                "date": time(),
                "from_user": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "test",
                },
                "chat": {"id": 2, "type": "private"},
                "voice": {
                    "duration": 3,
                    "mime_type": "audio/ogg",
                    "file_id": "AwADAgAD3wQAAncCKUpLSYvFZV5rixYE",
                    "file_size": 304,
                },
            },
        }
        self.bot.process_update(update_data)
        self.assertEqual(self.bot.api.getFile.call_count, 1)
        self.assertEqual(self.bot.api.sendMessage.call_count, 1)
        self.assertEqual(self.bot.api.sendMessage.calls[0]["args"][1], "Voice accepted")
        self.assertEqual(self.bot.api.editMessageText.call_count, 1)
        self.assertEqual(self.bot.api.editMessageText.calls[0]["args"][2], "Saved")
        self.assertEqual(self.bot.evernote.create_note.call_count, 1)
        call = self.bot.evernote.create_note.calls[0]
        self.assertEqual(call["args"][2], "File")
        self.assertEqual(len(call["kwargs"]["files"]), 1)
        self.assertEqual(call["kwargs"]["files"][0]["name"], "robots.txt")

    def test_save_video(self):
        user_id = 6
        update_data = {
            "update_id": 1,
            "message": {
                "message_id": 2,
                "date": time(),
                "from_user": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "test",
                },
                "chat": {"id": 2, "type": "private"},
                "video": {
                    "file_id": "AwADAgAD3wQAAncCKUpLSYvFZV5rixYE",
                    "width": 100,
                    "height": 100,
                    "duration": 10,
                    "file_size": 304,
                },
            },
        }
        self.bot.process_update(update_data)
        self.assertEqual(self.bot.api.getFile.call_count, 1)
        self.assertEqual(self.bot.api.sendMessage.call_count, 1)
        self.assertEqual(self.bot.api.sendMessage.calls[0]["args"][1], "Video accepted")
        self.assertEqual(self.bot.api.editMessageText.call_count, 1)
        self.assertEqual(self.bot.api.editMessageText.calls[0]["args"][2], "Saved")
        self.assertEqual(self.bot.evernote.create_note.call_count, 1)
        call = self.bot.evernote.create_note.calls[0]
        self.assertEqual(call["args"][2], "File")
        self.assertEqual(len(call["kwargs"]["files"]), 1)
        self.assertEqual(call["kwargs"]["files"][0]["name"], "robots.txt")
