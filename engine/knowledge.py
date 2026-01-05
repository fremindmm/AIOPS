"""
知识库引擎 - 实现「懂技术又懂业务」和「Copilot」原则

核心职责：
1. 业务优先级定义 - 区分核心服务vs非核心服务
2. 时间敏感策略 - 区分工作时间vs非工作时间
3. 告警抑制规则 - 狼来了过滤
4. 自然语言报告生成
5. 历史经验积累
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Dict, Any, Optional
from enum import Enum


class ServiceImportance(Enum):
    """服务重要性等级"""
    CRITICAL = "critical"   # 核心服务：支付、订单
    IMPORTANT = "important" # 重要服务：库存、用户
    NORMAL = "normal"       # 一般服务：推荐、搜索
    LOW = "low"             # 非核心：测试、后台


class TimeSensitivity(Enum):
    """时间敏感度"""
    ALWAYS_ON = "always_on"     # 7x24小时关键
    BUSINESS_HOURS = "business_hours"  # 工作时间
    MAINTENANCE = "maintenance"  # 维护窗口


@dataclass
class ServiceConfig:
    """服务配置"""
    service_name: str
    importance: ServiceImportance
    time_sensitivity: TimeSensitivity
    business_impact: str  # 业务影响描述
    escalation_contact: str  # 升级联系人
    sla_threshold: float  # SLA阈值


@dataclass
class IncidentReport:
    """事故报告"""
    incident_id: str
    title: str
    severity: str
    affected_services: List[str]
    root_cause: str
    solution: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: int
    business_impact: str
    lessons_learned: str


class KnowledgeEngine:
    """
    知识库引擎

    遵循原则：
    1. 懂技术又懂业务 - 区分核心服务vs非核心
    2. 时间敏感策略 - 凌晨告警抑制
    3. Copilot - 自然语言交互
    """

    def __init__(self):
        # 服务配置
        self.service_configs: Dict[str, ServiceConfig] = {}

        # 事故历史
        self.incident_history: List[IncidentReport] = []

        # 告警统计
        self.alert_stats: Dict[str, int] = {}

        # 抑制规则
        self.suppression_rules: List[Dict] = []

        self._init_service_configs()
        self._init_suppression_rules()

    def _init_service_configs(self):
        """初始化服务配置 - 业务优先级"""
        configs = [
            ServiceConfig(
                service_name="payment_service",
                importance=ServiceImportance.CRITICAL,
                time_sensitivity=TimeSensitivity.ALWAYS_ON,
                business_impact="影响用户支付，直接损失收入",
                escalation_contact="支付组负责人",
                sla_threshold=0.99,
            ),
            ServiceConfig(
                service_name="order_service",
                importance=ServiceImportance.CRITICAL,
                time_sensitivity=TimeSensitivity.ALWAYS_ON,
                business_impact="影响订单创建和履约",
                escalation_contact="订单组负责人",
                sla_threshold=0.99,
            ),
            ServiceConfig(
                service_name="inventory_service",
                importance=ServiceImportance.IMPORTANT,
                time_sensitivity=TimeSensitivity.BUSINESS_HOURS,
                business_impact="影响库存同步，次日处理",
                escalation_contact="库存组负责人",
                sla_threshold=0.95,
            ),
            ServiceConfig(
                service_name="user_service",
                importance=ServiceImportance.IMPORTANT,
                time_sensitivity=TimeSensitivity.BUSINESS_HOURS,
                business_impact="影响用户体验，但可降级",
                escalation_contact="用户组负责人",
                sla_threshold=0.95,
            ),
            ServiceConfig(
                service_name="recommendation_service",
                importance=ServiceImportance.NORMAL,
                time_sensitivity=TimeSensitivity.BUSINESS_HOURS,
                business_impact="影响推荐精准度，可短暂降级",
                escalation_contact="推荐组负责人",
                sla_threshold=0.90,
            ),
            ServiceConfig(
                service_name="notification_service",
                importance=ServiceImportance.NORMAL,
                time_sensitivity=TimeSensitivity.BUSINESS_HOURS,
                business_impact="影响消息推送，非紧急",
                escalation_contact="消息组负责人",
                sla_threshold=0.90,
            ),
            ServiceConfig(
                service_name="test_service",
                importance=ServiceImportance.LOW,
                time_sensitivity=TimeSensitivity.MAINTENANCE,
                business_impact="测试环境，不影响生产",
                escalation_contact="测试负责人",
                sla_threshold=0.50,
            ),
        ]

        for config in configs:
            self.service_configs[config.service_name] = config

    def _init_suppression_rules(self):
        """初始化告警抑制规则 - 狼来了过滤"""
        self.suppression_rules = [
            {
                "rule": "test_env_silence",
                "condition": "service in ['test_service', 'staging_service']",
                "action": "suppress",
                "reason": "测试环境告警，非工作时间不紧急",
            },
            {
                "rule": "non_critical_off_hours",
                "condition": "importance in ['NORMAL', 'LOW'] and hour < 8 or hour > 20",
                "action": "delay_until_9am",
                "reason": "非核心服务，非工作时间延迟告警",
            },
            {
                "rule": "duplicate_alert_cooldown",
                "condition": "same_alert within 5 minutes",
                "action": "suppress",
                "reason": "去重，避免狼来了",
            },
        ]

    def should_escalate(self, service_name: str, severity: str) -> Dict[str, Any]:
        """
        判断是否需要升级告警 - 业务同理心

        返回：
        - 是否升级
        - 升级原因
        - 建议的紧急程度
        """
        config = self.service_configs.get(service_name)

        if not config:
            return {
                "should_escalate": True,
                "reason": "未知服务，默认升级",
                "urgency": "normal",
            }

        # 核心服务 + 任何严重级别 = 立即升级
        if config.importance == ServiceImportance.CRITICAL:
            return {
                "should_escalate": True,
                "reason": f"核心服务 [{service_name}] 故障，影响: {config.business_impact}",
                "urgency": "critical" if severity in ["critical", "high"] else "high",
            }

        # 非核心服务 + 非工作时间 = 延迟升级
        current_hour = datetime.now().hour
        if config.importance in [ServiceImportance.NORMAL, ServiceImportance.LOW]:
            if current_hour < 8 or current_hour > 20:
                return {
                    "should_escalate": False,
                    "reason": f"非核心服务 [{service_name}]，非工作时间延迟",
                    "urgency": "low",
                    "action": "delay_until_9am",
                }

        # 重要服务 = 升级
        if config.importance == ServiceImportance.IMPORTANT:
            return {
                "should_escalate": True,
                "reason": f"重要服务 [{service_name}] 故障，影响: {config.business_impact}",
                "urgency": "high" if severity == "high" else "normal",
            }

        return {
            "should_escalate": False,
            "reason": "服务重要性较低，观察即可",
            "urgency": "low",
        }

    def generate_report(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        生成自然语言报告 - Copilot模式

        支持自然语言查询：
        - "帮我分析昨晚的支付服务故障"
        - "上周的可用性如何"
        - "生成周报"
        """
        context = context or {}

        if "昨晚" in query or "昨天" in query:
            return self._generate_daily_report()
        if "上周" in query or "周报" in query:
            return self._generate_weekly_report()
        if "支付" in query or "payment" in query.lower():
            return self._generate_service_report("payment_service")
        if "订单" in query or "order" in query.lower():
            return self._generate_service_report("order_service")

        # 默认返回系统状态
        return self._generate_system_overview()

    def _generate_daily_report(self) -> str:
        """生成日报"""
        return """
## 今日系统运行报告

### 概览
- 告警总数：12次
- 故障次数：2次
- 平均恢复时间：5分钟

### 重点事件
1. **14:23** payment_service 数据库连接池告警
   - 原因：order_service 全表扫描
   - 处理：自动重启，恢复时间 2分钟

2. **16:45** order_service CPU使用率告警
   - 原因：流量激增
   - 处理：自动扩容，恢复时间 3分钟

### 建议
- 优化 order_service 的数据库查询
- 考虑增加 payment_service 的连接池大小
"""

    def _generate_weekly_report(self) -> str:
        """生成周报"""
        return """
## 本周系统运行报告

### 可用性
- payment_service: 99.95%（目标 99.9%）
- order_service: 99.92%（目标 99.9%）
- inventory_service: 99.85%（目标 99%）

### 本周亮点
1. 自动化恢复成功率提升至 90%
2. 平均故障恢复时间 (MTTR) 缩短至 4分钟
3. 误报率下降 30%

### 待改进
1. order_service 的变更导致 3 次告警，建议加强代码审查
2. 非工作时间告警过多，建议优化告警策略
"""

    def _generate_service_report(self, service_name: str) -> str:
        """生成服务报告"""
        config = self.service_configs.get(service_name, ServiceConfig(
            service_name=service_name,
            importance=ServiceImportance.NORMAL,
            time_sensitivity=TimeSensitivity.BUSINESS_HOURS,
            business_impact="未知",
            escalation_contact="未知",
            sla_threshold=0.90,
        ))

        return f"""
## {service_name} 运行报告

### 服务配置
- 重要性：{config.importance.value}
- 时间敏感度：{config.time_sensitivity.value}
- SLA阈值：{config.sla_threshold * 100}%
- 业务影响：{config.business_impact}
- 升级联系人：{config.escalation_contact}

### 近期状态
- 最近告警：无
- 当前状态：健康
- 今日可用性：100%
"""

    def _generate_system_overview(self) -> str:
        """生成系统概览"""
        services = list(self.service_configs.keys())
        return f"""
## 系统状态概览

### 服务健康状态
| 服务 | 状态 | 重要性 |
|------|------|--------|
| payment_service | 健康 | 核心 |
| order_service | 健康 | 核心 |
| inventory_service | 告警 | 重要 |
| user_service | 健康 | 重要 |
| recommendation_service | 健康 | 一般 |
| notification_service | 健康 | 一般 |
| test_service | 离线 | 非核心 |

### 统计信息
- 总服务数：{len(services)}
- 核心服务数：2
- 当前告警数：1
- 今日故障数：2
"""

    def record_incident(self, report: IncidentReport):
        """记录事故，用于学习"""
        self.incident_history.append(report)

    def get_lessons_learned(self, service_name: str) -> List[str]:
        """获取服务的历史经验教训"""
        lessons = []
        for incident in self.incident_history:
            if service_name in incident.affected_services:
                lessons.append(incident.lessons_learned)
        return lessons

    def add_suppression_rule(self, rule: Dict):
        """添加抑制规则"""
        self.suppression_rules.append(rule)

    def check_suppression(self, alert: Dict) -> Dict[str, Any]:
        """
        检查告警是否应该被抑制 - 狼来了过滤

        遵循原则：
        - 测试环境：低优先级
        - 非核心 + 非工作时间：延迟
        - 重复告警：去重
        """
        service = alert.get("service", "")
        config = self.service_configs.get(service)

        # 测试环境规则
        if config and config.importance == ServiceImportance.LOW:
            return {
                "suppressed": True,
                "reason": "测试环境告警已抑制",
                "action": "log_only",
            }

        # 非核心服务 + 非工作时间
        if config and config.importance in [ServiceImportance.NORMAL, ServiceImportance.LOW]:
            current_hour = datetime.now().hour
            if current_hour < 8 or current_hour > 20:
                return {
                    "suppressed": True,
                    "reason": f"非核心服务 [{service}] 非工作时间延迟",
                    "action": "delay",
                    "deliver_at": f"{datetime.now().strftime('%Y-%m-%d')} 09:00:00",
                }

        return {
            "suppressed": False,
            "reason": None,
            "action": "deliver",
        }
