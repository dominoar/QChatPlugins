# -*- coding: utf-8 -*-
"""
@CreateTime     : 2023/1/17 18:42
@Author         : DominoAR and group(member_name)
@File           : main.py
@LastEditTime   : 
"""
import model.ChatWaifu.ChatWaifu_marai
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost

"""
接入ChatWaifu的语音生成程序，您需要将ChatWaifu文件夹放在model中
"""


# 注册插件
@register(name="ChatWaifu", description="这是一个语音程序，可以让你的GPT3生成语音发送到QQ群里", version="0.1",
          author="多米诺艾尔")
class HelloPlugin(Plugin):

    # 插件加载时触发
    # plugin_host (pkg.plugin.host.PluginHost) 提供了与主程序交互的一些方法，详细请查看其源码
    def __init__(self, plugin_host: PluginHost):
        pass

    # 当收到群消息时触发
    @on(NormalMessageResponded)
    def group_normal_message_received(self, event: EventContext, **kwargs):
        msg = kwargs["response_text"]
        if len(msg) < 100:
            voice = model.ChatWaifu.ChatWaifu_marai.process_mod(msg)
            kwargs['host'].send_group_message(kwargs["launcher_id"], msg)
            kwargs['host'].send_group_message(kwargs["launcher_id"], voice)
        event.prevent_default()

    # 插件卸载时触发
    def __del__(self):
        pass
