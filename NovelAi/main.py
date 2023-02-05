# -*- coding: utf-8 -*-
"""
@CreateTime     : 2023/1/30 12:17
@Author         : DominoAR and group(member_name)
@File           : main.py.py
@LastEditTime   : 
"""
import asyncio
import json
import os
import re
import sqlite3
import time
import traceback
from logging import Logger, StreamHandler
from typing import Optional, List

import requests
import yaml
from aiohttp import ClientSession

from pkg.plugin.host import PluginHost, EventContext
from pkg.plugin.models import *
from plugins.NovelAi.novelai_api.BanList import BanList
from plugins.NovelAi.novelai_api.BiasGroup import BiasGroup
from plugins.NovelAi.novelai_api.GlobalSettings import GlobalSettings
from plugins.NovelAi.novelai_api.NovelAI_API import NovelAIAPI
from plugins.NovelAi.novelai_api.Preset import Model, Preset
from plugins.NovelAi.novelai_api.Tokenizer import Tokenizer
from plugins.NovelAi.novelai_api.utils import get_encryption_key, b64_to_tokens


class API:
    _username: str
    _password: str
    _session: ClientSession

    logger: Logger
    api: Optional[NovelAIAPI]

    def __init__(self):
        config_dict = yaml.load(open(f'{os.getcwd()}/plugins/NovelAi/config.yaml', mode='r', encoding='utf-8').read(),
                                yaml.CLoader)

        self._username = config_dict['account']['user']
        self._password = config_dict['account']['password']
        if self._username is None or self._password is None:
            raise RuntimeError("NovelAi：账号或密码错误，账号或密码不能为空，且必须为字符串")
        if self._username == "" or self._password == "":
            raise RuntimeError("NovelAi：账号或密码错误，账号或密码不能为空")

        self.logger = Logger("NovelAI")
        self.logger.addHandler(StreamHandler())

        self.api = NovelAIAPI(logger=self.logger)

    @property
    def encryption_key(self):
        return get_encryption_key(self._username, self._password)

    async def __aenter__(self):
        self._session = ClientSession()
        await self._session.__aenter__()

        self.api.attach_session(self._session)
        await self.api.high_level.login(self._username, self._password)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.__aexit__(exc_type, exc_val, exc_tb)


class NovelAiStory:
    """NovelAi故事插件的功能类"""
    # 故事会话池
    story_pool = {}
    username: str
    password: str
    mode: str
    text_length: int
    banlist: list

    def __init__(self):
        # 读取配置文件
        logging.debug("NovelAi：开始读取配置文件")
        try:
            this_path = os.getcwd()
            config_dict = yaml.load(open(f'{this_path}/plugins/NovelAi/config.yaml', mode='r', encoding='utf-8').read(),
                                    yaml.CLoader)
            self.username = config_dict['account']['user']
            self.password = config_dict['account']['password']
            self.mode = config_dict['story']['mode']
            self.text_length = config_dict['story']['text_length']
            self.banlist = config_dict['story']['banlist']
        except Exception:
            traceback.print_exc()
            raise RuntimeError("NovelAi：读取文件失败，请检查配置文件是否正确")

    async def process_mod(self, massage):
        """入口函数"""
        reply = await self.get_novel_reply(massage)
        return reply

    async def get_novel_reply(self, massage):
        """获取novelai的回复"""
        async with API() as api_handler:
            api = api_handler.api
            logger = api_handler.logger
            if self.mode == "Euterpe":
                model = Model.Euterpe
            elif self.mode == "Sigurd":
                model = Model.Sigurd
            elif self.mode == "Krake":
                model = Model.Krake
            prompt = massage
            preset = Preset.from_default(model)
            preset["max_length"] = self.text_length
            global_settings = GlobalSettings(num_logprobs=GlobalSettings.NO_LOGPROBS)
            global_settings["bias_dinkus_asterism"] = True
            ban_words = BanList()
            for word in self.banlist:
                ban_words.add(word)
            bad_words: Optional[BanList] = ban_words
            bias_groups: List[BiasGroup] = []
            bias_group1 = BiasGroup(0.00)
            bias_group2 = BiasGroup(0.00)
            if bias_groups:
                bias_group1.add("very", " very", " slightly", " incredibly", " enormously", " loudly")
                bias_group1 += " proverbially"
                bias_group2 += " interestingly"
                bias_group2 += " brutally"
            module = None
            gen = await api.high_level.generate(prompt, model, preset, global_settings, bad_words, bias_groups,
                                                module)
            reply_msg = Tokenizer.decode(model, b64_to_tokens(gen["output"]))
            return reply_msg


# 记录会话novelai story的开启状态
# 存在号码即是开启，反之关闭
novel_status = []


@register(name="NovelAI故事插件~", description="#", version="0.1", author="多米诺艾尔")
class NovalAiStoryPlugins(Plugin):
    sqlite = None
    cursor = None

    def __init__(self, plugin_host: PluginHost):
        asyncio.set_event_loop(asyncio.new_event_loop())
        # 加载配置文件
        with open(f'{os.getcwd()}/plugins/NovelAi/config.yaml', mode='r', encoding='UTF-8') as novel_conf_file:
            self.novel_config = yaml.load(novel_conf_file.read(), yaml.CLoader)
        # 创建novel故事Ai
        self.novel_story = NovelAiStory()
        # 创建异步loop
        self.async_loop = asyncio.get_event_loop()
        # 初始化数据库
        self.sqlite = sqlite3.connect(f"{os.getcwd()}/database.db")
        self.cursor = self.sqlite.cursor()
        create_tb_sql = '''
                            CREATE TABLE IF NOT EXISTS novel_content (
                            person_id int,
                            type varchar(10),
                            datatime integer,
                            content varchar(8000));
                            '''
        self.cursor.execute(create_tb_sql)
        self.sqlite.commit()
        self.cursor.close()
        self.sqlite.close()

    @on(PersonNormalMessageReceived)
    @on(GroupNormalMessageReceived)
    def normal_message_received(self, event: EventContext, **kwargs):
        person_id = kwargs['launcher_id']
        person_msg = kwargs['text_message']
        if person_id in novel_status:
            # 获取接下来需要使用到的各个参数
            launcher_type = kwargs['launcher_type']
            language = self.novel_config.get('story').get('language')
            trans_choice = self.novel_config.get("Translate").get("your_choice")
            # 数据库
            self.sqlite = sqlite3.connect(f"{os.getcwd()}/database.db")
            self.cursor = self.sqlite.cursor()
            # 翻译用户输入的中文文本消息 -> 英文
            if language == 'zh':
                en_trans_msg = translate_chinese_check(trans_choice, person_msg, 1, novel_config=self.novel_config)
            else:
                en_trans_msg = person_msg
            # 获取用户content文本
            person_content = self._get_db_contents(person_id, en_trans_msg, launcher_type)
            # 开始获取NovelAi回复(异步)
            novel_task = self.async_loop.create_task(self.novel_story.process_mod(person_content))
            self.async_loop.run_until_complete(novel_task)
            reply = novel_task.result()
            # 将回复写入数据库
            self._set_db_content(person_id, context=person_content + reply)
            self._delete_db_timeout()
            # 翻译NovelAi的回复
            if language == 'zh':
                zh_trans_reply = translate_chinese_check(trans_choice, reply, 0, novel_config=self.novel_config)
                event.add_return("reply", [zh_trans_reply])
            else:
                event.add_return("reply", reply)
            event.prevent_default()

    @on(GroupCommandSent)
    @on(PersonCommandSent)
    def command_sent_event(self, event: EventContext, **kwargs):
        cmd = kwargs.get('command')
        params_list = kwargs.get('params')
        if re.search('story|故事', cmd):
            self.sqlite = sqlite3.connect(f"{os.getcwd()}/database.db")
            self.cursor = self.sqlite.cursor()
            if_admin = not kwargs.get('is_admin')
            launcher_id = kwargs.get('launcher_id')
            # 指令列表必须大于0
            if len(params_list) > 0:
                if re.search('^reset|^重置会话', params_list[0]):
                    if len(params_list) == 1:
                        self._reset_one_db_session(launcher_id=launcher_id)
                        event.add_return("reply", ["已完成重置个人会话"])
                    elif len(params_list) == 2 and re.match('^all|^全部', params_list[1]) and if_admin:
                        self._reset_all_db_session()
                        event.add_return("reply", ["已完成重置所有会话"])
                    else:
                        if not if_admin:
                            event.add_return("reply", ["哼~ 这个功能只有管理员才能用你不知道吗？(ｰ̀дｰ́)"])
                        else:
                            event.add_return("reply", ["笨蛋！参数错啦,这一级指令只有[all|全部]可用！"])
                elif re.match('^start|^启|^开', params_list[0]):
                    if novel_status.count(launcher_id):
                        event.add_return("reply", ["你已经进入故事模式~ ヾ(✿ﾟ▽ﾟ)ノ"])
                    else:
                        novel_status.append(launcher_id)
                        event.add_return("reply", ["成功进入故事模式~ ヾ(✿ﾟ▽ﾟ)ノ"])
                elif re.match('^stop|^停|^退|^关', params_list[0]):
                    if novel_status.count(launcher_id) == 0:
                        event.add_return("reply", ["你从未进入故事模式"])
                    else:
                        novel_status.remove(launcher_id)
                        event.add_return("reply", ["成功退出故事模式 |ू･ω･` )"])
                else:
                    event.add_return("reply", ["你是不是傻(￣.￣),这一级指令只有[reset|start|stop]可用哦~"])
            else:
                event.add_return("reply", ["用法：!story [reset(重置会话) start(开启故事模式) stop(关闭故事模式)]"])
            event.prevent_default()

    # 下面是数据库操作
    def _set_db_content(self, person_id, context):
        if len(context) > 8000:  # context不能超过8000个字符,否则重置到4000
            context = context[4000:]
        if re.search(r'\.$', context) is None:
            context += '.'
        context = re.sub('\n', '.', context)
        # 字符串sql转义单，双引号
        context = re.sub('"', '“', context)
        context = re.sub("'", '”', context)
        sql = """
            UPDATE novel_content
            SET content = '%s' , datatime = %s
            WHERE person_id = '%s';
            """ % (context, int(time.time()), person_id)
        self.cursor.execute(sql)
        self.sqlite.commit()

    def _get_db_contents(self, person_id, person_msg, launcher_type):
        """
        获取目标成员的文本,如果没有该成员则创建一个成员
        :param person_id: 消息发送者
        :param person_msg: 消息内容
        :param launcher_type: 消息源自于(私聊/群组)
        """
        select_sql = """
            SELECT content FROM novel_content WHERE person_id = %s;
            """ % person_id
        contents = self.cursor.execute(select_sql)
        context = contents.fetchone()
        if context:
            context = context[0]
            context = re.sub('“', '"', context)
            context = re.sub("”", "'", context)
            return context + person_msg
        else:  # 如果是第一次会话
            person_msg = re.sub('"', '“', person_msg)
            person_msg = re.sub("'", '”', person_msg)
            crete_sql = """
            INSERT INTO novel_content (person_id, content,type,datatime) VALUES (%s,'%s','%s',%s)
            """ % (person_id, person_msg, launcher_type, int(time.time()))
            self.cursor.execute(crete_sql)
            self.sqlite.commit()
            return person_msg

    def _delete_db_timeout(self):
        """删除超过20分钟的数据"""
        delete_sql = """
            DELETE FROM novel_content WHERE datatime < %s
            """ % (int(time.time()) - 1200)
        self.cursor.execute(delete_sql)
        self.sqlite.commit()

    def _reset_all_db_session(self):
        """删除所有数据库会话"""
        delete_sql = """
            DELETE FROM novel_content WHERE TRUE
            """
        self.cursor.execute(delete_sql)
        self.sqlite.commit()

    def _reset_one_db_session(self, launcher_id):
        """
        删除某一个人(群聊)的会话
        :param launcher_id: 发送消息的人(群)的号码
        """
        delete_sql = """
            DELETE FROM novel_content WHERE person_id = %s
            """ % launcher_id
        self.cursor.execute(delete_sql)
        self.sqlite.commit()

    @staticmethod
    def baiduTranslate(novel_config, translate_text, flag=1) -> str:
        """
        :param translate_text: 待翻译的句子，字数小于2000
        :param flag: 1:英文->中文; 0:中文->英文;
        :param novel_config: novelAI配置文件
        :return: 成功：返回服务器结果。失败：返回服务器失败原因。
        """
        baidu_trans_conf = novel_config.get('Translate').get('baidu')
        api_key = baidu_trans_conf.get('apikey')
        api_secret = baidu_trans_conf.get('api_secret')
        # 获取百度access_token
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": api_key, "client_secret": api_secret}
        access_token = str(requests.post(url, params=params).json().get("access_token"))
        # 开始翻译
        url = "https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1?access_token=" + access_token
        if flag:
            payload = json.dumps({
                "from": "en",
                "to": "zh",
                "q": translate_text
            })
        else:
            payload = json.dumps({
                "from": "zh",
                "to": "en",
                "q": translate_text
            })

        baidu_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        resp = requests.request("POST", url, headers=baidu_headers, data=payload)
        resp_json = json.loads(resp.content)
        if resp_json.get('error_code'):
            logging.error(
                f"[NovelAi]: 百度翻译错误，错误码：{resp_json.get('error_code')}，错误信息：{resp_json.get('error_msg')}")
        return resp_json.get('result').get('trans_result')[0].get('dst')

    @staticmethod
    def googleTranslate(novel_config, translate_text, flag=1) -> str:
        """谷歌机器翻译,或许需要挂系统代理？
      :param translate_text: 待翻译的句子，字数小于15K
      :param flag: 1:英文->中文; 0:中文->英文;
      :param novel_config: novelAI配置文件
      :return: 成功：返回服务器结果。失败：你猜猜会怎么样？
      """
        from pygoogletranslation import Translator
        # 翻译对象
        translator = Translator()
        # 获取最大尝试次数
        max_number = novel_config.get("Translate").get("google").get("try_number")
        if max_number is None:
            max_number = 10
        # 判断中英文
        if flag:
            language_dest = 'en'
        else:
            language_dest = 'zh-cn'
        # 翻译处理
        t = 0
        if max_number is None:
            max_number = 10
        # 请求翻译，直到成功或超出max_number
        while True:
            try:
                t = (translator.translate([f"{translate_text}", "."], dest=language_dest))
            except Exception as e:
                t += 1
                logging.warning(f"[NovelAi]: 谷歌第{t}次翻译错误：{e}\n[NovelAi]: 正在尝试第{t + 1}次")
            if type(t) is not int or t > max_number:
                break
        return t[0].text

    # 插件卸载时触发
    def __del__(self):
        self.async_loop.close()
        self.cursor.close()
        self.sqlite.close()


# 全局函数

def translate_chinese_check(trans_choice, translate_text, flag, novel_config):
    """翻译接口的判断，判断使用哪一个翻译接口
    :param translate_text: 要翻译的文本
    :param trans_choice: 选择的翻译接口: "百度" "谷歌"
    :param flag: 1:英文->中文; 0:中文->英文;
    :param novel_config: novelAI配置文件
    """
    if re.match('^baidu|^百度', trans_choice):
        en_trans_msg = NovalAiStoryPlugins.baiduTranslate(novel_config, translate_text, flag)
    elif re.match('^google|^谷歌', trans_choice):
        en_trans_msg = NovalAiStoryPlugins.googleTranslate(novel_config, translate_text, flag)
    else:
        logging.warning("[NovelAi]: 无法获取到你选择的翻译,默认为你使用谷歌翻译")
        en_trans_msg = NovalAiStoryPlugins.googleTranslate(novel_config, translate_text, flag)
    return en_trans_msg
