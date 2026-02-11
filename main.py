import httpx
import os
import uuid
import re
import json
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.event.filter import EventMessageType
from astrbot.api.message_components import *
from astrbot.api import logger

@register("astrbot_plugin_voicevox_xingshuo", "Gemini", "星烁语音 (Voicevox) 全量指南终极版", "v1.2.1")
class VoicevoxPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.base_url = "https://co2.de5.net"
        self.api_key = "xingshuo"
        self.data_dir = os.path.join("data", "voicevox_xingshuo")
        self.preset_path = os.path.join(self.data_dir, "presets.json")
        self.presets = self._load_presets()
        logger.info("[vox] 插件 v1.2.1 初始化完成，全量帮助文档已就绪")

    def _load_presets(self):
        if os.path.exists(self.preset_path):
            try:
                with open(self.preset_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception: return {}
        return {}

    def _save_presets(self):
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            with open(self.preset_path, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, ensure_ascii=False, indent=4)
        except Exception: pass

    def _detect_mode(self, text: str) -> str:
        if re.search(r'[\u4e00-\u9fa5]', text): return "pseudo_jp"
        if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text): return "raw"
        return "pseudo_jp"

    @filter.event_message_type(filter.EventMessageType.ALL, priority=2000)
    async def on_all_msg(self, event: AstrMessageEvent):
        raw_msg = event.message_str.strip()
        msg = raw_msg if raw_msg.startswith("/") else "/" + raw_msg
        
        if not msg.lower().startswith("/vox"):
            return

        # 1. 全量帮助 (Markdown)
        if msg.lower().startswith("/vox_help"):
            event.set_result(event.plain_result(self._get_full_help_md()))
            return

        # 2. 列出所有预设配置
        if msg.lower().startswith("/voxconfigls"):
            await self._on_vox_config_ls(event)
            return

        # 3. 声线列表
        if msg.lower().startswith("/vox_list"):
            await self._on_vox_list(event)
            return

        # 4. 配置指令 /vox(\d+)config
        config_match = re.match(r'^/vox(\d+)config(?:\s+(.*))?$', msg, re.IGNORECASE)
        if config_match:
            pid, params = config_match.groups()
            await self._on_config(event, pid, params)
            return

        # 5. 调用指令 /vox(\d+) <text>
        call_match = re.match(r'^/vox(\d+)\s+(.*)$', msg, re.IGNORECASE | re.DOTALL)
        if call_match:
            pid, text = call_match.groups()
            await self._on_preset_call(event, pid, text)
            return

    async def _on_vox_config_ls(self, event: AstrMessageEvent):
        if not self.presets:
            event.set_result(event.plain_result("💡 目前还没有保存任何预设哦。"))
            return
        msg = "📋 **Voicevox 已保存预设汇总**：\n"
        for pid, conf in sorted(self.presets.items(), key=lambda x: int(x[0])):
            bgm = "ON" if conf.get("bgmEnabled") else "OFF"
            msg += f"• **预设 {pid}**: ID={conf.get('speaker')} | 速={conf.get('speedScale')} | 音={conf.get('pitchScale')} | BGM={bgm}\n"
        event.set_result(event.plain_result(msg))

    async def _on_config(self, event: AstrMessageEvent, pid: str, params_str: str):
        existing_conf = self.presets.get(pid, {
            "speaker": 22, "speedScale": 1.0, "pitchScale": 0.0, 
            "intonationScale": 1.0, "volumeScale": 1.0,
            "bgmEnabled": False, "bgmVolume": 0.35
        })
        if not params_str:
            conf_str = json.dumps(existing_conf, indent=2, ensure_ascii=False)
            event.set_result(event.plain_result(f"🔍 预设 {pid} 详细配置：\n{conf_str}"))
            return
        mapping = {'s': 'speaker', 'spd': 'speedScale', 'pit': 'pitchScale', 'int': 'intonationScale', 'vol': 'volumeScale', 'bgm': 'bgmEnabled', 'bgmv': 'bgmVolume'}
        pairs = re.findall(r'(\w+)=([\w\d\.\-]+)', params_str)
        if not pairs:
            event.set_result(event.plain_result("❌ 格式错误。示例：/vox1config bgm=1 spd=1.1"))
            return
        for k, v in pairs:
            if k.lower() in mapping:
                rk = mapping[k.lower()]
                try:
                    if rk == 'bgmEnabled': existing_conf[rk] = v.lower() in ['true', '1', 'on']
                    elif rk == 'speaker': existing_conf[rk] = int(v)
                    else: existing_conf[rk] = float(v)
                except: continue
        self.presets[pid] = existing_conf
        self._save_presets()
        event.set_result(event.plain_result(f"✅ 预设 {pid} 已增量更新并持久化保存。"))

    async def _on_preset_call(self, event: AstrMessageEvent, pid: str, text: str):
        conf = self.presets.get(pid)
        if not conf:
            event.set_result(event.plain_result(f"❌ 预设 {pid} 未配置。请使用 /vox{pid}config s=22 等进行设置。"))
            return
        mode = self._detect_mode(text)
        payload = {
            "text": text, "speaker": int(conf.get("speaker", 22)), "mode": mode,
            "speedScale": float(conf.get("speedScale", 1.0)), "pitchScale": float(conf.get("pitchScale", 0.0)),
            "intonationScale": float(conf.get("intonationScale", 1.0)), "volumeScale": float(conf.get("volumeScale", 1.0)),
            "prePhonemeLength": 0.1, "postPhonemeLength": 0.1, "outputSamplingRate": 24000, "outputStereo": False,
            "kana": "", "bgmEnabled": bool(conf.get("bgmEnabled", False)), "bgmVolume": float(conf.get("bgmVolume", 0.35))
        }
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.base_url}/tts", json=payload, headers=headers, timeout=60)
                if resp.status_code == 200:
                    fpath = os.path.join(self.data_dir, f"tts_{uuid.uuid4()}.wav")
                    with open(fpath, "wb") as f: f.write(resp.content)
                    event.set_result(event.chain_result([Record(file=fpath)]))
                else: event.set_result(event.plain_result(f"❌ 合成失败 ({resp.status_code})"))
        except Exception as e: event.set_result(event.plain_result(f"❌ 异常: {e}"))

    async def _on_vox_list(self, event: AstrMessageEvent):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/voices", headers={"X-API-Key": self.api_key}, timeout=10)
                if resp.status_code == 200:
                    msg = "🎙️ **Voicevox 声线全列表**\n"
                    for char in resp.json():
                        styles = " ".join([f"{s['name']}({s['id']})" for s in char.get('styles', [])])
                        msg += f"• **{char['name']}**: {styles}\n"
                    event.set_result(event.plain_result(msg[:2500]))
        except: event.set_result(event.plain_result("❌ 列表拉取失败"))

    def _get_full_help_md(self):
        return (
            "# 🎙️ 星烁语音 (Voicevox) 终极使用指南\n\n"
            "本插件支持无限动态预设，自动识别中日双语并应用“拟音”优化。\n\n"
            "### 1️⃣ 预设配置 (Config)\n"
            "**指令**: `/vox<N>config [参数=值 ...]`\n"
            "- **查询当前**: `/vox1config` (不带参数)\n"
            "- **增量更新**: `/vox1config bgm=1 pit=0.05` (仅改BGM和音高，其它不变)\n\n"
            "**📚 参数映射表**:\n"
            "| 简写 | 参数全名 | 说明 | 建议范围 |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| `s` | `speaker` | 声线 ID | 见 `/vox_list` |\n"
            "| `bgm` | `bgm` | BGM 开关 | `1`(开) / `0`(关) |\n"
            "| `bgmv`| `bgmv` | BGM 音量 | `0.2 ~ 0.45` |\n"
            "| `pit` | `pitch` | 音高 (粗细) | `-0.15 ~ 0.15` |\n"
            "| `spd` | `speed` | 语速 (快慢) | `0.8 ~ 1.4` |\n"
            "| `int` | `intonation`| 语调起伏 | `0.8 ~ 1.3` |\n"
            "| `vol` | `volume` | 人声音量 | `0.8 ~ 1.4` |\n\n"
            "### 2️⃣ 调用合成 (Call)\n"
            "**指令**: `/vox<N> <文本>`\n"
            "- 示例: `/vox1 这是一个全参数预设测试。` \n\n"
            "### 3️⃣ 预设概览 (List)\n"
            "**指令**: `/voxconfigls` \n"
            "- 作用: 列出所有已保存的预设编号及其核心参数。\n\n"
            "### 4️⃣ 强烈推荐 ASMR 模板\n"
            "- **俊达萌私语**: `/vox1config s=38 spd=1.2 bgm=1 bgmv=0.25` \n"
            "- **四国美谈低语**: `/vox2config s=36 spd=1.1 vol=1.2` \n\n"
            "### 5️⃣ 模式说明\n"
            "- **拟音优化**: 自动检测中文，语速默认 1.0 且不强制加速，听感自然。\n"
            "- **原版模式**: 自动检测纯日语，对齐官方原版听感。"
        )