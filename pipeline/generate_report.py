"""
GEO 周度运营报告生成器

读取 pipeline/data/dashboard_data.json（部署数据源），生成 Markdown 周报并写入仓库根目录 reports/。
由 .github/workflows/weekly-report.yml 每周自动执行并提交。

用法:
    cd pipeline
    python generate_report.py              # 默认读取 JSON
    python generate_report.py --source db  # 读取 SQLite（本地开发）
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("geo.report")

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_DIR = Path(__file__).resolve().parent
JSON_PATH = PIPELINE_DIR / "data" / "dashboard_data.json"
REPORT_DIR = REPO_ROOT / "reports"


def load_json_data() -> dict:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_db_data() -> dict:
    """本地开发模式：直接从 SQLite 聚合当日数据（用于没有 JSON 的场景）。"""
    sys.path.insert(0, str(PIPELINE_DIR))
    from database import init_db, get_db, DailyMetricsDAO, PlatformSnapshotDAO

    init_db()
    with get_db() as db:
        kpis = DailyMetricsDAO.get_aggregate_kpis(db)
        platforms = DailyMetricsDAO.get_latest_all(db)
        snapshots = PlatformSnapshotDAO.get_all(db)
    return {
        "kpis": kpis or {},
        "kpis_real": {},
        "kpi_changes": {},
        "kpi_changes_real": {},
        "trend": [],
        "trend_source": "none",
        "platforms": platforms or [],
        "snapshots": snapshots or [],
        "exported_at": datetime.utcnow().isoformat(),
        "data_quality": {"total_platforms": len(platforms)},
    }


def _fmt_kpi(label: str, kpis: dict, key: str, suffix: str = "") -> str:
    value = kpis.get(key)
    if value is None:
        return f"- {label}：无数据"
    return f"- {label}：**{value}**{suffix}"


def build_report(data: dict) -> str:
    """将看板 JSON 转成 Markdown 周报。"""
    kpis = data.get("kpis", {})
    kpis_real = data.get("kpis_real", {})
    dq = data.get("data_quality", {})
    record_date = kpis.get("record_date", "未知")
    exported_at = data.get("exported_at", "未知")

    lines = [
        "# GEO 周度运营报告",
        "",
        f"- 数据日期：{record_date}",
        f"- 导出时间：{exported_at}",
        f"- 数据质量：真实采集 **{dq.get('real_count', 0)}** 个平台（共 {dq.get('total_platforms', 0)}），其余为预留演示数据",
        "",
        "## 一、头部 KPI",
        "",
        "### 全部平台口径（真实 + 预留演示）",
        "",
    ]
    if kpis:
        lines += [
            _fmt_kpi("AI 可见性指数", kpis, "ai_visibility_index"),
            _fmt_kpi("AI 提到品牌的比例", kpis, "citation_rate", "%"),
            _fmt_kpi("大模型提到品牌次数", kpis, "mention_count"),
            _fmt_kpi("AI 对品牌的好感度", kpis, "sentiment_score"),
            _fmt_kpi("AI 推荐带来的访问量（估算）", kpis, "referral_traffic"),
            _fmt_kpi("官网被 AI 读懂的程度", kpis, "structural_health"),
        ]
    else:
        lines.append("- 无数据")
    lines += ["", "### 真实平台口径（仅真实采集）", ""]
    if kpis_real and kpis_real.get("ai_visibility_index") is not None:
        lines += [
            _fmt_kpi("AI 可见性指数", kpis_real, "ai_visibility_index"),
            _fmt_kpi("AI 提到品牌的比例", kpis_real, "citation_rate", "%"),
            _fmt_kpi("大模型提到品牌次数", kpis_real, "mention_count"),
            _fmt_kpi("AI 对品牌的好感度", kpis_real, "sentiment_score"),
            _fmt_kpi("AI 推荐带来的访问量（估算）", kpis_real, "referral_traffic"),
            _fmt_kpi("官网被 AI 读懂的程度", kpis_real, "structural_health"),
        ]
    else:
        lines.append("- 当前无真实采集平台，暂不展示真实口径")

    changes = data.get("kpi_changes", {})
    lines += ["", "## 二、KPI 环比变化（近 7 天 vs 前 7 天）", ""]
    if changes:
        lines.append(
            f"- 可见性变化：{changes.get('visibility_change', 0)}% ｜ 引用率变化：{changes.get('citation_change', 0)}% ｜ "
            f"提及数变化：{changes.get('mention_change', 0)} 次 ｜ 对比区间：{changes.get('comparison_period', '-')}"
        )
    else:
        lines.append("- 历史数据不足 14 天，暂无法计算环比")

    lines += ["", "## 三、平台明细", "", "| 平台 | 数据来源 | 可见性 | 引用率 | 提及数 | 情感 | 引荐流量 |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for p in data.get("platforms", []):
        lines.append(
            f"| {p.get('platform_name', p.get('platform', '-'))} | {p.get('data_source', '-')} | "
            f"{p.get('visibility_score', '-')} | {p.get('citation_rate', '-')}% | "
            f"{p.get('mention_count', '-')} | {p.get('avg_sentiment', '-')} | {p.get('referral_traffic', '-')} |"
        )

    trend = data.get("trend", [])
    lines += ["", "## 四、真实趋势", ""]
    if trend:
        lines.append(f"- 真实趋势点数：**{len(trend)}**（{trend[0].get('date')} ~ {trend[-1].get('date')}）")
        if len(trend) >= 2:
            first, last = trend[0], trend[-1]
            lines.append(
                f"- 可见性：{first.get('avg_visibility')} → {last.get('avg_visibility')}；"
                f"引用率：{first.get('avg_citation_rate')}% → {last.get('avg_citation_rate')}%"
            )
    else:
        lines.append("- 真实采集天数不足，暂无可视化趋势")

    lines += ["", "## 五、结论与建议", ""]
    real_platforms = dq.get("real_platforms", [])
    if real_platforms:
        lines.append(f"- 本周真实采集平台：{', '.join(real_platforms)}，请保持 API Key 有效并关注引用变化。")
    else:
        lines.append("- 本周无真实采集平台：请配置各平台 API Key（见 docs/API_KEYS_GUIDE.md），否则看板仅展示预留演示数据。")
    lines.append("- 下一步：补齐缺失平台真实数据 → 累积 14 天历史 → 让环比与趋势图具备业务意义。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="GEO 周度运营报告生成器")
    parser.add_argument("--source", choices=["json", "db"], default="json")
    args = parser.parse_args()

    data = load_json_data() if args.source == "json" else load_db_data()
    if not data.get("kpis"):
        logger.warning("无可用数据，跳过报告生成")
        return 1

    record_date = data.get("kpis", {}).get("record_date", datetime.utcnow().strftime("%Y-%m-%d"))
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORT_DIR / f"geo-weekly-report-{record_date}.md"
    out_path.write_text(build_report(data), encoding="utf-8")
    logger.info("报告已生成: %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
