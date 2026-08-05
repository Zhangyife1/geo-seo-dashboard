(function() {
  window.GEOCharts = {};
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim() || '#00d4aa';
  var accent2 = style.getPropertyValue('--accent2').trim() || '#3b82f6';
  var accent3 = style.getPropertyValue('--accent3').trim() || '#f59e0b';
  var accent4 = style.getPropertyValue('--accent4').trim() || '#ef4444';
  var accent5 = style.getPropertyValue('--accent5').trim() || '#8b5cf6';
  var ink = style.getPropertyValue('--ink').trim() || '#f0f4f8';
  var muted = style.getPropertyValue('--muted').trim() || '#94a3b8';
  var rule = style.getPropertyValue('--rule').trim() || '#1e293b';
  var bg2 = style.getPropertyValue('--bg2').trim() || '#111827';
  var bg3 = style.getPropertyValue('--bg3').trim() || '#1a2332';

  var palette = [accent, accent2, accent3, accent5, accent4, '#06b6d4'];

  var commonGrid = { left: '3%', right: '4%', bottom: '3%', top: '12%', containLabel: true };
  var commonTooltip = { trigger: 'axis', backgroundColor: 'rgba(17,24,39,0.95)', borderColor: rule, textStyle: { color: ink }, appendToBody: true };

  // --- Chart: Platform Radar ---
  var chartPlatformRadar = echarts.init(document.getElementById('chart-platform-radar'), null, { renderer: 'svg' });
  chartPlatformRadar.setOption({
    animation: true, animationDuration: 1500,
    tooltip: { trigger: 'item', backgroundColor: 'rgba(17,24,39,0.95)', borderColor: rule, textStyle: { color: ink }, appendToBody: true },
    radar: {
      indicator: [
        { name: 'DeepSeek', max: 100 }, { name: 'ChatGPT', max: 100 }, { name: '豆包', max: 100 },
        { name: '文心一言', max: 100 }, { name: 'Kimi', max: 100 }, { name: 'Perplexity', max: 100 }
      ],
      shape: 'polygon', splitNumber: 4,
      axisName: { color: muted, fontSize: 11 },
      splitLine: { lineStyle: { color: rule } },
      splitArea: { show: true, areaStyle: { color: ['rgba(0,212,170,0.02)', 'rgba(0,212,170,0.04)'] } },
      axisLine: { lineStyle: { color: rule } }
    },
    series: [{
      type: 'radar',
      data: [
        { value: [92, 78, 85, 71, 66, 58], name: '嗖马SomaAI', symbol: 'circle', symbolSize: 6,
          lineStyle: { width: 2, color: accent }, areaStyle: { color: 'rgba(0,212,170,0.15)' }, itemStyle: { color: accent } },
        { value: [70, 85, 65, 80, 55, 72], name: '行业平均', symbol: 'circle', symbolSize: 4,
          lineStyle: { width: 1.5, color: muted, type: 'dashed' }, areaStyle: { color: 'rgba(148,163,184,0.06)' }, itemStyle: { color: muted } }
      ]
    }],
    legend: { bottom: 0, textStyle: { color: muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
    graphic: { type: 'text', right: 10, bottom: 5, z: 100, style: { text: '示意数据', fill: muted, fontSize: 10, opacity: 0.5 } }
  });
  window.GEOCharts.platformRadar = chartPlatformRadar;
  window.addEventListener('resize', function() { chartPlatformRadar.resize(); });

  // --- Chart: Citation Trend ---
  var chartCitationTrend = echarts.init(document.getElementById('chart-citation-trend'), null, { renderer: 'svg' });
  var weeks = ['W1','W2','W3','W4','W5','W6','W7','W8','W9','W10','W11','W12'];
  chartCitationTrend.setOption({
    animation: true, animationDuration: 1500,
    tooltip: { ...commonTooltip, axisPointer: { type: 'cross', crossStyle: { color: muted } } },
    legend: { top: 0, textStyle: { color: muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
    grid: commonGrid,
    xAxis: { type: 'category', data: weeks, axisLine: { lineStyle: { color: rule } }, axisLabel: { color: muted, fontSize: 10 } },
    yAxis: [
      { type: 'value', name: '引用率%', min: 0, max: 100, axisLine: { show: false }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLabel: { color: muted, fontSize: 10 }, nameTextStyle: { color: muted, fontSize: 10 } },
      { type: 'value', name: '可见性', min: 0, max: 100, axisLine: { show: false }, splitLine: { show: false }, axisLabel: { color: muted, fontSize: 10 }, nameTextStyle: { color: muted, fontSize: 10 } }
    ],
    series: [
      { name: '引用率', type: 'line', data: [32, 35, 38, 42, 45, 48, 52, 56, 58, 61, 63, 64.2], smooth: true, symbol: 'circle', symbolSize: 5,
        lineStyle: { width: 2.5, color: accent }, itemStyle: { color: accent },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(0,212,170,0.25)' }, { offset: 1, color: 'rgba(0,212,170,0)' }] } } },
      { name: '可见性指数', type: 'line', yAxisIndex: 1, data: [45, 50, 55, 58, 62, 65, 68, 71, 73, 75, 77, 78.5], smooth: true, symbol: 'circle', symbolSize: 5,
        lineStyle: { width: 2.5, color: accent2 }, itemStyle: { color: accent2 },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.2)' }, { offset: 1, color: 'rgba(59,130,246,0)' }] } } },
      { name: '行业平均引用率', type: 'line', data: [28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39], smooth: true, symbol: 'none',
        lineStyle: { width: 1.5, color: muted, type: 'dashed' }, itemStyle: { color: muted } }
    ]
  });
  window.GEOCharts.citationTrend = chartCitationTrend;
  window.addEventListener('resize', function() { chartCitationTrend.resize(); });

  // --- Chart: Keyword Heatmap ---
  var chartKeywordHeatmap = echarts.init(document.getElementById('chart-keyword-heatmap'), null, { renderer: 'svg' });
  var platforms = ['DeepSeek', 'ChatGPT', '豆包', '文心一言', 'Kimi', 'Perplexity'];
  var keywords = ['AI营销', '获客机器人', '智能客服', '自动引流', '私域运营', '内容生成', '用户增长', 'CRM'];
  var heatmapData = [
    [0,0,92],[0,1,88],[0,2,75],[0,3,82],[0,4,70],[0,5,65],[0,6,78],[0,7,60],
    [1,0,80],[1,1,85],[1,2,72],[1,3,78],[1,4,68],[1,5,70],[1,6,75],[1,7,65],
    [2,0,85],[2,1,82],[2,2,78],[2,3,80],[2,4,72],[2,5,68],[2,6,70],[2,7,62],
    [3,0,70],[3,1,72],[3,2,68],[3,3,75],[3,4,65],[3,5,60],[3,6,62],[3,7,55],
    [4,0,65],[4,1,68],[4,2,62],[4,3,70],[4,4,58],[4,5,55],[4,6,60],[4,7,50],
    [5,0,58],[5,1,60],[5,2,55],[5,3,62],[5,4,52],[5,5,50],[5,6,55],[5,7,48]
  ];
  chartKeywordHeatmap.setOption({
    animation: true, animationDuration: 1500,
    tooltip: { position: 'top', backgroundColor: 'rgba(17,24,39,0.95)', borderColor: rule, textStyle: { color: ink }, appendToBody: true, formatter: function(p) { return platforms[p.value[1]] + ' / ' + keywords[p.value[0]] + '<br/>覆盖度: <strong>' + p.value[2] + '%</strong>'; } },
    grid: { left: '16%', right: '8%', bottom: '12%', top: '5%' },
    xAxis: { type: 'category', data: keywords, splitArea: { show: false }, axisLine: { lineStyle: { color: rule } }, axisLabel: { color: muted, fontSize: 10, rotate: 30 } },
    yAxis: { type: 'category', data: platforms, splitArea: { show: false }, axisLine: { lineStyle: { color: rule } }, axisLabel: { color: muted, fontSize: 10 } },
    visualMap: { min: 40, max: 100, calculable: false, orient: 'horizontal', left: 'center', bottom: '0%',
      inRange: { color: [bg3, accent2, accent] }, outOfRange: { color: 'transparent' },
      textStyle: { color: muted, fontSize: 10 }, itemWidth: 12, itemHeight: 100 },
    series: [{
      type: 'heatmap', data: heatmapData,
      label: { show: true, fontSize: 10, color: ink, formatter: function(p) { return p.value[2]; } },
      itemStyle: { borderColor: bg2, borderWidth: 1 }
    }],
    graphic: { type: 'text', right: 10, bottom: 5, z: 100, style: { text: '示意数据', fill: muted, fontSize: 10, opacity: 0.5 } }
  });
  window.GEOCharts.keywordHeatmap = chartKeywordHeatmap;
  window.addEventListener('resize', function() { chartKeywordHeatmap.resize(); });

  // --- Chart: Sentiment Gauge ---
  var chartSentimentGauge = echarts.init(document.getElementById('chart-sentiment-gauge'), null, { renderer: 'svg' });
  chartSentimentGauge.setOption({
    animation: true, animationDuration: 1500,
    tooltip: { backgroundColor: 'rgba(17,24,39,0.95)', borderColor: rule, textStyle: { color: ink }, appendToBody: true },
    series: [
      {
        type: 'gauge', startAngle: 200, endAngle: -20, min: 0, max: 100, splitNumber: 10,
        itemStyle: { color: accent },
        progress: { show: true, width: 14, roundCap: true },
        pointer: { show: true, length: '60%', width: 4, itemStyle: { color: ink } },
        axisLine: { lineStyle: { width: 14, color: [[1, rule]] } },
        axisTick: { show: false },
        splitLine: { length: 8, lineStyle: { width: 1, color: rule } },
        axisLabel: { distance: 18, color: muted, fontSize: 9 },
        anchor: { show: true, showAbove: true, size: 12, itemStyle: { borderColor: accent, borderWidth: 2, color: bg2 } },
        title: { show: true, offsetCenter: [0, '30%'], fontSize: 12, color: muted },
        detail: { valueAnimation: true, fontSize: 28, offsetCenter: [0, '-10%'], fontFamily: 'Tektur', fontWeight: 500, color: accent, formatter: '{value}' },
        data: [{ value: 86, name: '好感度评分' }]
      },
      {
        type: 'gauge', startAngle: 200, endAngle: -20, min: 0, max: 100, radius: '72%',
        itemStyle: { color: accent3 },
        progress: { show: true, width: 8, roundCap: true },
        pointer: { show: false },
        axisLine: { lineStyle: { width: 8, color: [[1, 'transparent']] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: { show: false },
        detail: { show: false },
        data: [{ value: 72 }]
      }
    ]
  });
  window.GEOCharts.sentimentGauge = chartSentimentGauge;
  window.addEventListener('resize', function() { chartSentimentGauge.resize(); });

  // --- Chart: Quality Radar ---
  var chartQualityRadar = echarts.init(document.getElementById('chart-quality-radar'), null, { renderer: 'svg' });
  chartQualityRadar.setOption({
    animation: true, animationDuration: 1500,
    tooltip: { trigger: 'item', backgroundColor: 'rgba(17,24,39,0.95)', borderColor: rule, textStyle: { color: ink }, appendToBody: true },
    radar: {
      indicator: [
        { name: '经验性 E', max: 100 }, { name: '专业性 E', max: 100 }, { name: '权威性 A', max: 100 },
        { name: '可信度 T', max: 100 }, { name: '结构化数据', max: 100 }, { name: '内容时效', max: 100 }
      ],
      shape: 'polygon', splitNumber: 4,
      axisName: { color: muted, fontSize: 10 },
      splitLine: { lineStyle: { color: rule } },
      splitArea: { show: true, areaStyle: { color: ['rgba(139,92,246,0.03)', 'rgba(139,92,246,0.06)'] } },
      axisLine: { lineStyle: { color: rule } }
    },
    series: [{
      type: 'radar',
      data: [
        { value: [78, 85, 72, 80, 92, 88], name: '嗖马SomaAI', symbol: 'circle', symbolSize: 5,
          lineStyle: { width: 2, color: accent5 }, areaStyle: { color: 'rgba(139,92,246,0.15)' }, itemStyle: { color: accent5 } },
        { value: [65, 70, 60, 68, 55, 62], name: '优化前基准', symbol: 'circle', symbolSize: 4,
          lineStyle: { width: 1.5, color: muted, type: 'dashed' }, areaStyle: { color: 'rgba(148,163,184,0.05)' }, itemStyle: { color: muted } }
      ]
    }],
    legend: { bottom: 0, textStyle: { color: muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
    graphic: { type: 'text', right: 10, bottom: 5, z: 100, style: { text: '示意数据', fill: muted, fontSize: 10, opacity: 0.5 } }
  });
  window.GEOCharts.qualityRadar = chartQualityRadar;
  window.addEventListener('resize', function() { chartQualityRadar.resize(); });

  // --- Chart: GEO vs SEO Compare ---
  var chartGeoSeoCompare = echarts.init(document.getElementById('chart-geo-seo-compare'), null, { renderer: 'svg' });
  var categories = ['品牌曝光', '内容引用', '用户信任', '流量质量', '转化效率', '长期价值'];
  chartGeoSeoCompare.setOption({
    animation: true, animationDuration: 1500,
    tooltip: { ...commonTooltip, axisPointer: { type: 'shadow' } },
    legend: { top: 0, textStyle: { color: muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
    grid: commonGrid,
    xAxis: { type: 'category', data: categories, axisLine: { lineStyle: { color: rule } }, axisLabel: { color: muted, fontSize: 10 } },
    yAxis: { type: 'value', max: 100, axisLine: { show: false }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLabel: { color: muted, fontSize: 10 } },
    series: [
      { name: 'GEO', type: 'bar', data: [85, 78, 82, 88, 75, 90], barWidth: '28%',
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: accent }, { offset: 1, color: 'rgba(0,212,170,0.3)' }] }, borderRadius: [4, 4, 0, 0] } },
      { name: 'SEO', type: 'bar', data: [62, 55, 58, 65, 60, 70], barWidth: '28%',
        itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: accent2 }, { offset: 1, color: 'rgba(59,130,246,0.3)' }] }, borderRadius: [4, 4, 0, 0] } }
    ],
    graphic: { type: 'text', right: 10, bottom: 5, z: 100, style: { text: '示意数据', fill: muted, fontSize: 10, opacity: 0.5 } }
  });
  window.GEOCharts.geoSeoCompare = chartGeoSeoCompare;
  window.addEventListener('resize', function() { chartGeoSeoCompare.resize(); });

  // --- Chart: Authority Metrics ---
  var chartAuthority = echarts.init(document.getElementById('chart-authority'), null, { renderer: 'svg' });
  chartAuthority.setOption({
    animation: true, animationDuration: 1500,
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(17,24,39,0.95)', borderColor: rule, textStyle: { color: ink }, appendToBody: true },
    legend: { top: 0, textStyle: { color: muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
    grid: commonGrid,
    xAxis: { type: 'category', data: weeks, axisLine: { lineStyle: { color: rule } }, axisLabel: { color: muted, fontSize: 10 } },
    yAxis: { type: 'value', max: 100, axisLine: { show: false }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLabel: { color: muted, fontSize: 10 } },
    series: [
      { name: '引用源影响因子', type: 'line', data: [45, 48, 52, 55, 58, 62, 65, 68, 72, 75, 78, 80], smooth: true, symbol: 'circle', symbolSize: 4,
        lineStyle: { width: 2, color: accent5 }, itemStyle: { color: accent5 } },
      { name: '机构信度等级', type: 'line', data: [50, 52, 55, 58, 60, 63, 65, 68, 70, 73, 75, 77], smooth: true, symbol: 'circle', symbolSize: 4,
        lineStyle: { width: 2, color: accent3 }, itemStyle: { color: accent3 } },
      { name: '数据时效性', type: 'line', data: [60, 62, 65, 68, 72, 75, 78, 80, 83, 85, 87, 89], smooth: true, symbol: 'circle', symbolSize: 4,
        lineStyle: { width: 2, color: accent }, itemStyle: { color: accent } }
    ],
    graphic: { type: 'text', right: 10, bottom: 5, z: 100, style: { text: '示意数据', fill: muted, fontSize: 10, opacity: 0.5 } }
  });
  window.GEOCharts.authority = chartAuthority;
  window.addEventListener('resize', function() { chartAuthority.resize(); });

  // --- Chart: SEO Baseline ---
  var chartSeoBaseline = echarts.init(document.getElementById('chart-seo-baseline'), null, { renderer: 'svg' });
  chartSeoBaseline.setOption({
    animation: true, animationDuration: 1500,
    tooltip: { trigger: 'item', backgroundColor: 'rgba(17,24,39,0.95)', borderColor: rule, textStyle: { color: ink }, appendToBody: true },
    legend: { top: 0, textStyle: { color: muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '12%', containLabel: true },
    xAxis: { type: 'value', max: 100, axisLine: { lineStyle: { color: rule } }, splitLine: { lineStyle: { color: rule, type: 'dashed' } }, axisLabel: { color: muted, fontSize: 10 } },
    yAxis: { type: 'category', data: ['域名权重','收录页面','核心词排名','外链质量','页面速度','移动适配'], axisLine: { lineStyle: { color: rule } }, axisLabel: { color: muted, fontSize: 10 } },
    series: [
      { name: '当前值', type: 'bar', data: [68, 82, 55, 74, 91, 88], barWidth: '40%',
        itemStyle: { color: function(p) { return palette[p.dataIndex % palette.length]; }, borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'right', color: ink, fontSize: 11, fontFamily: 'GeistMono' } },
      { name: '行业TOP10均值', type: 'bar', data: [78, 88, 72, 82, 88, 90], barWidth: '40%', barGap: '-100%',
        itemStyle: { color: 'transparent', borderColor: muted, borderWidth: 1, borderType: 'dashed', borderRadius: [0, 4, 4, 0] }, label: { show: false } }
    ],
    graphic: { type: 'text', right: 10, bottom: 5, z: 100, style: { text: '示意数据', fill: muted, fontSize: 10, opacity: 0.5 } }
  });
  window.GEOCharts.seoBaseline = chartSeoBaseline;
  window.addEventListener('resize', function() { chartSeoBaseline.resize(); });

  // 暴露趋势图更新函数
  window.GEOCharts.updateTrend = function(trendData) {
    if (!trendData || !trendData.length) {
      // 无真实趋势数据：清空假数据并显示占位提示
      chartCitationTrend.setOption({
        xAxis: { data: [] },
        series: [
          { name: '引用率', data: [] },
          { name: '可见性指数', data: [] },
          { name: '行业平均引用率', data: [] }
        ],
        graphic: { type: 'text', left: 'center', top: 'middle', z: 100, style: { text: '暂无真实趋势数据（真实采集天数不足）', fill: muted, fontSize: 12 } }
      });
      return;
    }
    var dates = trendData.map(function(d) { return d.date.substring(5); }); // MM-DD
    var visData = trendData.map(function(d) { return d.avg_visibility; });
    var citData = trendData.map(function(d) { return d.avg_citation_rate; });

    chartCitationTrend.setOption({
      xAxis: { data: dates },
      series: [
        { name: '引用率', data: citData },
        { name: '可见性指数', data: visData },
        { name: '行业平均引用率', data: [] } // 清空行业平均（无真实数据时不显示）
      ],
      graphic: [] // 移除示意标注
    });
  };

  // 暴露情感仪表盘更新函数
  window.GEOCharts.updateSentiment = function(score) {
    if (score === undefined || score === null || Number.isNaN(score)) return;
    var pctScore = Math.round(score); // 如果是0-100的值
    // 如果是 -1~1 的值，转换为 0~100
    if (score <= 1 && score >= -1) {
      pctScore = Math.round((score + 1) * 50);
    }
    chartSentimentGauge.setOption({
      series: [{ data: [{ value: pctScore, name: '好感度评分' }] }, { data: [{ value: Math.round(pctScore * 0.85) }] }]
    });
  };
})();
