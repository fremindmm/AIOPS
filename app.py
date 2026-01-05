"""
AIOPS 演示系统 - 主服务入口

实现四大核心能力：
1. 因果分析 - 知道"谁干的"
2. 智能决策 - 把排查变成"选择题"
3. 业务感知 - 懂技术又懂业务
4. Copilot - 自然语言交互
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from engine.causality import CausalityEngine, Alert, Severity, ChangeEvent
from engine.decision import DecisionEngine
from engine.knowledge import KnowledgeEngine
from services.mock_data import MockMetricsService, MockGitService, MockAlertService

app = Flask(__name__)

# 初始化各引擎
causality_engine = CausalityEngine()
decision_engine = DecisionEngine()
knowledge_engine = KnowledgeEngine()

# 初始化Mock服务
metrics_service = MockMetricsService()
git_service = MockGitService()
alert_service = MockAlertService()

# 配置服务依赖关系
causality_engine.register_service("order_service", ["payment_service", "inventory_service"])
causality_engine.register_service("payment_service", ["database"])
causality_engine.register_service("inventory_service", ["database"])
causality_engine.register_service("user_service", ["database", "cache"])
causality_engine.register_service("recommendation_service", ["user_service", "cache"])
causality_engine.register_service("notification_service", ["user_service"])
causality_engine.register_service("database", [])
causality_engine.register_service("cache", [])


def setup_sample_data():
    """设置示例数据 - 预置一些变更记录"""
    now = datetime.now()

    sample_changes = [
        ChangeEvent(
            commit_id="a1b2c3d",
            author="张伟",
            service="order_service",
            file_path="OrderService.java",
            line_number=45,
            change_type="modify",
            description="优化订单查询逻辑，添加全表扫描以兼容老版本",
            timestamp=now - timedelta(hours=2),
        ),
        ChangeEvent(
            commit_id="e5f6g7h",
            author="李娜",
            service="payment_service",
            file_path="PaymentController.java",
            line_number=120,
            change_type="modify",
            description="修复支付超时处理逻辑，添加重试机制",
            timestamp=now - timedelta(hours=5),
        ),
        ChangeEvent(
            commit_id="i8j9k0l",
            author="王强",
            service="inventory_service",
            file_path="InventoryDao.java",
            line_number=88,
            change_type="add",
            description="新增库存预扣减功能，使用批量更新",
            timestamp=now - timedelta(days=1),
        ),
    ]

    for change in sample_changes:
        causality_engine.record_change(change)


# 初始化示例数据
setup_sample_data()


@app.route("/")
def index():
    """主页"""
    return render_template("dashboard.html")


@app.route("/api/metrics")
def get_metrics():
    """获取所有服务指标"""
    metrics = metrics_service.get_all_metrics()

    # 按服务分组
    service_metrics = {}
    for metric in metrics:
        if metric.service not in service_metrics:
            service_metrics[metric.service] = {}
        service_metrics[metric.service][metric.metric_name] = {
            "value": metric.value,
            "unit": metric.unit,
            "threshold": metric.threshold,
            "status": metric.status,
        }

    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "services": service_metrics,
    })


@app.route("/api/alerts")
def get_alerts():
    """获取活跃告警"""
    return jsonify({
        "alerts": alert_service.get_active_alerts(),
    })


@app.route("/api/analyze", methods=["POST"])
def analyze_alert():
    """
    分析告警 - 核心API

    实现「别告诉我有问题，告诉我谁干的」
    """
    data = request.json

    alert_type = data.get("alert_type", "high_cpu")
    service = data.get("service", "order_service")

    # 生成告警
    alert_event = alert_service.generate_alert(alert_type, service)

    # 构建Alert对象
    severity_map = {
        "critical": Severity.P0_CRITICAL,
        "high": Severity.P1_HIGH,
        "medium": Severity.P2_MEDIUM,
        "low": Severity.P3_LOW,
    }

    alert = Alert(
        alert_id=alert_event["alert_id"],
        service=service,
        metric=alert_event["metric"],
        value=alert_event["value"],
        threshold=alert_event["threshold"],
        severity=severity_map.get(alert_event["severity"], Severity.P2_MEDIUM),
        timestamp=datetime.now(),
        symptom=alert_event["symptom"],
    )

    # 因果分析
    root_cause = causality_engine.analyze(alert)

    # 决策推荐
    decision = decision_engine.recommend(
        alert_type=alert_event["metric"],
        context={
            "alert_id": alert_event["alert_id"],
            "service": service,
            "symptom": alert_event["symptom"],
            "status": alert_event["severity"],
        },
    )

    # 业务感知
    escalation = knowledge_engine.should_escalate(service, alert_event["severity"])

    result = {
        "alert": alert_event,
        "root_cause": None,
        "decision": {
            "problem_summary": decision.problem_summary,
            "options": [
                {
                    "label": opt.label,
                    "description": opt.description,
                    "success_rate": opt.success_rate,
                    "risk_level": opt.risk_level.value,
                    "risk_description": opt.risk_description,
                    "estimated_downtime": opt.estimated_downtime,
                    "auto_executable": opt.auto_executable,
                }
                for opt in decision.options
            ],
            "recommended_option": decision.recommended_option,
            "reasoning": decision.reasoning,
        },
        "escalation": escalation,
    }

    if root_cause:
        result["root_cause"] = {
            "commit_id": root_cause.commit_id,
            "author": root_cause.author,
            "file_path": root_cause.file_path,
            "line_number": root_cause.line_number,
            "description": root_cause.description,
            "confidence": root_cause.confidence,
            "solution": root_cause.solution,
            "related_services": root_cause.related_services,
        }

    return jsonify(result)


@app.route("/api/execute", methods=["POST"])
def execute_action():
    """
    执行决策操作

    实现「把排查变成做选择题」后的执行
    """
    data = request.json

    alert_id = data.get("alert_id")
    action = data.get("action")
    auto_approved = data.get("auto_approved", False)

    result = decision_engine.execute(alert_id, action, auto_approved)

    return jsonify(result)


@app.route("/api/copilot", methods=["POST"])
def copilot_chat():
    """
    Copilot 交互

    实现「是伙伴、是助手、是副驾」
    """
    data = request.json
    query = data.get("query", "")

    # 生成自然语言报告
    report = knowledge_engine.generate_report(query)

    return jsonify({
        "query": query,
        "report": report,
        "suggestions": [
            "帮我分析昨晚的支付服务故障",
            "上周的可用性如何",
            "生成周报",
            "order_service 的状态",
        ],
    })


@app.route("/api/changes")
def get_changes():
    """获取代码变更历史"""
    service = request.args.get("service")
    hours = int(request.args.get("hours", 24))

    changes = git_service.get_recent_changes(service, hours)

    return jsonify({
        "changes": changes,
    })


@app.route("/api/services")
def get_services():
    """获取所有服务列表及配置"""
    services = []
    for name, config in knowledge_engine.service_configs.items():
        services.append({
            "name": name,
            "importance": config.importance.value,
            "time_sensitivity": config.time_sensitivity.value,
            "business_impact": config.business_impact,
            "escalation_contact": config.escalation_contact,
            "sla_threshold": config.sla_threshold,
        })

    return jsonify({
        "services": services,
    })


@app.route("/api/demo/scenario", methods=["POST"])
def run_demo_scenario():
    """
    运行预设演示场景
    """
    scenario = request.json.get("scenario", "db_oom")

    if scenario == "db_oom":
        # 场景：数据库连接池耗尽
        alert_type = "db_pool_exhausted"
        service = "order_service"
        description = "模拟场景：order_service 数据库连接池耗尽，原因是张伟在 OrderService.java:45 添加了全表扫描"
    elif scenario == "high_cpu":
        alert_type = "high_cpu"
        service = "payment_service"
        description = "模拟场景：payment_service CPU使用率飙升，疑似流量激增"
    elif scenario == "oom":
        alert_type = "oom"
        service = "recommendation_service"
        description = "模拟场景：recommendation_service OOM，可能是内存泄漏"
    else:
        return jsonify({"error": "未知场景"}), 400

    return jsonify({
        "scenario": scenario,
        "description": description,
        "alert_type": alert_type,
        "service": service,
    })


if __name__ == "__main__":
    print("=" * 60)
    print("AIOPS 演示系统启动中...")
    print("访问 http://localhost:5001 查看仪表盘")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5001, debug=True)
