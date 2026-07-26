import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time
from fastapi import Depends
from sqlalchemy.orm import Session
import threading

from app.db.session import SessionLocal
from app.db.models import User
from app.services.glucose_monitor import glucose_monitor_service
from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

class GlucoseMonitorScheduler:
    """血糖监测定时任务调度器"""

    def __init__(self):
        self.running = False
        self.thread = None
        self.interval = 15 * 60  # 默认15分钟检查一次
        self.device_configs = {}  # 用户设备配置

    def start(self):
        """启动定时任务"""
        if self.running:
            logger.warning("血糖监测定时任务已在运行中")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("血糖监测定时任务已启动")

    def stop(self):
        """停止定时任务"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info("血糖监测定时任务已停止")

    def _run_scheduler(self):
        """运行定时任务循环"""
        logger.info("血糖监测定时任务循环开始")

        while self.running:
            try:
                # 创建一个新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # 执行定时任务
                loop.run_until_complete(self._check_glucose_data())

                # 关闭事件循环
                loop.close()

            except Exception as e:
                logger.error(f"血糖监测定时任务执行失败: {str(e)}")

            # 等待下一次执行
            time.sleep(self.interval)

        logger.info("血糖监测定时任务循环结束")

    async def _check_glucose_data(self):
        """检查所有用户的血糖数据"""
        logger.info(f"开始检查用户血糖数据: {datetime.now()}")

        # 创建数据库会话
        db = SessionLocal()
        try:
            # 获取所有活跃用户
            users = db.query(User).filter(User.is_active == True).all()
            logger.info(f"找到{len(users)}个活跃用户")

            for user in users:
                # 检查用户是否有设备配置
                user_config = self.device_configs.get(user.id)
                if not user_config:
                    continue

                try:
                    # 获取设备数据
                    device_type = user_config.get("device_type")
                    params = user_config.get("params", {})

                    if not device_type:
                        continue

                    logger.info(f"从{device_type}获取用户{user.id}的血糖数据")
                    data = await glucose_monitor_service.get_device_data(
                        device_type=device_type,
                        user_id=user.id,
                        params=params
                    )

                    if not data:
                        logger.warning(f"用户{user.id}没有新的血糖数据")
                        continue

                    # 保存到数据库
                    saved_records = await glucose_monitor_service.save_glucose_data(
                        db=db,
                        user_id=user.id,
                        glucose_data=data
                    )

                    logger.info(f"为用户{user.id}保存了{len(saved_records)}条血糖记录")

                    # 分析数据
                    analysis_result = await glucose_monitor_service.analyze_glucose_data(
                        db=db,
                        user_id=user.id,
                        hours=6  # 分析最近6小时的数据
                    )

                    # 如果有预警，生成预警消息
                    if analysis_result.get("status") == "ok" and analysis_result.get("has_alerts", False):
                        alert_message = await glucose_monitor_service.generate_alert_message(
                            analysis_result=analysis_result,
                            user_name=user.name or f"用户{user.id}"
                        )

                        logger.warning(f"用户{user.id}的血糖预警: {alert_message}")

                        # 这里可以添加发送预警通知的逻辑，如发送短信、推送通知等

                except Exception as e:
                    logger.error(f"处理用户{user.id}的血糖数据失败: {str(e)}")

        except Exception as e:
            logger.error(f"血糖监测定时任务执行失败: {str(e)}")
        finally:
            db.close()

    def register_device(self, user_id: str, device_type: str, params: Dict[str, Any] = None):
        """
        注册用户设备

        Args:
            user_id: 用户ID
            device_type: 设备类型
            params: 设备参数
        """
        self.device_configs[user_id] = {
            "device_type": device_type,
            "params": params or {},
            "last_check": datetime.now()
        }
        logger.info(f"用户{user_id}注册了{device_type}设备")

    def unregister_device(self, user_id: str):
        """
        取消注册用户设备

        Args:
            user_id: 用户ID
        """
        if user_id in self.device_configs:
            del self.device_configs[user_id]
            logger.info(f"用户{user_id}取消注册了设备")

# 创建调度器实例
glucose_scheduler = GlucoseMonitorScheduler()
