# 求情插件 (Plea for Mercy)

> 作者：qa296  
> 仓库： [GitHub – astrbot_plugin_plea_mercy](https://github.com/qa296/astrbot_plugin_plea_mercy)

当 AstrBot 在群聊里被管理员禁言时，它会第一时间私聊那位管理员，或撒娇、或委屈、或俏皮地“求个情”，争取秒速解除禁言。

---

## 功能特性

| 特性 | 说明 |  
|---|---|  
| **自动感知** | 实时监听机器人被禁言事件，无需人工干预。 |  
| **精准定位** | 精确识别是哪一位管理员下的禁言指令。 |  
| **双重求情模式** | • **固定文案**：一键发送预设的可爱求情。<br>•  **LLM 智能**：动态调用大模型，参考最近聊天记录，生成“量身定制”的求情话术|  


---

## 更新日志

v1.0.0 首个版本发布  
> • 支持 aiocqhttp 全系列适配器（go-cqhttp、NapCat、Lagrange.Core 等）  
> • 支持固定与 LLM 双模式  
> • 支持变量注入群名、管理员昵称、禁言时长
> • 支持识别全体禁言

---

## 快速安装

```bash
# 1. 克隆仓库
git clone https://github.com/qa296/astrbot_plugin_plea_mercy.git

# 2. 放入插件目录
cp -r astrbot_plugin_plea_mercy  astrbot/data/plugins/

# 3. 重启 AstrBot
./restart.sh
```

---

## 可视化配置

打开 **AstrBot WebUI → 插件市场 → 已安装 → 求情插件 → 管理**，即可图形化调整：

| 配置项 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `plea_mode` | 选择 | `fixed` | 求情模式：fixed（固定文案） / llm（大模型智能文案） |
| `fixed_plea_message` | 文本 | 见下 | 固定文案，支持变量：<br>`{admin_name}` 管理员昵称<br>`{group_name}` 群名<br>`{duration_str}` 格式化禁言时长 |
| `llm_system_prompt` | 文本 | 见下 | LLM 系统提示词，设定 Bot 的“人设” |
| `llm_history_count` | 整数 | `10` | 调用 LLM 时参考的最近聊天条数 |

> 默认固定文案  
> 「呜呜呜，{admin_name} 大人，我做错了什么吗？我在群【{group_name}】被您禁言了 {duration_str}，可以原谅我吗？」  
> 默认LLM提示词  
> 你在一个群被群管理员禁言了。请根据下面提供的聊天记录，以一种非常委屈、可怜、且略带俏皮的语气，向禁言你的管理员写一段求情的话，请求他解除禁言。聊天记录中，'assistant'角色的发言是你自己的发言。

---

## 使用说明

1. 安装并启用插件。  
2. 按需选择“固定”或“LLM”模式并保存。  
3. 机器人在任意群被禁言时，插件自动私聊对应管理员求情，无需额外指令。  

---

觉得有趣？记得在点个 ⭐！  
任何 Bug 或建议，欢迎到 [GitHub Issues](https://github.com/qa296/astrbot_plugin_plea_mercy/issues) 留言讨论。
