# coding=utf-8
import webbrowser

from weibo import APIClient

import pixiv_daily.sina.sina_config as config


class Client(object):
    def __init__(self,APP_KEY=None,APP_SECRET=None):
        if APP_KEY:
            self.APP_KEY=APP_KEY
        else:
            self.APP_KEY=config.APP_KEY
        if APP_SECRET:
            self.APP_SECRET=APP_SECRET
        else:
            self.APP_SECRET = config.APP_SECRET

    def get_client(self):

        # 管理中心---应用信息---高级信息，将"授权回调页"的值改成https://api.weibo.com/oauth2/default.html
        CALLBACK_URL = 'https://api.weibo.com/oauth2/default.html'
        client = APIClient(app_key=self.APP_KEY, app_secret=self.APP_SECRET, redirect_uri=CALLBACK_URL)

        access_token = config.access_token
        expires_in = config.expires_in
        if not (access_token or expires_in):
            url = client.get_authorize_url()
            print u'正在打开授权网址：' + url
            webbrowser.open(url)
            code = raw_input('输入code:')
            r = client.request_access_token(code)
            access_token = r.access_token  # 新浪返回的token，类似abc123xyz456
            expires_in = r.expires_in
        client.set_access_token(access_token, expires_in)
        return client
