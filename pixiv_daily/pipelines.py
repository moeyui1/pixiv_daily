# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import os
import os.path

import scrapy
from scrapy.exceptions import DropItem
from scrapy.http import Request
from scrapy.pipelines.images import FilesPipeline


class PixivDaliyImageInfoPipeline(object):
    b = False

    def __init__(self):
        self.file = open('items.json', 'w')
        self.file.write('[')

    def process_item(self, item, spider):
        line=''
        if (self.b):
            line += ','
        else:
            self.b = True
        line += json.dumps(dict(item), ensure_ascii=False, indent=2)

        line += '\n'
        self.file.write(line)
        return item

    def close_spider(self, spider):
        self.file.write(']')
        self.file.close()


class PixivImagesPipeline(FilesPipeline):
    """抽取ITEM中的图片地址，并下载"""

    # 非法字符元组
    invalidChar = ('"', '?', "\\", "/", "<", '>', '|', ':', '*')

    def get_media_requests(self, item, info):
        try:
            for image_url in item['img_urls']:
                yield scrapy.Request(image_url,
                                     headers={'Referer': item['url'],  # 添加Referer，否则会返回403错误
                                              'User-Agent': 'Mozilla/5.0 (Macintosh; '
                                                            'Intel Mac OS X 10_10_5) '
                                                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                            'Chrome/45.0.2454.101 Safari/537.36'

                                              }, meta={'item': item})
        except KeyError:
            raise DropItem("Item contains no images")

    def item_completed(self, results, item, info):
        # 遍历result这个2元素元组，检查图片路径是否为空
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no images")
        settings = self.spiderinfo.spider.settings
        item['image_paths'] = settings['FILES_STORE'] + image_paths[0]
        return item

    def file_path(self, request, response=None, info=None):
        item = request.meta['item']

        # start of deprecation warning block (can be removed in the future)
        def _warn():
            from scrapy.exceptions import ScrapyDeprecationWarning
            import warnings
            warnings.warn('FilesPipeline.file_key(url) method is deprecated, please use '
                          'file_path(request, response=None, info=None) instead',
                          category=ScrapyDeprecationWarning, stacklevel=1)

        # check if called from file_key with url as first argument
        if not isinstance(request, Request):
            _warn()
            url = request
        else:
            url = request.url

        # detect if file_key() method has been overridden
        if not hasattr(self.file_key, '_base'):
            _warn()
            return self.file_key(url)
        # end of deprecation warning block

        media_guid = item['user_name'] + '__' + item['title']  # change to request.url after deprecation
        media_ext = os.path.splitext(url)[1]  # change to request.url after deprecation
        filename = media_guid + media_ext
        # 剔除非法字符
        for c in self.invalidChar:
            filename = filename.replace(c, "")
        # 获取个settings真的这么麻烦吗？。。。
        settings = self.spiderinfo.spider.settings
        return '%s/%s/%s' % (settings['START_DATE'].strftime("%Y/%m/%d"), settings['MODE'],filename)
