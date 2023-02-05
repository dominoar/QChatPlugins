# -*- coding: utf-8 -*-
"""
@CreateTime     : 2023/1/17 18:42
@Author         : DominoAR and group(member_name)
@File           : main.py
@LastEditTime   : 
"""
import base64
import hashlib
import os
import platform
import re
import traceback

import mirai
import requests

import model.ChatWaifu.ChatWaifu_marai
import plugins.ChatWaifu.config as waifu_config
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost

"""
接入ChatWaifu的语音生成程序，您需要将ChatWaifu文件夹放在model中
"""


def process_mod(answer, sender_id):
    """
    :param answer 文本消息，转换为语音
    """

    try:
        if len(answer) > 100:
            return answer
        if re.search('[ぁ-んァ-ン]', answer):
            model.ChatWaifu.ChatWaifu_marai.generateSound(answer, language="jp", old_msg=answer,
                                                          sender_id=sender_id)
        else:
            model.ChatWaifu.ChatWaifu_marai.generateSound("[ZH]" + answer + "[ZH]", old_msg=answer, language="ch",
                                                          sender_id=sender_id)

        # 获取随机生成的语音命名号码
        hash_key = hashlib.md5((str(sender_id) + answer).encode()).hexdigest()
        the_file_path = os.getcwd()
        voice_wav = f'{the_file_path}\\voice-file\\voice_{hash_key}.wav'
        voice_pcm = f'{the_file_path}\\voice-file\\voice_{hash_key}.pcm'
        voice_silk = f'{the_file_path}\\voice-file\\voice_{hash_key}.silk'

        # 执行命令转换为手机可以收听的语音
        if platform.system() == "Linux":
            cmd = f"""ffmpeg -i {voice_wav} -f s16le {voice_pcm} & \
            .\\plugins\\ChatWaifu\\silk-v3-decoder\\converter.sh  {voice_pcm} {voice_silk} -tencent"""
        else:
            cmd = f""".\\plugins\\ChatWaifu\\ffmpeg\\ffmpeg.exe -i {voice_wav} -f s16le {voice_pcm} & \
            .\\plugins\\ChatWaifu\\silk-v3-decoder\\windows\\silk_v3_encoder.exe {voice_pcm} {voice_silk} -tencent"""
        trans_ok = os.system(cmd)
        # 判断是否成功
        if trans_ok == 0:
            logging.info("语音silk生成成功！ヽ(￣▽￣)ﾉ")
            try:
                os.remove(voice_wav)
                os.remove(voice_pcm)
            except FileNotFoundError:
                logging.warning("警告：未找到应该删除的wav与pcm语音文件")
            except Exception:
                traceback.print_exc()
        else:
            logging.error("""
            注意：语音可能生成失败！
            1、如果你是Linxu平台，请检查你是否安装了对应linux发行版的ffmpeg。
            2、将你的错误截图反馈给开发者(也就是我) @ Dominoar&多米诺艾尔
            """)

        ai_voice = mirai.Voice(path=voice_silk)
        return ai_voice
    except Exception:
        traceback.print_exc()
        return ''


# 注册插件
@register(name="ChatWaifu", description="这是一个语音程序，可以让你的GPT3生成语音发送到QQ群里", version="0.2",
          author="多米诺艾尔")
class HelloPlugin(Plugin):

    # 插件加载时触发
    # plugin_host (pkg.plugin.host.PluginHost) 提供了与主程序交互的一些方法，详细请查看其源码
    def __init__(self, plugin_host: PluginHost):
        try:
            os.mkdir(f"{os.getcwd()}\\voice-file")
        except Exception:
            pass

    # 当收到文字消息时触发
    @on(NormalMessageResponded)
    def group_normal_message_received(self, event: EventContext, **kwargs):
        msg = kwargs["response_text"]
        msg = re.sub(r'<\|im_end\|>', '', msg)
        launcher_type = kwargs['launcher_type']
        launcher_id = kwargs['launcher_id']
        self_host = kwargs['host']
        sender_id = kwargs['sender_id']
        # 如果配置了gocq则私聊也通过，否则只能通过群组
        if len(msg) < 100 and (waifu_config.gocq_voice or re.search('[gG]', launcher_type)):
            voice = process_mod(msg, sender_id)
            # 如果配置了GoCQ连接，则使用GoCQ发送消息
            if waifu_config.gocq_voice:
                self._send_gocq_message_voice(launcher_type, msg, launcher_id,
                                              waifu_config.gocq_url, sender_id=sender_id)
                if not waifu_config.only_voice:
                    self._send_gocq_message(launcher_type, launcher_id, msg,
                                            waifu_config.gocq_url)
            else:
                # 使用QChatGPT提供的插件host发送消息
                self_host.send_group_message(launcher_id, voice)
                if not waifu_config.only_voice:
                    self_host.send_group_message(launcher_id, msg)
            event.prevent_default()

    # 插件卸载时触发
    def __del__(self):
        pass

    def _send_gocq_message_voice(self, launcher_type, msg, launcher_id, gocq_url, sender_id):
        """
            launcher_type: 发送消息的类型(group/person)
            launcher_id: 发送消息的群号/QQ号
            msg: 发送的消息
            gocq_url: gocq的http地址，如(http://ip地址:/端口号)
            sender_id: 发送者的QQ号
            """

        # 读取silk语音数据
        hash_key = hashlib.md5((str(sender_id) + msg).encode()).hexdigest()

        with open(os.getcwd() + f'/voice-file/voice_{hash_key}.silk', 'rb') as voice_file:
            voice_base64 = base64.b64encode(voice_file.read())
            voice_base64 = voice_base64.decode('utf-8')
            voice_file.close()

        # 判断消息发送是否为聊群,并定义消息体
        if re.search('[gG]', launcher_type):
            gocq_url = gocq_url + '/send_group_msg'
            data = {"group_id": launcher_id,
                    "message": f"[CQ:record,file=base64://{voice_base64}]"}
        else:
            gocq_url = gocq_url + '/send_private_msg'
            data = {"user_id": launcher_id,
                    "message": f"[CQ:record,file=base64://{voice_base64}]"}
        # 删除用过的silk文件
        os.remove(os.getcwd() + f'/voice-file/voice_{hash_key}.silk')
        # 发送请求
        requests.post(gocq_url, params=data)
        return 0

    def _send_gocq_message(self, launcher_type, launcher_id, msg, gocq_url):
        """
        launcher_type: 发送消息的类型(group/person)
        launcher_id: 发送消息的群号/QQ号
        msg: 发送的消息
        gocq_url: gocq的http地址，如(http://ip地址:/端口号)
        """

        # 判断消息发送是否为聊群,并定义消息体
        if re.search('[gG]', launcher_type):
            gocq_url = gocq_url + '/send_group_msg'
            data = {"group_id": launcher_id,
                    "message": msg}
        else:
            gocq_url = gocq_url + '/send_private_msg'
            data = {"user_id": launcher_id,
                    "message": msg}

        # 发送请求
        requests.post(gocq_url, params=data)
        return 0
