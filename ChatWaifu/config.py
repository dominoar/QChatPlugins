# -*- coding: utf-8 -*-
"""
@CreateTime     : 2023/1/31 15:00
@Author         : DominoAR and group(member_name)
@File           : config.py.py
@LastEditTime   : 
"""

# 是否只发送语音(False/True)
# 默认False
only_voice = False

# 是否通过gocq发送语音消息(False/True)
# 此选项需要您部署GoCQ项目
# 如果你不知道这是什么，请勿更改
# 默认不开启(False)
gocq_voice = False

# gocq http连接地址
# 请确保您已经打开gocq的http协议
# 示例 gocq_url = "http://IP地址/端口号"
gocq_url = "http://127.0.0.1:5700"

# 在下方选择您的语音模型
# 默认为0，即是綾地寧々
waifu_voice = 0
"""
ID      Speaker
0       綾地寧々
1       在原七海
2       小茸
3       唐乐吟
4       随机
"""
