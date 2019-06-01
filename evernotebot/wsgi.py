import traceback
from time import time
from os.path import dirname, realpath, join
from urllib.parse import urlparse

from evernotebot.config import load_config
from evernotebot.bot.core import EvernoteBot
from evernotebot.util.telegram.models import TelegramUpdate
from uhttp import WsgiApplication
from uhttp.core import HTTPFound


def telegram_hook(request):
    bot = request.app.bot
    data = request.json()
    telegram_update = TelegramUpdate(data)
    bot.handle_telegram_update(telegram_update)


def evernote_oauth(request):
    callback_key = request.GET['key']
    oauth_verifier = request.GET.get('oauth_verifier')
    access = request.GET.get('access', 'basic')
    bot = request.app.bot
    bot.oauth_callback(callback_key, oauth_verifier, access)
    return HTTPFound(bot.url)


config = load_config()
webhook_url = config['webhook_url']
src_root = realpath(dirname(__file__))
app = WsgiApplication(src_root, config=config, urls=(
    ('POST', urlparse(webhook_url).path, telegram_hook),
    ('GET', r'^/evernote/oauth$', evernote_oauth),
))
app.bot = EvernoteBot(config)
try:
    app.bot.api.setWebhook(webhook_url)
except Exception as e:
    str_traceback = ''.join(traceback.format_tb(e.__traceback__))
    message = 'Can\'t set up webhook url `{url}`. Exception:\n{exception}'.format(url=webhook_url, exception=str_traceback)
    app.log(level='error', message=message)