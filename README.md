## QChatGPT项目，随机图片插件

[QChatGPT]:https://github.com/RockChinQ/QChatGPT

[ChatWaifu]:链接：https://pan.baidu.com/s/1UuBV2x0TQ7s90he6dQ-EjA?pwd=domi

### 项目插件安装方式

    方式一： 在QQ聊天窗口使用 !plugins 指令进行安装所有插件

    方式二： 下载此源码 ZIP 文件解压到 QChatGPT/plugins 目录下

### 使用说明

#### ChatWaifu语音转换插件

* 安装后自动启用无需配置

* __安装__
    + 下载并解压好[ChatWaifu]项目。
    + 移动 model 文件夹到 [QChatGPT] 项目根目录下。
    + 安装python库
  ```bash
  pip install numba librosa numpy scipy torch unidecode openjtalk>=0.3.0.dev2 jamo pypinyin jieba protobuf cn2an inflect eng_to_ipa ko_pron indic_transliteration num_thai opencc pyChatGPT vosk sounddevice miraicle
  ```
    + 即可完成安装使用。
    + 你可以在QchatGPT项根目录的config.py中配置语言模型。
      + 在QChatGPT根目录config.py的末尾添加
      ```python
      waifu_voice = 0
      """ 将你想要的语音模型填在上方的等号后面
      0       綾地寧々
      1       在原七海
      2       小茸
      3       唐乐吟
      4       随机
      """
      ```

#### Ranimg 插件：

* 在 ranimg/conf.xml 可以配置图片来源的 API
* 安装python库

```bash
pip install lxml parsel requests
```

* 在聊天窗口使用下面指令
  ```![ranimg|图片|壁纸] [PC|PE|R18|电脑|手机……]```来获取壁纸 ( PS:包含关键字即可 )

#### Galgame插件：

* 此插件需要一定的爬虫知识，自己写爬虫，也可以直接使用，不过目前只支持一个站点<kbd>量字ACG</kbd>，随心情更新吧 ψ(*｀ー´)ψ。
* 安装python库

```bash
pip install requests
```

* 在聊天窗口使用下面指令`![galgame|美少女游戏] [站点名(如：量子)] [要搜索的资源内容] [页面(可选)]`

#### BanList插件：

* 插件可以屏蔽匹配到的关键词不做处理，非常适合搭配其他框架使用的时候，屏蔽指令，避免回复过多（之后会单独开发一个插件）。
* 安装python库
* 在QChatGPT根目录的plugins/Banlist/banlist.yaml中配置屏蔽词

```bash
pip install pyYAML
```