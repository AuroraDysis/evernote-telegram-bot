import hashlib
import logging

from evernote.api.client import EvernoteClient as EvernoteSdk


class EvernoteApiError(Exception):
    pass


class EvernoteClient:
    def __init__(self, sandbox):
        self.sandbox = False

    def get_oauth_data(self, user_id, session_key, evernote_config, access='basic'):
        access_config = evernote_config['access'][access]
        api_key = access_config['key']
        api_secret = access_config['secret']
        bytes_key = '{0}{1}{2}'.format(api_key, api_secret, user_id).encode()
        callback_key = hashlib.sha1(bytes_key).hexdigest()
        callback_url = "{callback_url}?access={access}&key={key}&session_key={session_key}".format(
            access=access,
            callback_url=evernote_config['oauth_callback_url'],
            key=callback_key,
            session_key=session_key
        )
        sdk = EvernoteSdk(consumer_key=api_key, consumer_secret=api_secret, sandbox=self.sandbox)
        try:
            request_token = sdk.get_request_token(callback_url)
            if not request_token.get('oauth_token'):
                logging.getLogger().error('[X] EVERNOTE returns: {}'.format(request_token))
                raise EvernoteApiError("Can't obtain oauth token from Evernote")
            oauth_url = sdk.get_authorize_url(request_token)
        except Exception as e:
            raise EvernoteApiError(e)
        return {
            'oauth_url': oauth_url,
            'oauth_token': request_token['oauth_token'],
            'oauth_token_secret': request_token['oauth_token_secret'],
            'callback_key': callback_key,
        }

    def get_access_token(self, api_key, api_secret, oauth_token, oauth_token_secret, oauth_verifier):
        sdk = EvernoteSdk(consumer_key=api_key, consumer_secret=api_secret, sandbox=self.sandbox)
        return sdk.get_access_token(oauth_token, oauth_token_secret, oauth_verifier)
