"""
决策推荐引擎 - 实现「把排查变成做选择题」原则

核心职责：
1. 根据历史数据和知识库预判解决方案
2. 评估每个方案的风险和收益
3. 生成选择题式的决策建议
4. 支持自动执行或人工确认
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class DecisionOption:
    """决策选项"""
    label: str  # A/B/C...
    action: str  # 执行的动作
    description: str  # 描述
    success_rate: float  # 历史成功率
    risk_level: RiskLevel
    risk_description: str  # 风险说明
    estimated_downtime: str  # 预计停机时间
    auto_executable: bool  # 是否可自动执行


@dataclass
class DecisionRecommendation:
    """决策推荐"""
    alert_id: str
    problem_summary: str
    current_status: str
    options: List[DecisionOption]
    recommended_option: str  # 推荐的选项
    reasoning: str  # 推荐理由
    context: Dict[str, Any] = field(default_factory=dict)


class DecisionEngine:
    """
    决策推荐引擎

    遵循原则：
    - 把排查变成选择题
    - 评估风险和收益
    - 支持自动执行低风险操作
    """

    def __init__(self):
        # 决策知识库：问题类型 -> 解决方案
        self.solution_knowledge: Dict[str, List[Dict]] = {}

        # 操作历史：用于计算成功率
        self.operation_history: List[Dict] = []

        # 自动执行策略
        self.auto_execute_policy: Dict[str, bool] = {}

        self._init_solution_knowledge()

    def _init_solution_knowledge(self):
        """初始化解决方案知识库"""
        self.solution_knowledge = {
            "database_connection_pool_exhausted": [
                {
                    "action": "restart_service",
                    "label": "A. 立即重启服务",
                    "description": "重启 {service} 服务，释放连接池",
                    "success_rate": 0.92,
                    "risk_level": RiskLevel.MEDIUM,
                    "risk_description": "重启期间服务不可用，约30秒中断",
                    "estimated_downtime": "30秒",
                    "auto_executable": True,
                    "reasoning": "重启能快速释放连接池，历史成功率92%",
                },
                {
                    "action": "increase_pool_size",
                    "label": "B. 扩容连接池",
                    "description": "将连接池大小从 {current} 调整到 {target}",
                    "success_rate": 0.75,
                    "risk_level": RiskLevel.LOW,
                    "risk_description": "需要配置变更，可能需要重新部署",
                    "estimated_downtime": "无需停机",
                    "auto_executable": False,
                    "reasoning": "从根本上解决连接池不足问题，但需要配置变更",
                },
                {
                    "action": "rollback_change",
                    "label": "C. 回滚变更",
                    "description": "回滚 commit {commit_id}",
                    "success_rate": 0.85,
                    "risk_level": RiskLevel.HIGH,
                    "risk_description": "会丢失新功能，需要测试验证",
                    "estimated_downtime": "1-2分钟",
                    "auto_executable": False,
                    "reasoning": "如果确定是新变更导致，回滚是最根本的方案",
                },
            ],
            "high_cpu_usage": [
                {
                    "action": "restart_service",
                    "label": "A. 立即重启",
                    "description": "重启 {service} 释放CPU资源",
                    "success_rate": 0.88,
                    "risk_level": RiskLevel.MEDIUM,
                    "risk_description": "服务中断约30秒",
                    "estimated_downtime": "30秒",
                    "auto_executable": True,
                    "reasoning": "快速恢复服务，历史成功率88%",
                },
                {
                    "action": "scale_up",
                    "label": "B. 扩容实例",
                    "description": "增加 {service} 实例数量",
                    "success_rate": 0.95,
                    "risk_level": RiskLevel.LOW,
                    "risk_description": "可能增加成本",
                    "estimated_downtime": "无需停机",
                    "auto_executable": True,
                    "reasoning": "无停机风险，可快速扩容",
                },
            ],
            "oom": [
                {
                    "action": "restart_service",
                    "label": "A. 立即重启",
                    "description": "重启 {service} 释放内存",
                    "success_rate": 0.90,
                    "risk_level": RiskLevel.MEDIUM,
                    "risk_description": "服务中断约30秒",
                    "estimated_downtime": "30秒",
                    "auto_executable": True,
                    "reasoning": "快速恢复，90%成功率",
                },
                {
                    "action": "increase_memory",
                    "label": "B. 扩容内存",
                    "description": "将内存限制从 {current} 调整到 {target}",
                    "success_rate": 0.70,
                    "risk_level": RiskLevel.LOW,
                    "risk_description": "需要配置变更和重新部署",
                    "estimated_downtime": "1分钟",
                    "auto_executable": False,
                    "reasoning": "从根本上解决内存不足",
                },
            ],
            "disk_full": [
                {
                    "action": "cleanup_logs",
                    "label": "A. 清理日志",
                    "description": "清理7天前的日志文件",
                    "success_rate": 0.98,
                    "risk_level": RiskLevel.LOW,
                    "risk_description": "清理的日志已安全归档",
                    "estimated_downtime": "无需停机",
                    "auto_executable": True,
                    "reasoning": "低风险操作，可自动执行",
                },
                {
                    "action": "increase_disk",
                    "label": "B. 扩容磁盘",
                    "description": "增加磁盘空间",
                    "success_rate": 0.95,
                    "risk_level": RiskLevel.LOW,
                    "risk_description": "云盘扩容无风险",
                    "estimated_downtime": "无需停机",
                    "auto_executable": False,
                    "reasoning": "从根本上解决磁盘空间问题",
                },
            ],
        }

    def recommend(self, alert_type: str, context: Dict[str, Any] = None) -> DecisionRecommendation:
        """
        生成决策推荐 - 核心方法

        把排查变成选择题
        """
        context = context or {}

        # 获取问题的解决方案
        solutions = self.solution_knowledge.get(alert_type, [])

        if not solutions:
            # 默认方案
            return DecisionRecommendation(
                alert_id=context.get("alert_id", "unknown"),
                problem_summary=context.get("symptom", "未知问题"),
                current_status=context.get("status", "异常"),
                options=[
                    DecisionOption(
                        label="A. 人工处理",
                        action="manual",
                        description="请运维人员介入处理",
                        success_rate=0.5,
                        risk_level=RiskLevel.HIGH,
                        risk_description="需要人工排查",
                        estimated_downtime="未知",
                        auto_executable=False,
                    ),
                ],
                recommended_option="A",
                reasoning="没有找到自动化方案，建议人工处理",
            )

        # 生成选项
        options = []
        service = context.get("service", "服务")

        for sol in solutions:
            option = DecisionOption(
                label=sol["label"],
                action=sol["action"],
                description=sol["description"].format(**context),
                success_rate=sol["success_rate"],
                risk_level=sol["risk_level"],
                risk_description=sol["risk_description"],
                estimated_downtime=sol["estimated_downtime"],
                auto_executable=sol["auto_executable"],
            )
            options.append(option)

        # 选择推荐方案（优先高成功率、低风险、可自动执行）
        recommended = self._select_best_option(options)

        return DecisionRecommendation(
            alert_id=context.get("alert_id", "unknown"),
            problem_summary=context.get("symptom", alert_type),
            current_status=context.get("status", "异常"),
            options=options,
            recommended_option=recommended.label.split(".")[0],
            reasoning=recommended.description,
            context=context,
        )

    def _select_best_option(self, options: List[DecisionOption]) -> DecisionOption:
        """
        选择最佳方案 - 好品味：消除边界情况

        评分规则：
        - 成功率高 = +分
        - 风险低 = +分
        - 可自动执行 = +分
        """
        best = None
        best_score = -1

        for opt in options:
            # 成功率权重：0.5
            success_score = opt.success_rate * 0.5

            # 风险权重：0.3（低=1，中=0.5，高=0）
            risk_score = {
                RiskLevel.LOW: 1.0,
                RiskLevel.MEDIUM: 0.5,
                RiskLevel.HIGH: 0.0,
            }.get(opt.risk_level, 0) * 0.3

            # 自动执行权重：0.2
            auto_score = 0.2 if opt.auto_executable else 0

            total_score = success_score + risk_score + auto_score

            if total_score > best_score:
                best_score = total_score
                best = opt

        return best

    def execute(self, alert_id: str, action: str, auto_approved: bool = False) -> Dict[str, Any]:
        """
        执行决策

        遵循原则：
        - 自动执行低风险操作
        - 高风险操作需要人工确认
        """
        # 查找对应的解决方案
        solution = None
        for solutions in self.solution_knowledge.values():
            for sol in solutions:
                if sol["action"] == action:
                    solution = sol
                    break

        if not solution:
            return {
                "status": "failed",
                "message": f"未找到操作: {action}",
            }

        # 检查是否需要人工确认
        if not auto_approved and not solution["auto_executable"]:
            return {
                "status": "requires_approval",
                "message": f"此操作风险等级: {solution['risk_level']}，需要人工确认",
                "action": action,
                "risk_description": solution["risk_description"],
            }

        # 记录操作
        operation = {
            "alert_id": alert_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "auto_executed": auto_approved,
        }
        self.operation_history.append(operation)

        # 模拟执行
        return {
            "status": "success",
            "message": f"操作 {action} 执行成功",
            "operation": operation,
        }

    def get_success_rate(self, action: str) -> float:
        """获取操作成功率"""
        if not self.operation_history:
            return 0.0

        relevant = [op for op in self.operation_history if op["action"] == action]
        if not relevant:
            return 0.0

        return len(relevant) / len(self.operation_history)

    def can_auto_execute(self, action: str) -> bool:
        """检查操作是否可自动执行"""
        for solutions in self.solution_knowledge.values():
            for sol in solutions:
                if sol["action"] == action:
                    return sol["auto_executable"]
        return False
