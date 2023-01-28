# -*- coding: utf-8 -*-
"""
@CreateTime     : 2023/1/26 23:10
@Author         : DominoAR and group(member_name)
@File           : main.py.py
@LastEditTime   : 
"""
import os
import yaml
import re
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost


# 注册插件
@register(name="BanMassage", description="屏蔽插件，若匹配到关键词则屏蔽，不回复", version="0.1",
          author="多米诺艾尔")
class HelloPlugin(Plugin):

    # 插件加载时触发
    # plugin_host (pkg.plugin.host.PluginHost) 提供了与主程序交互的一些方法，详细请查看其源码
    def __init__(self, plugin_host: PluginHost):
        pass

    # 当收到文字消息时触发
    @on(GroupNormalMessageReceived)
    @on(PersonNormalMessageReceived)
    def group_normal_message_received(self, event: EventContext, **kwargs):
        try:
            msg = kwargs['text_message']
            file_path = os.path.join(os.path.dirname(__file__), 'banlist.yaml').replace("\\", "/")
            yaml_file = open(file_path, 'r', encoding='utf-8')
            yml_banlist = yaml.load(stream=yaml_file, Loader=yaml.CLoader)
            if yml_banlist['contain'] != '' and re.search(yml_banlist['contain'], msg):
                event.prevent_default()
            elif yml_banlist['regex'] != '' and re.search(yml_banlist['regex'], msg):
                event.prevent_default()
            else:
                for index, ban_text in enumerate(yml_banlist['perfect']):
                    if index >= len(yml_banlist['perfect']):
                        break
                    elif msg == ban_text:
                        event.prevent_default()
                        break
                    else:
                        continue
        except FileNotFoundError:
            logging.error("错误：未找到或无法读取banlist.yaml文件，您可以用管理员身份运行再次尝试")

    # 插件卸载时触发
    def __del__(self):
        pass
