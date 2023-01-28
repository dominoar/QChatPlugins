# -*- coding: utf-8 -*-
"""
@CreateTime     : 2023/1/17 18:42
@Author         : DominoAR and group(member_name)
@File           : main.py
@LastEditTime   : 
"""
import os
import platform
import re
import traceback

import mirai
import model.ChatWaifu.ChatWaifu_marai
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost

"""
接入ChatWaifu的语音生成程序，您需要将ChatWaifu文件夹放在model中
"""


def process_mod(answer):
    """
    :param answer 文本消息，转换为语音
    """

    try:
        # 删除已有的文件避免卡在命令行
        os.remove("output.pcm")
        os.remove("output.wav")
        os.remove("output.silk")
        if len(answer) > 100:
            return answer
        if re.search('[ぁ-んァ-ン]', answer):
            model.ChatWaifu.ChatWaifu_marai.generateSound(answer, language="jp")
        else:
            model.ChatWaifu.ChatWaifu_marai.generateSound("[ZH]" + answer + "[ZH]", language="ch")

        if platform.system() == "Linux":
            cmd = """ffmpeg -i .\\output.wav -f s16le .\\output.pcm & \
            .\\plugins\\ChatWaifu\\silk-v3-decoder\\converter.sh  .\\output.pcm .\\output.silk -tencent"""
        else:
            cmd = """.\\plugins\\ChatWaifu\\ffmpeg\\ffmpeg.exe -i .\\output.wav -f s16le .\\output.pcm & \
            .\\plugins\\ChatWaifu\\silk-v3-decoder\\windows\\silk_v3_encoder.exe .\\output.pcm .\\output.silk -tencent"""
        trans_ok = os.system(cmd)
        # 判断是否成功
        if trans_ok == 0:
            logging.info("语音silk生成成功！ヽ(￣▽￣)ﾉ")
        else:
            logging.error("""
            注意：语音可能生成失败！
            1、如果你是Linxu平台，请检查你是否安装了对应linux发行版的ffmpeg。
            2、将你的错误截图反馈给开发者(也就是我) @ Dominoar&多米诺艾尔
            """)

        ai_voice = mirai.Voice(path='output.silk')
        return ai_voice
    except FileNotFoundError:
        pass
    except Exception:
        traceback.print_exc()
        return ''


# 注册插件
@register(name="ChatWaifu", description="这是一个语音程序，可以让你的GPT3生成语音发送到QQ群里", version="0.1",
          author="多米诺艾尔")
class HelloPlugin(Plugin):

    # 插件加载时触发
    # plugin_host (pkg.plugin.host.PluginHost) 提供了与主程序交互的一些方法，详细请查看其源码
    def __init__(self, plugin_host: PluginHost):
        pass

    # 当收到文字消息时触发
    @on(NormalMessageResponded)
    def group_normal_message_received(self, event: EventContext, **kwargs):
        msg = kwargs["response_text"]
        if len(msg) < 100:
            voice = process_mod(msg)
            kwargs['host'].send_group_message(kwargs["launcher_id"], msg)
            kwargs['host'].send_group_message(kwargs["launcher_id"], voice)
            event.prevent_default()

    # 插件卸载时触发
    def __del__(self):
        pass
