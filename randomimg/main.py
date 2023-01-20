# -*- coding: utf-8 -*-
"""
@CreateTime     : 2023/1/9 17:33
@Author         : DominoAR
@File           : main.py
@LastEditTime   : 2023/1/11
"""
import base64
import logging
import os
import random
import re

import lxml.etree
import mirai
import requests

from plugins import headers
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost


# 基于QChatGPT实现的随机图片的机器人回复
class RandomImg:
    # api 接口队列
    api_item = {}
    # api 返回值处理队列
    api_ret_item = {}
    # 所有API名称
    all_api_name = []
    # 将随机在此处开始获取
    random_num = 0

    def __init__(self):
        # 载入配置文件……
        logging.debug('开始读取配置文件')
        this_file_path = os.getcwd()  # 当前文件的绝对路径
        config_file = open(file=this_file_path + '\\plugins\\randomimg\\conf.xml', mode='r', encoding='UTF-8')
        dom_root = lxml.etree.parse(config_file, lxml.etree.XMLParser())
        api_names = dom_root.xpath('//api/@api_name')
        self.all_api_name = api_names
        for api_name in api_names:
            # 获取图片API地址
            try:  # 随机 API图片URL
                dom_random_url = dom_root.xpath(f'//api[@api_name="{api_name}"]/api_url/random/text()')[0]
            except IndexError:
                dom_random_url = ''
            try:  # 随机 API图片参数
                dom_pc_url = dom_root.xpath(f'//api[@api_name="{api_name}"]/api_url/pc/text()')[0]
            except IndexError:
                dom_pc_url = ''
            try:
                dom_pe_url = dom_root.xpath(f'//api[@api_name="{api_name}"]/api_url/pe/text()')[0]
            except IndexError:
                dom_pe_url = ''
            try:
                dom_r18_url = dom_root.xpath(f'//api[@api_name="{api_name}"]/api_url/r18/text()')[0]
            except IndexError:
                dom_r18_url = ""

            self.api_item.update({api_name: {'random': {'url': dom_random_url},
                                             'pc': {'url': dom_pc_url},
                                             'pe': {'url': dom_pe_url},
                                             'r18': {'url': dom_r18_url}}})
        logging.debug('配置文件读取成功')
        self.random_num = random.randint(0, len(self.all_api_name) - 1)

    def _loop_random_image(self, random_num, type_img):
        """
        循环获取符合要求的API
        :program 指令队列
        :random_num 随机数值
        :type_img 图片类型(pc&pe&random)
        """
        random_number = random_num
        url = self.api_item[self.all_api_name[random_number]][type_img]['url']
        if url == "":
            for i in range(len(self.all_api_name)):
                try:
                    url = self.api_item[self.all_api_name[random_number]][type_img]['url']
                except IndexError:
                    random_number += 1
                if url != "":
                    break
                if random_number > len(self.all_api_name):
                    random_number = 0
                else:
                    random_number += 1
        if url == "":  # 如果找不到就随机返回壁纸
            url = self.api_item[self.all_api_name[0]]["random"]['url']
        return url

    def get_random_image(self, program: list):
        """
        获取随机图片
        : program 指令队列
        : reply 返回base64编码图片
        : return Base64 Images and image message
        """
        logging.debug('开始获取图片')
        # 判断获取图片类型
        if len(program) == 0 or program[0] == '':
            url = self._loop_random_image(self.random_num, 'random')
        elif re.search('pc|PC|电脑', program[0]):
            url = self._loop_random_image(self.random_num, 'pc')
        elif re.search('pe|PE|android|mobile|手机|安卓', program[0]):
            url = self._loop_random_image(self.random_num, 'pe')
        elif re.search('色图|涩图|成年人|养生|18', program[0]):
            url = self._loop_random_image(self.random_num, 'r18')
        elif re.search('random|随机', program[0]):
            url = self._loop_random_image(self.random_num, 'random')
        else:
            return [
                '[小猫bot]: "参数不正确!\n !ranimg|图片|壁纸 [pc|PC|电脑|pe|PE|android|mobile|手机|安卓|random|随机|……]"']
        while True:
            try:
                # 获取随机值来随机选择API
                resp = requests.get(url=url,
                                    headers=headers.get_random_ua())
                reply = [mirai.Image(base64=base64.b64encode(resp.content))]
                break
            except requests.exceptions.SSLError:
                pass
        return reply


def process_mod(program):
    reply = RandomImg().get_random_image(program)
    return reply


"""
在收到私聊或群聊消息"hello"时，回复"hello, <发送者id>!"或"hello, everyone!"
"""


# 注册插件
@register(name="Hello", description="hello world", version="0.1", author="RockChinQ")
class HelloPlugin(Plugin):

    # 插件加载时触发
    # plugin_host (pkg.plugin.host.PluginHost) 提供了与主程序交互的一些方法，详细请查看其源码
    def __init__(self, plugin_host: PluginHost):
        pass

    # 当收到个人消息时触发
    @on(PersonCommandSent)
    @on(GroupCommandSent)
    def person_normal_message_received(self, event: EventContext, **kwargs):
        if re.search('图片|壁纸|ranimg|要看', kwargs['command']):
            replay = process_mod(kwargs["params"])
            event.prevent_default()
            event.add_return('reply', replay)

    # 插件卸载时触发
    def __del__(self):
        pass
