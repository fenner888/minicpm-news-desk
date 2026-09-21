"""One explicit send to a fixed Telegram destination. No discovery or retries."""
import json
import os
import re
import urllib.request
from .core import loads
from .network import NoRedirect
from .presentation import telegram_html


def credentials():
    token=os.environ.get('NEWSDESK_TELEGRAM_TOKEN','')
    chat=os.environ.get('NEWSDESK_TELEGRAM_CHAT_ID','')
    if not re.fullmatch(r'[0-9]{5,15}:[A-Za-z0-9_-]{20,100}',token):raise ValueError('telegram_token_missing_or_invalid')
    if not re.fullmatch(r'-?[1-9][0-9]{0,19}',chat):raise ValueError('telegram_numeric_chat_required')
    return token,chat


def send(part,token,chat,opener=None):
    # Fixed host/method. Proxy credentials and redirects must not receive tokens.
    if not re.fullmatch(r'[0-9]{5,15}:[A-Za-z0-9_-]{20,100}',token):raise ValueError('invalid_token')
    if not re.fullmatch(r'-?[1-9][0-9]{0,19}',chat):raise ValueError('invalid_chat')
    payload={'chat_id':chat,'text':telegram_html(part),'parse_mode':'HTML',
             'link_preview_options':{'is_disabled':True}}
    request=urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage',
        data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    opener=opener or urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    # Never log/rethrow HTTP details: Telegram embeds the token in the URL.
    try:
        with opener.open(request,timeout=20) as response:
            if response.status!=200:raise ValueError('telegram_send_unconfirmed')
            raw=response.read(100001)
        if len(raw)>100000:raise ValueError('telegram_send_unconfirmed')
        result=loads(raw)
        message=result.get('result',{})
        mid=message.get('message_id')
        if result.get('ok') is not True or type(mid) is not int or mid<=0:
            raise ValueError('telegram_send_unconfirmed')
        if str(message.get('chat',{}).get('id'))!=chat:raise ValueError('telegram_send_unconfirmed')
        return mid
    except Exception:
        raise ValueError('telegram_send_unconfirmed') from None
