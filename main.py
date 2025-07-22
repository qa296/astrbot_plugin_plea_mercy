import asyncio
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.star.filter.event_message_type import EventMessageType

# 尝试从 aiocqhttp 导入 CQHttp 类型，用于类型提示
try:
    from aiocqhttp import CQHttp
except ImportError:
    CQHttp = None

@register(
    "astrbot_plugin_plea_mercy",
    "qa296",
    "当被禁言时，向管理员私聊求情。",
    "1.0.0",
    "https://github.com/qa296/astrbot_plugin_plea_mercy", 
)
class PleaForMercyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        # 从配置中加载设置
        self.plea_mode = self.config.get("plea_mode", "fixed")
        self.fixed_plea_message = self.config.get(
            "fixed_plea_message", 
            "呜呜呜，{admin_name}大人，我做错了什么吗？我被您在群{group_name}里禁言了 {duration_str}，可以原谅我吗？"
        )
        self.llm_system_prompt = self.config.get(
            "llm_system_prompt",
            "你是一个被群管理员禁言了的机器人。请根据下面提供的聊天记录，以一种非常委屈、可怜、且略带俏皮的语气，向禁言你的管理员写一段求情的话，请求他解除禁言。不要超过100字，不要连续两次换行。聊天记录中，'assistant'角色的发言是你自己的发言。"
        )
        self.llm_history_count = self.config.get("llm_history_count", 20)
        logger.info("求情插件(astrbot_plugin_plea_mercy)已加载。")

    @staticmethod
    def _format_duration(duration_seconds: int) -> str:
        """将秒数格式化为易读的时间字符串"""
        if duration_seconds <= 0:
            return "很短的时间"
        
        days, rem = divmod(duration_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}秒")
        
        return "".join(parts)

    async def _get_operator_name(self, client: CQHttp, group_id: int, operator_id: int) -> str:
        """获取操作者（管理员）的群昵称"""
        try:
            info = await client.get_group_member_info(group_id=group_id, user_id=operator_id)
            return info.get("card") or info.get("nickname", str(operator_id))
        except Exception as e:
            logger.warning(f"获取管理员({operator_id})昵称失败: {e}")
            return f"管理员({operator_id})"

    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_ban_notice(self, event: AiocqhttpMessageEvent):
        """监听群禁言通知"""
        # 仅处理 aiocqhttp 平台的事件
        if event.get_platform_name() != "aiocqhttp":
            return

        raw_message = getattr(event.message_obj, "raw_message", None)

        # 确保是 notice 事件，且是 group_ban 类型
        if (
            not isinstance(raw_message, dict)
            or raw_message.get("post_type") != "notice"
            or raw_message.get("notice_type") != "group_ban"
        ):
            return

        # 确保是自己被禁言
        self_id = int(event.get_self_id())
        user_id = raw_message.get("user_id", 0)
        if user_id != self_id:
            return
        
        # 确保是禁言操作（duration > 0），而不是解禁
        duration = raw_message.get("duration", 0)
        if duration <= 0:
            return

        # 获取关键信息
        client: CQHttp = event.bot
        group_id = raw_message.get("group_id")
        operator_id = raw_message.get("operator_id")
        
        try:
            group_info = await client.get_group_info(group_id=group_id)
            group_name = group_info.get("group_name", str(group_id))
            admin_name = await self._get_operator_name(client, group_id, operator_id)
            duration_str = self._format_duration(duration)

            plea_message = ""
            if self.plea_mode == "llm":
                logger.info(f"检测到被禁言，使用 LLM 模式生成求情消息。")
                plea_message = await self._generate_llm_plea(client, group_id, self_id, admin_name, group_name, duration_str)
            else: # 默认使用 fixed 模式
                logger.info(f"检测到被禁言，使用固定模式生成求情消息。")
                plea_message = self.fixed_plea_message.format(
                    admin_name=admin_name,
                    group_name=group_name,
                    duration_str=duration_str
                )
            
            if plea_message:
                await client.send_private_msg(user_id=operator_id, message=plea_message)
                logger.info(f"已向管理员 {admin_name}({operator_id}) 发送求情私聊。")

            # 停止事件传播，因为这只是一个通知事件
            event.stop_event()

        except Exception as e:
            logger.error(f"处理禁言求情时发生错误: {e}", exc_info=True)

    async def _generate_llm_plea(self, client: CQHttp, group_id: int, self_id: int, admin_name: str, group_name: str, duration_str: str) -> str:
        """使用LLM生成求情文案"""
        provider = self.context.get_using_provider()
        if not provider:
            logger.warning("LLM模式求情失败：未找到当前启用的LLM Provider。")
            return ""

        try:
            # 1. 获取群聊历史消息
            history_data = await client.get_group_msg_history(group_id=group_id, message_seq=0)
            messages = history_data.get("messages", [])
            
            # 2. 截取并格式化为LLM上下文
            recent_messages = messages[-self.llm_history_count:]
            contexts = []
            for msg in recent_messages:
                sender_id = msg.get("sender", {}).get("user_id")
                content = msg.get("message", "")
                if not isinstance(content, str): # 简化处理，只用纯文本
                    content = "[非文本消息]"

                role = "assistant" if sender_id == self_id else "user"
                contexts.append({"role": role, "content": content})

            # 3. 构建Prompt
            prompt = (
                f"管理员“{admin_name}”你好，我刚刚在群“{group_name}”里被你禁言了{duration_str}。"
                "这是我被禁言前群里的一些聊天记录，我真的不知道我哪里说错了，求求你原谅我吧！"
            )

            # 4. 调用LLM
            llm_response = await provider.text_chat(
                prompt=prompt,
                contexts=contexts,
                system_prompt=self.llm_system_prompt
            )

            if llm_response and llm_response.completion_text:
                return llm_response.completion_text
            else:
                logger.warning("LLM未能生成有效的求情回复。")
                return ""

        except Exception as e:
            logger.error(f"LLM生成求情文案时出错: {e}", exc_info=True)
            return ""

    async def terminate(self):
        logger.info("求情插件(astrbot_plugin_plea_mercy)已卸载。")
