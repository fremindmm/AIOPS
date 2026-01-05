"""
Mock服务 - 模拟被监控的服务和指标数据

用于Demo演示，提供逼真的模拟数据
"""

import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class MockMetric:
    """模拟指标"""
    service: str
    metric_name: str
    value: float
    unit: str
    threshold: float
    status: str  # ok/warning/critical


class MockMetricsService:
    """
    模拟指标服务

    生成模拟的监控指标数据
    """

    def __init__(self):
        # 服务配置
        self.services = {
            "payment_service": {
                "port": 8080,
                "base_cpu": 30,
                "base_memory": 40,
                "base_connections": 50,
            },
            "order_service": {
                "port": 8081,
                "base_cpu": 40,
                "base_memory": 45,
                "base_connections": 60,
            },
            "inventory_service": {
                "port": 8082,
                "base_cpu": 20,
                "base_memory": 30,
                "base_connections": 30,
            },
            "user_service": {
                "port": 8083,
                "base_cpu": 25,
                "base_memory": 35,
                "base_connections": 40,
            },
            "recommendation_service": {
                "port": 8084,
                "base_cpu": 50,
                "base_memory": 55,
                "base_connections": 20,
            },
        }

        # 当前异常状态
        self.active_anomalies: Dict[str, Dict] = {}

    def get_all_metrics(self) -> List[MockMetric]:
        """获取所有服务的当前指标"""
        metrics = []

        for service, config in self.services.items():
            # CPU使用率
            cpu = self._generate_value(config["base_cpu"], 20)
            metrics.append(MockMetric(
                service=service,
                metric_name="cpu_usage",
                value=cpu,
                unit="%",
                threshold=80,
                status="critical" if cpu > 90 else ("warning" if cpu > 80 else "ok"),
            ))

            # 内存使用率
            memory = self._generate_value(config["base_memory"], 20)
            metrics.append(MockMetric(
                service=service,
                metric_name="memory_usage",
                value=memory,
                unit="%",
                threshold=85,
                status="critical" if memory > 95 else ("warning" if memory > 85 else "ok"),
            ))

            # 数据库连接
            conn = self._generate_value(config["base_connections"], 30)
            metrics.append(MockMetric(
                service=service,
                metric_name="db_connections",
                value=conn,
                unit="个",
                threshold=100,
                status="critical" if conn > 100 else ("warning" if conn > 80 else "ok"),
            ))

        return metrics

    def get_service_metrics(self, service_name: str) -> List[MockMetric]:
        """获取单个服务的指标"""
        all_metrics = self.get_all_metrics()
        return [m for m in all_metrics if m.service == service_name]

    def _generate_value(self, base: float, variance: float) -> float:
        """生成带波动的值"""
        return round(base + random.uniform(-variance, variance), 1)

    def trigger_anomaly(self, service: str, anomaly_type: str):
        """触发异常 - 用于演示"""
        self.active_anomalies[service] = {
            "type": anomaly_type,
            "start_time": datetime.now(),
        }

        if anomaly_type == "db_pool_exhausted":
            # 数据库连接池耗尽
            pass  # 会在get_all_metrics中体现

    def clear_anomaly(self, service: str):
        """清除异常"""
        if service in self.active_anomalies:
            del self.active_anomalies[service]


class MockGitService:
    """
    模拟Git服务

    提供模拟的代码变更记录
    """

    def __init__(self):
        self.changes = []

        # 预置一些"真实的"变更记录
        self._init_sample_changes()

    def _init_sample_changes(self):
        """初始化示例变更"""
        now = datetime.now()

        changes = [
            {
                "commit_id": "a1b2c3d",
                "author": "张伟",
                "service": "order_service",
                "file_path": "OrderService.java",
                "line_number": 45,
                "change_type": "modify",
                "description": "优化订单查询逻辑，添加全表扫描以兼容老版本",
                "timestamp": now - timedelta(hours=2),
            },
            {
                "commit_id": "e5f6g7h",
                "author": "李娜",
                "service": "payment_service",
                "file_path": "PaymentController.java",
                "line_number": 120,
                "change_type": "modify",
                "description": "修复支付超时处理逻辑",
                "timestamp": now - timedelta(hours=5),
            },
            {
                "commit_id": "i8j9k0l",
                "author": "王强",
                "service": "inventory_service",
                "file_path": "InventoryDao.java",
                "line_number": 88,
                "change_type": "add",
                "description": "新增库存预扣减功能",
                "timestamp": now - timedelta(days=1),
            },
            {
                "commit_id": "m1n2o3p",
                "author": "赵敏",
                "service": "user_service",
                "file_path": "UserCache.java",
                "line_number": 200,
                "change_type": "modify",
                "description": "优化缓存过期策略",
                "timestamp": now - timedelta(hours=12),
            },
        ]

        for change in changes:
            from engine.causality import ChangeEvent
            self.changes.append(ChangeEvent(**change))

    def get_recent_changes(self, service: str = None, hours: int = 24) -> List[Dict]:
        """获取最近的变更"""
        now = datetime.now()
        filtered = [
            c for c in self.changes
            if now - c.timestamp <= timedelta(hours=hours)
        ]
        if service:
            filtered = [c for c in filtered if c.service == service]

        return [
            {
                "commit_id": c.commit_id,
                "author": c.author,
                "service": c.service,
                "file_path": c.file_path,
                "line_number": c.line_number,
                "change_type": c.change_type,
                "description": c.description,
                "timestamp": c.timestamp.isoformat(),
            }
            for c in filtered
        ]


class MockAlertService:
    """
    模拟告警服务

    生成模拟告警事件
    """

    def __init__(self):
        self.alerts = []
        self.alert_id_counter = 1000

    def generate_alert(self, alert_type: str, service: str) -> Dict:
        """生成告警"""
        self.alert_id_counter += 1

        alert_templates = {
            "db_pool_exhausted": {
                "metric": "database_connection_pool_exhausted",
                "symptom": "数据库连接池已耗尽",
                "value": 100,
                "threshold": 100,
                "severity": "critical",
                "message": "数据库连接池已耗尽，当前连接数：100，最大容量：100",
            },
            "high_cpu": {
                "metric": "high_cpu_usage",
                "symptom": "CPU使用率过高",
                "value": 95,
                "threshold": 80,
                "severity": "high",
                "message": "CPU使用率达到95%，超过80%阈值",
            },
            "oom": {
                "metric": "oom",
                "symptom": "内存溢出",
                "value": 98,
                "threshold": 90,
                "severity": "critical",
                "message": "内存使用率达到98%，即将触发OOM",
            },
            "timeout": {
                "metric": "timeout",
                "symptom": "服务响应超时",
                "value": 5000,
                "threshold": 2000,
                "severity": "medium",
                "message": "响应时间达到5000ms，超过2000ms阈值",
            },
        }

        template = alert_templates.get(alert_type, alert_templates["high_cpu"])

        alert = {
            "alert_id": f"ALT-{self.alert_id_counter}",
            "service": service,
            "metric": template["metric"],
            "symptom": template["symptom"],
            "value": template["value"],
            "threshold": template["threshold"],
            "severity": template["severity"],
            "message": template["message"],
            "timestamp": datetime.now().isoformat(),
        }

        self.alerts.append(alert)
        return alert

    def get_active_alerts(self) -> List[Dict]:
        """获取活跃告警"""
        return self.alerts[-10:]  # 最近10条

    def clear_alerts(self):
        """清除告警历史"""
        self.alerts = []
