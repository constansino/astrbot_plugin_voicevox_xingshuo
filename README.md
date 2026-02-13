# AstrBot Voicevox Xingshuo Plugin

基于 [xingshuo](https://co2.de5.net) 接口的 Voicevox 语音合成插件。

## 当前版本说明
本插件当前采用“预设编号”模式，不再使用 `/vox -s <speaker_id> <文本>` 这种旧写法。

请使用以下指令：
- `/vox<N>config [参数=值 ...]`
- `/vox<N> <文本>`
- `/voxconfigls`
- `/vox_list`
- `/vox_help`

其中 `<N>` 为预设编号（正整数），例如 `1`、`2`、`10`。

## 指令详解

### 1. 配置或查看预设
`/vox<N>config [参数=值 ...]`

用途：创建/更新指定编号预设，或查看该预设的当前配置。

示例：
- 查看预设 1：`/vox1config`
- 仅修改部分参数（增量覆写）：`/vox1config bgm=1 spd=1.1 pit=0.05`
- 创建预设 2：`/vox2config s=36 vol=1.2`

说明：
- 支持“增量更新”，只会修改你传入的键，未传入的参数保持原值。
- 预设会持久化保存到 `data/voicevox_xingshuo/presets.json`。

参数映射：
- `s` -> `speaker`（声线 ID，整数）
- `spd` -> `speedScale`（语速，浮点）
- `pit` -> `pitchScale`（音高，浮点）
- `int` -> `intonationScale`（语调起伏，浮点）
- `vol` -> `volumeScale`（人声音量，浮点）
- `bgm` -> `bgmEnabled`（BGM 开关：`1/0`、`true/false`、`on/off`）
- `bgmv` -> `bgmVolume`（BGM 音量，浮点）

### 2. 调用预设进行语音合成
`/vox<N> <文本>`

用途：使用预设 `<N>` 对文本进行合成并返回语音。

示例：
- `/vox1 你好，这是预设一。`
- `/vox2 今天想听低语版本。`

注意：
- 如果对应预设不存在，会提示先执行 `/vox<N>config ...`。

### 3. 列出所有已保存预设
`/voxconfigls`

用途：汇总显示当前已保存预设及核心参数（声线、语速、音高、BGM 状态等）。

### 4. 查看可用声线列表
`/vox_list`

用途：从接口拉取可用声线及 style ID，供 `s=<speaker_id>` 配置时参考。

### 5. 查看内置完整帮助
`/vox_help`

用途：返回插件内置 Markdown 帮助文本。

## 快速上手
1. 先拉声线列表：`/vox_list`
2. 创建预设 1：`/vox1config s=22 spd=1.1 bgm=1 bgmv=0.25`
3. 直接调用：`/vox1 这是一段测试语音。`
4. 需要微调时继续覆写：`/vox1config pit=0.03 vol=1.15`

## 兼容性与旧文档声明
- 旧写法 `/vox <文本>` 与 `/vox -s <speaker_id> <文本>` 已不作为当前主用接口。
- 如你在其他文档中看到旧写法，请以本 README 与 `/vox_help` 为准。

## 依赖
- `httpx`

安装示例：
```bash
pip install httpx
```
