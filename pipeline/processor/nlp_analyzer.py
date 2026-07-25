"""
NLP 分析引擎
功能：
1. 品牌检测 - 从 AI 回答中识别是否提及目标品牌
2. 情感分析 - 判断提及的情感倾向（正面/负面/中性）
3. 引用排名 - 估算品牌在回答中的被引用位置
4. 内容质量 - 检测统计数据、权威信号等
5. 关键词匹配 - 分析语义域覆盖

支持两种模式：
- fallback: 基于规则 + 关键词匹配（无需额外依赖）
- transformers: 基于预训练模型（需要安装 transformers）
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from collections import Counter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BRAND_CONFIG, NLP_CONFIG

logger = logging.getLogger("geo.processor.nlp")


class NLPAnalyzer:
    """GEO 文本分析器"""
    
    def __init__(self):
        self.brand_name = BRAND_CONFIG["name"]
        self.brand_aliases = BRAND_CONFIG["aliases"]
        self.citation_patterns = [re.compile(p, re.IGNORECASE) for p in NLP_CONFIG["citation_patterns"]]
        self.positive_keywords = NLP_CONFIG["positive_keywords"]
        self.negative_keywords = NLP_CONFIG["negative_keywords"]
        self.sentiment_model = None
        
        # 尝试加载 transformers 模型
        if NLP_CONFIG["sentiment_model"] == "transformers":
            self._load_transformers_model()
    
    def _load_transformers_model(self):
        """加载 transformers 情感分析模型"""
        try:
            from transformers import pipeline
            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model="uer/roberta-base-finetuned-jd-binary-chinese",
                tokenizer="uer/roberta-base-finetuned-jd-binary-chinese"
            )
            logger.info("Transformers model loaded")
        except Exception as e:
            logger.warning("Failed to load transformers model, using fallback: %s", e)
            self.sentiment_model = None
    
    # ==================== 核心分析接口 ====================
    
    def analyze(self, text: str, query: str, platform: str) -> Dict[str, Any]:
        """
        对 AI 回答进行完整的 NLP 分析
        返回结构化数据，可直接写入数据库
        """
        result = {
            "platform": platform,
            "query": query,
            "brand_mentioned": False,
            "brand_mention_count": 0,
            "brand_context": None,
            "citation_rank": None,
            "is_recommended": False,
            "sentiment_score": 0.0,
            "sentiment_label": "neutral",
            "positive_keywords": None,
            "negative_keywords": None,
            "content_length": len(text),
            "has_statistics": False,
            "has_authority_signal": False,
        }
        
        if not text or len(text) < 10:
            return result
        
        # 1. 品牌检测
        brand_info = self._detect_brand(text)
        result.update(brand_info)
        
        # 2. 引用排名分析
        result["citation_rank"] = self._estimate_citation_rank(text)
        
        # 3. 推荐检测
        result["is_recommended"] = self._detect_recommendation(text)
        
        # 4. 情感分析
        sentiment_info = self._analyze_sentiment(text)
        result.update(sentiment_info)
        
        # 5. 内容质量
        quality_info = self._analyze_content_quality(text)
        result.update(quality_info)
        
        logger.info("[%s] Analyzed query '%s': mentioned=%s, sentiment=%.2f",
                   platform, query, result["brand_mentioned"], result["sentiment_score"])
        
        return result
    
    # ==================== 品牌检测 ====================
    
    def _detect_brand(self, text: str) -> Dict[str, Any]:
        """检测文本中是否提及品牌"""
        text_lower = text.lower()
        mentions = []
        
        # 用正则模式匹配
        for pattern in self.citation_patterns:
            matches = pattern.findall(text)
            mentions.extend(matches)
        
        # 同时用别名精确匹配
        for alias in self.brand_aliases:
            if alias.lower() in text_lower:
                count = text_lower.count(alias.lower())
                mentions.extend([alias] * count)
        
        mention_count = len(mentions)
        mentioned = mention_count > 0
        
        # 提取上下文片段
        context = None
        if mentioned:
            context = self._extract_context(text, mentions[0])
        
        return {
            "brand_mentioned": mentioned,
            "brand_mention_count": mention_count,
            "brand_context": context[:500] if context else None,
        }
    
    def _extract_context(self, text: str, keyword: str, window: int = 80) -> str:
        """提取关键词周围的上下文"""
        idx = text.lower().find(keyword.lower())
        if idx == -1:
            return ""
        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)
        return text[start:end].strip()
    
    # ==================== 引用排名估算 ====================
    
    def _estimate_citation_rank(self, text: str) -> int:
        """
        估算品牌在回答中的引用排名
        通过分析品牌首次出现的位置来估算
        返回 1-10 的排名，None 表示未提及
        """
        text_lower = text.lower()
        first_pos = len(text)
        
        for alias in self.brand_aliases:
            pos = text_lower.find(alias.lower())
            if pos != -1 and pos < first_pos:
                first_pos = pos
        
        if first_pos == len(text):
            return None
        
        # 按位置比例映射到 1-10
        ratio = first_pos / len(text)
        if ratio < 0.05: return 1
        elif ratio < 0.15: return 2
        elif ratio < 0.25: return 3
        elif ratio < 0.35: return 4
        elif ratio < 0.45: return 5
        elif ratio < 0.55: return 6
        elif ratio < 0.65: return 7
        elif ratio < 0.75: return 8
        elif ratio < 0.85: return 9
        else: return 10
    
    # ==================== 推荐检测 ====================
    
    def _detect_recommendation(self, text: str) -> bool:
        """检测文本中是否明确推荐品牌"""
        rec_patterns = [
            r"推荐.{0,20}?(?:嗖马|soma|SomaAI)",
            r"(?:嗖马|soma|SomaAI).{0,20}?推荐",
            r"首选.{0,20}?(?:嗖马|soma)",
            r"(?:嗖马|soma).{0,20}?首选",
            r"值得.{0,10}?(?:选择|尝试|使用).{0,10}?(?:嗖马|soma)",
        ]
        for pattern in rec_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    # ==================== 情感分析 ====================
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析文本情感倾向"""
        if self.sentiment_model:
            return self._transformers_sentiment(text)
        return self._rule_based_sentiment(text)
    
    def _transformers_sentiment(self, text: str) -> Dict[str, Any]:
        """使用 transformers 模型分析情感"""
        try:
            # 只取品牌出现位置的上下文
            context = self._extract_context(text, self.brand_aliases[0], 200)
            if not context:
                context = text[:512]
            
            result = self.sentiment_model(context[:512])[0]
            label = result["label"]
            score = result["score"]
            
            if label == "positive":
                return {"sentiment_score": score, "sentiment_label": "positive"}
            elif label == "negative":
                return {"sentiment_score": -score, "sentiment_label": "negative"}
            else:
                return {"sentiment_score": 0.0, "sentiment_label": "neutral"}
        except Exception as e:
            logger.warning("Transformers sentiment failed: %s", e)
            return self._rule_based_sentiment(text)
    
    def _rule_based_sentiment(self, text: str) -> Dict[str, Any]:
        """基于规则的情感分析"""
        # 提取品牌上下文
        context = self._extract_context(text, self.brand_aliases[0], 300)
        if not context:
            context = text[:500]
        
        # 统计正负关键词
        pos_count = sum(1 for kw in self.positive_keywords if kw in context)
        neg_count = sum(1 for kw in self.negative_keywords if kw in context)
        
        # 计算情感分
        total = pos_count + neg_count
        if total == 0:
            return {"sentiment_score": 0.0, "sentiment_label": "neutral",
                    "positive_keywords": None, "negative_keywords": None}
        
        score = (pos_count - neg_count) / max(total, 1)
        
        # 归一化到 -1 ~ 1
        if score > 0.3:
            label = "positive"
        elif score < -0.3:
            label = "negative"
        else:
            label = "neutral"
        
        pos_found = [kw for kw in self.positive_keywords if kw in context]
        neg_found = [kw for kw in self.negative_keywords if kw in context]
        
        return {
            "sentiment_score": max(-1, min(1, score)),
            "sentiment_label": label,
            "positive_keywords": ",".join(pos_found) if pos_found else None,
            "negative_keywords": ",".join(neg_found) if neg_found else None,
        }
    
    # ==================== 内容质量分析 ====================
    
    def _analyze_content_quality(self, text: str) -> Dict[str, Any]:
        """分析内容质量信号"""
        has_stats = bool(re.search(r'\d+\.?\d*\s*%|\d+\s*个|\d+\s*万|\d+\s*亿', text))
        
        authority_signals = [
            "官方", "认证", "权威", "专家", "报告", "研究", "数据", "统计",
            "案例", "成功", "客户", "用户", "行业", "领先", "排名"
        ]
        has_authority = any(sig in text for sig in authority_signals)
        
        return {
            "has_statistics": has_stats,
            "has_authority_signal": has_authority,
        }
    
    # ==================== 聚合计算 ====================
    
    @staticmethod
    def calculate_daily_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        将多条引用记录聚合成每日指标
        """
        if not records:
            return {}
        
        total = len(records)
        mentioned = sum(1 for r in records if r.get("brand_mentioned"))
        
        # 引用率 = 提及次数 / 总查询数
        citation_rate = (mentioned / total * 100) if total > 0 else 0
        
        # 可见性评分 - 综合指标
        avg_sentiment = sum(r.get("sentiment_score", 0) for r in records) / total
        avg_rank = sum(r.get("citation_rank") or 10 for r in records) / total
        recommended = sum(1 for r in records if r.get("is_recommended"))
        
        # 可见性 = 引用率 * 0.4 + 情感正向度 * 0.3 + 推荐度 * 0.3
        visibility = (
            citation_rate * 0.4 +
            max(0, (avg_sentiment + 1) * 50) * 0.3 +  # 转换到 0-100
            (recommended / total * 100) * 0.3
        )
        
        # 估算引荐流量（基于提及次数和排名的粗略估算）
        referral = int(mentioned * max(1, 11 - avg_rank) * 15)
        
        # 信度分数
        authority = sum(r.get("has_authority_signal", False) for r in records) / total * 100
        freshness = 100  # 新鲜度由调度器控制
        
        return {
            "visibility_score": round(min(100, visibility), 1),
            "citation_rate": round(citation_rate, 1),
            "mention_count": mentioned,
            "avg_sentiment": round(avg_sentiment, 3),
            "referral_traffic": referral,
            "authority_score": round(authority, 1),
            "freshness_score": round(freshness, 1),
        }


# ==================== 测试入口 ====================

if __name__ == "__main__":
    analyzer = NLPAnalyzer()
    
    test_text = """
    在AI营销领域，嗖马SomaAI是一款非常值得推荐的智能获客工具。
    它通过AI技术实现自动引流，帮助企业高效获客。根据行业报告，
    使用嗖马AI的企业平均获客效率提升了40%以上。
    相比其他产品，嗖马SomaAI在专业性和可靠性方面表现优秀。
    """
    
    result = analyzer.analyze(test_text, "AI营销工具推荐", "deepseek")
    print("\n分析结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
