# coding=utf-8
import json
import logging
import scrapy
from scrapy.spiders import CrawlSpider
from pixiv_daily.items import PixivCrawlItem


class PixivSpider(CrawlSpider):
    name = "pixiv"
    allowed_domains = ['pixiv.net']

    def start_requests(self):
        return [
            scrapy.Request(url='https://accounts.pixiv.net/login?lang=zh', callback=self.before_login)
        ]

    def before_login(self, response):
        # 获取登录校验key
        key = response.xpath('//*[@id="old-login"]/form/input[@name="post_key"]/@value').extract()
        setting = self.settings
        # 登录请求
        yield scrapy.FormRequest(url='https://accounts.pixiv.net/login?lang=zh', formdata={
            'pixiv_id': setting['PIXIV_USER_NAME'],
            'password': setting['PIXIV_USER_PASS'],
            'post_key': key,
            'source': 'pc'
        }, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
        },
                                 meta={
                                     'dont_redirect': True,
                                     'handle_httpstatus_list': [302]
                                 },
                                 callback=self.after_logged_in)

    def after_logged_in(self, response):
        # logging.warning(response.status)
        if (response.status == 302):
            yield scrapy.Request('http://www.pixiv.net/ranking.php?'
                                 'mode={mode}&content=illust&format=json&date={date}'.format(
                date=self.settings["START_DATE"].strftime("%Y%m%d"),
                mode=self.settings['MODE']
            ), callback=self.parse)
        else:
            # 没有302重定向，表示登录失败了
            logging.error("登录失败，请检查用户名和密码")

    def parse(self, response):
        result = json.loads(response.body.decode('utf-8'), 'utf8')
        for section in result['contents']:
            item = PixivCrawlItem()
            item['title'] = section['title']
            item['date'] = section['date']
            item['user_id'] = section['user_id']
            item['user_name'] = section['user_name']
            item['rank'] = section['rank']
            item['yes_rank'] = section['yes_rank']
            item['total_score'] = section['total_score']
            item['views'] = section['view_count']
            item['is_sexual'] = section['illust_content_type']['sexual']
            item['illust_id'] = section['illust_id']
            item['tags'] = section['tags']

            # header中不写referer或者referer正确会导致403错误。
            yield scrapy.Request(
                self.generate_detail_url(section['illust_id']),
                callback=self.parse_detail,
                meta={'item': item},
                headers={
                    'referer': response.url,
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
                }
            )

    """ 根据给定的illust_id返回对应的详情页URL
    Args:
        illust_id:每个绘画的唯一ID号
    Returns:
        根据模板生成的URL地址字符串
    """

    def generate_detail_url(self, illust_id):
        return 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id={0}'.format(illust_id)

    def parse_detail(self, response):
        # //*[@id="wrapper"]/div[2]/div/img
        item = response.meta['item']
        item['url'] = response.url
        img_url = response.css('._illust_modal img').css('::attr("data-src")').extract()
        if (len(img_url) > 0):
            item['img_urls'] = img_url
        yield item
