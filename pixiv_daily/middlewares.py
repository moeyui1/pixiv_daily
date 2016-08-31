# encoding=utf-8
import random
from pixiv_daily.user_agents import agents
import logging

class UserAgentMiddleware(object):
    """ 换User-Agent """

    def process_request(self, request, spider):
        agent = random.choice(agents)
        request.headers["User-Agent"] = agent


class ProxyMiddleware(object):
    # overwrite process request
    def process_request(self, request, spider):
        settings=spider.settings
        if not (settings['PROXY_ENABLED']):
            return #如果没有启用代理功能，直接返回
        # Set the location of the proxy
        logging.warning("have set the proxy to %s" % settings['PROXY_URL'])
        request.meta['proxy'] = settings['PROXY_URL']