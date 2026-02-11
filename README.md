# AstrBot Voicevox Xingshuo Plugin

基于 [xingshuo](https://co2.de5.net) 接口的 Voicevox 语音合成插件。

## 功能
- `/vox <文本>`: 使用默认声线合成语音。
- `/vox -s <speaker_id> <文本>`: 使用指定声线 ID 合成语音。
- `/vox_list`: 获取所有可用声线及其 ID 列表。

## 配置
在 AstrBot 管理面板中可以配置以下参数：
- API 基础地址
- API Key
- 默认声线 ID
- 语速、音高、语调、音量等参数
- BGM 开关及音量

## 安装
将插件文件夹放入 AstrBot 的 `plugins` 目录下（容器环境下通常是 `/data/astrbot/01/plugins`），并确保环境中有 `httpx`。
```bash
pip install httpx
```
然后重启 AstrBot 即可。