"""
因果分析引擎 - 实现「别告诉我有问题，告诉我谁干的」原则

核心职责：
1. 构建服务间的因果依赖图
2. 将告警追溯到根本原因（代码变更、责任人）
3. 支持根因定位和影响范围分析
"""

import networkx as nx
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class Severity(Enum):
    """告警严重程度"""
    P0_CRITICAL = "critical"  # 立即处理
    P1_HIGH = "high"          # 紧急
    P2_MEDIUM = "medium"      # 一般
    P3_LOW = "low"            # 提示


@dataclass
class ChangeEvent:
    """变更事件 - 记录谁在什么时候改了什么"""
    commit_id: str
    author: str
    service: str
    file_path: str
    line_number: int
    change_type: str  # add/modify/delete
    description: str
    timestamp: datetime
    risk_score: float = 0.0  # 风险评分


@dataclass
class Alert:
    """告警事件"""
    alert_id: str
    service: str
    metric: str
    value: float
    threshold: float
    severity: Severity
    timestamp: datetime
    symptom: str  # 症状描述


@dataclass
class RootCause:
    """根因分析结果"""
    alert: Alert
    commit_id: str
    author: str
    file_path: str
    line_number: int
    description: str
    confidence: float  # 置信度 0-1
    solution: str
    related_services: List[str] = field(default_factory=list)


class CausalityEngine:
    """
    因果分析引擎

    使用有向图构建服务间的因果关系，支持：
    - 从告警追溯到代码变更
    - 计算影响传播路径
    - 定位最可能的根因
    """

    def __init__(self):
        # 因果图：节点是服务，边表示调用/依赖关系
        self.dependency_graph = nx.DiGraph()

        # 代码变更记录
        self.change_history: List[ChangeEvent] = []

        # 告警历史
        self.alert_history: List[Alert] = []

        # 知识图谱：症状 -> 可能的原因
        self.symptom_causes: Dict[str, Dict[str, float]] = {}

        self._init_knowledge_base()

    def _init_knowledge_base(self):
        """初始化症状-原因知识库 - 好品味：消除边界情况"""
        self.symptom_causes = {
            "database_connection_pool_exhausted": {
                "full_table_scan": 0.85,
                "connection_leak": 0.70,
                "traffic_spike": 0.50,
                "slow_queries": 0.60,
            },
            "high_cpu_usage": {
                "infinite_loop": 0.90,
                "memory_leak": 0.40,
                "traffic_spike": 0.35,
                "algorithm_inefficiency": 0.55,
            },
            "oom": {
                "memory_leak": 0.80,
                "large_data_load": 0.45,
                "connection_leak": 0.50,
            },
            "timeout": {
                "deadlock": 0.60,
                "slow_database": 0.40,
                "network_issue": 0.35,
                "resource_exhaustion": 0.55,
            },
        }

    def register_service(self, service_name: str, depends_on: List[str] = None):
        """
        注册服务及其依赖关系

        例：order_service 依赖 payment_service 和 inventory_service
        """
        if not self.dependency_graph.has_node(service_name):
            self.dependency_graph.add_node(service_name)

        if depends_on:
            for dep in depends_on:
                self.dependency_graph.add_node(dep)
                self.dependency_graph.add_edge(service_name, dep)  # service -> dependency

    def record_change(self, change: ChangeEvent):
        """记录代码变更"""
        self.change_history.append(change)

        # 风险评分计算 - 实用主义：根据变更类型和影响范围评分
        risk_weights = {
            "add": 0.3,
            "modify": 0.6,
            "delete": 0.8,
        }
        change.risk_score = risk_weights.get(change.change_type, 0.5)

    def analyze(self, alert: Alert) -> Optional[RootCause]:
        """
        核心分析：告警 -> 根因

        遵循原则：「别告诉我有问题，告诉我谁干的」

        算法步骤：
        1. 根据症状匹配可能的原因
        2. 在变更历史中查找相关变更
        3. 验证因果链
        4. 返回根因（包含commit_id、责任人、代码位置）
        """
        # 1. 根据症状获取可能原因
        possible_causes = self.symptom_causes.get(alert.metric, {})

        if not possible_causes:
            return None

        # 2. 在变更历史中查找相关变更（时间窗口：告警前4小时内）
        time_window = timedelta(hours=4)
        recent_changes = [
            c for c in self.change_history
            if alert.timestamp - c.timestamp <= time_window
            and c.service == alert.service
        ]

        if not recent_changes:
            # 没有变更？可能是流量问题
            return RootCause(
                alert=alert,
                commit_id="N/A",
                author="流量激增",
                file_path="N/A",
                line_number=0,
                description=f"检测到{alert.symptom}，但无近期变更记录，可能是流量激增导致",
                confidence=0.6,
                solution="考虑扩容或限流",
                related_services=self._get_affected_services(alert.service),
            )

        # 3. 查找最可能的根因（结合风险评分和原因匹配度）
        best_cause = None
        best_score = 0

        for change in recent_changes:
            for cause, match_score in possible_causes.items():
                # 检查变更描述是否包含原因关键词
                if self._match_cause(change.description, cause):
                    # 综合评分 = 原因匹配度 * 变更风险
                    score = match_score * change.risk_score
                    if score > best_score:
                        best_score = score
                        best_cause = change

        if best_cause:
            return RootCause(
                alert=alert,
                commit_id=best_cause.commit_id,
                author=best_cause.author,
                file_path=best_cause.file_path,
                line_number=best_cause.line_number,
                description=best_cause.description,
                confidence=min(best_score, 1.0),
                solution=self._get_solution(best_cause.description),
                related_services=self._get_affected_services(alert.service),
            )

        # 兜底：返回最近的变更作为可能原因
        latest_change = max(recent_changes, key=lambda c: c.timestamp)
        return RootCause(
            alert=alert,
            commit_id=latest_change.commit_id,
            author=latest_change.author,
            file_path=latest_change.file_path,
            line_number=latest_change.line_number,
            description=f"未找到明确原因，但发现以下变更：{latest_change.description}",
            confidence=0.4,
            solution="建议回滚此变更或进一步排查",
            related_services=self._get_affected_services(alert.service),
        )

    def _match_cause(self, description: str, cause: str) -> bool:
        """检查变更描述是否与原因匹配"""
        cause_keywords = {
            "full_table_scan": ["全表扫描", "select *", "without index"],
            "connection_leak": ["连接泄漏", "connection leak", "未关闭连接"],
            "memory_leak": ["内存泄漏", "memory leak", "未释放"],
            "infinite_loop": ["死循环", "infinite", "无限循环"],
            "slow_queries": ["慢查询", "slow query"],
        }
        keywords = cause_keywords.get(cause, [cause])
        return any(kw.lower() in description.lower() for kw in keywords)

    def _get_solution(self, description: str) -> str:
        """根据变更描述给出解决方案"""
        if "全表扫描" in description or "select *" in description.lower():
            return "建议：添加索引或优化SQL查询条件"
        if "连接泄漏" in description or "connection leak" in description.lower():
            return "建议：检查连接释放逻辑，使用try-with-resources"
        if "内存泄漏" in description or "memory leak" in description.lower():
            return "建议：检查对象引用，及时释放资源"
        return "建议：评估变更影响，考虑回滚"

    def _get_affected_services(self, service: str) -> List[str]:
        """获取受影响的服务列表 - 遵循 Never break userspace"""
        affected = []
        try:
            # 获取所有依赖该服务的上游服务
            for node in self.dependency_graph.nodes():
                if self.dependency_graph.has_path(node, service):
                    affected.append(node)
        except Exception:
            pass
        return affected if affected else [service]

    def get_causal_chain(self, service: str) -> List[str]:
        """获取服务的完整因果链"""
        chain = [service]
        try:
            for dep in nx.dfs_preorder_nodes(self.dependency_graph, service):
                if dep != service:
                    chain.append(dep)
        except Exception:
            pass
        return chain

    def get_change_history(self, service: str = None, hours: int = 24) -> List[ChangeEvent]:
        """获取变更历史"""
        time_window = timedelta(hours=hours)
        now = datetime.now()
        changes = [
            c for c in self.change_history
            if now - c.timestamp <= time_window
        ]
        if service:
            changes = [c for c in changes if c.service == service]
        return sorted(changes, key=lambda c: c.timestamp, reverse=True)
