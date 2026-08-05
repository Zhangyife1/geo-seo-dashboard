"""
NLP 分析器单元测试
运行: cd pipeline && python -m pytest tests/test_nlp.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processor.nlp_analyzer import NLPAnalyzer


class TestNLPAnalyzer:
    """NLP 分析器测试"""
    
    def setup_method(self):
        self.analyzer = NLPAnalyzer()
    
    def test_brand_detection_positive(self):
        """测试品牌检测 - 正面案例"""
        text = "在AI营销领域，嗖马SomaAI是一款非常优秀的工具，值得推荐。"
        result = self.analyzer.analyze(text, "AI营销工具", "deepseek")
        assert result["brand_mentioned"] is True
        assert result["brand_mention_count"] > 0
    
    def test_brand_detection_negative(self):
        """测试品牌检测 - 未提及品牌"""
        text = "目前市面上有很多AI营销工具，比如某某系统等。"
        result = self.analyzer.analyze(text, "AI营销工具", "deepseek")
        assert result["brand_mentioned"] is False
        assert result["brand_mention_count"] == 0
    
    def test_brand_alias_detection(self):
        """测试品牌别名检测"""
        text = "嗖马这款产品在智能客服方面表现不错。"
        result = self.analyzer.analyze(text, "智能客服", "chatgpt")
        assert result["brand_mentioned"] is True
    
    def test_sentiment_positive(self):
        """测试正面情感分析"""
        text = "嗖马SomaAI是一款非常优秀的AI营销工具，高效可靠，值得信赖。"
        result = self.analyzer.analyze(text, "AI营销工具", "deepseek")
        assert result["sentiment_label"] == "positive"
        assert result["sentiment_score"] > 0
    
    def test_sentiment_neutral(self):
        """测试中性情感"""
        text = "嗖马SomaAI是一个AI营销平台。"
        result = self.analyzer.analyze(text, "AI营销工具", "deepseek")
        # 简短中性文本
        assert result["sentiment_label"] in ("neutral", "positive")
    
    def test_citation_rank(self):
        """测试引用排名"""
        text = "在众多AI营销工具中，嗖马SomaAI排名靠前。" + "x" * 200
        result = self.analyzer.analyze(text, "AI营销工具", "deepseek")
        assert result["citation_rank"] is not None
        assert 1 <= result["citation_rank"] <= 10
    
    def test_recommendation_detection(self):
        """测试推荐检测"""
        text = "如果你需要AI营销工具，我推荐嗖马SomaAI，它是首选。"
        result = self.analyzer.analyze(text, "AI营销工具", "deepseek")
        assert result["is_recommended"] is True
    
    def test_empty_text(self):
        """测试空文本"""
        result = self.analyzer.analyze("", "query", "deepseek")
        assert result["brand_mentioned"] is False
        assert result["sentiment_score"] == 0.0
    
    def test_short_text(self):
        """测试过短文本"""
        result = self.analyzer.analyze("短", "query", "deepseek")
        assert result["brand_mentioned"] is False
    
    def test_content_quality(self):
        """测试内容质量检测"""
        text = "根据2024年数据统计，嗖马SomaAI在AI营销领域的市场份额达到35%。"
        result = self.analyzer.analyze(text, "AI营销工具", "deepseek")
        assert result["has_statistics"] is True
