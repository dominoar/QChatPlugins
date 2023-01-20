# -*- coding: utf-8 -*-
"""
@CreateTime     : 2023/1/11 16:22
@Author         : DominoAR and group(member_name)
@File           : main.py
@LastEditTime   :
@该模组接入QChatGPT，拓展指令进行爬取资源，您可以在下面拓展您要爬取的玩网站并按照自己的方式进行返回
"""
import abc
import re

import parsel as parsel
import requests
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost

from plugins import headers


class GalgameSpider:
    search_url: str  # 搜索的主链接，不带参数

    @abc.abstractmethod
    def process(self, params, page):
        """
        爬虫类的入口函数，必须重写此函数

        :params 指令参数
        """
        pass


class LzacgGalgame(GalgameSpider):
    """量子ACG爬虫类"""
    search_url = 'https://lzacg.one/'

    def process(self, search_value, page='0'):
        replay = self._get_title_link(search_value, page)
        replay = [replay]  # 装载为列表，方便机器人进行回复
        return replay

    # 创建参数并请求
    def _get_title_link(self, search_value, page='0'):
        """获取搜索结果的资源"""
        replay = '为您找到以下结果 :'
        payload = {'s': search_value}  # 参数
        if page == '0':
            resp = requests.get(url=self.search_url, params=payload, headers=headers.get_random_ua())
        else:
            resp = requests.get(url=self.search_url + 'page/' + page, params=payload, headers=headers.get_random_ua())
        dom_root = parsel.Selector(resp.text)  # 解析响应
        dom_h2s = dom_root.css('.ajaxpager posts .item-thumbnail')
        res_links = dom_h2s.re('href="(.*?)"')
        res_titles = dom_h2s.re('alt="(.*?)"')
        if len(res_titles) == 0:
            return '呜呜~ 什么也没有找到呢 (T ^ T) '
        for index in range(len(res_titles)):
            res_titles[index] = re.sub(r'&amp;|【Galgame】|-量子ACG', '', res_titles[index])
            replay = replay + f'\n{str(index)}.{res_titles[index]}\n{res_links[index]}'
        return replay + '\n以上！好多游戏哇~！ヾ(✿ﾟ▽ﾟ)ノ'


regex_class = {'量子': 'LzacgGalgame', }


def process_mod(params):
    """插件入口"""
    if len(params) == 0 or params[0] == '':
        replay = ['小猫：不带参数的随机推荐将会在有生之年支持！(绝对不是我懒)']
        return replay
    else:
        for regex in regex_class.keys():
            if re.search(regex, params[0]):
                if len(params) == 3:
                    try:
                        if_page = int(params[2])
                    except Exception:
                        return ["页数不能为数字以外的字符哦"]
                    replay = globals()[regex_class.get(regex)]().process(params[1], params[2])  # 自动调用匹配的入口
                else:
                    replay = globals()[regex_class.get(regex)]().process(params[1])
                return replay
            else:
                replay = [f'小猫：指令错误！(；´д｀)ゞ\n !已经支持的站点{regex_class.keys()} 资源名称']
                return replay


@register(name="定向WEB资源爬取", description="#", version="0.1", author="多米诺艾尔")
class GalgamePlugin(Plugin):

    # 插件加载时触发
    # plugin_host (pkg.plugin.host.PluginHost) 提供了与主程序交互的一些方法，详细请查看其源码
    def __init__(self, plugin_host: PluginHost):
        pass

    @on(PersonCommandSent)
    @on(GroupCommandSent)
    def person_normal_message_received(self, event: EventContext, **kwargs):
        if re.search('galgame|美少女游戏', kwargs["command"]):
            replay = process_mod(kwargs["params"])
            # 输出调试信息
            logging.debug("hello, {}".format(kwargs['sender_id']))
            # 阻止该事件默认行为（向接口获取回复）
            event.prevent_default()
            event.add_return('reply', replay)

    # 插件卸载时触发
    def __del__(self):
        pass
