import { BarChartOutlined, DatabaseOutlined, FundProjectionScreenOutlined, TeamOutlined } from '@ant-design/icons';
import { Card, Empty, Spin, Statistic, Typography } from 'antd';
import ReactECharts from 'echarts-for-react';
import 'echarts-wordcloud';
import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { fetchGroupReport } from '../api/resumes';
import type { CountItem, GroupReport, HeatmapPayload, WordCloudItem } from '../types';
import './GroupReportPage.css';

const palette = ['#1f6f68', '#d97706', '#315c9f', '#9f3a38', '#5f6f52', '#7c5c2e', '#276749', '#8b5cf6'];

const chartTitle = (title: string) => ({
  text: title,
  left: 16,
  top: 14,
  textStyle: {
    color: '#1f2a24',
    fontSize: 17,
    fontWeight: 800,
    fontFamily: 'Georgia, "Times New Roman", serif',
  },
});

const emptyText = {
  text: '暂无数据',
  left: 'center',
  top: 'middle',
  textStyle: { color: '#9a9387', fontSize: 14 },
};

const labelFormatter = (name: string) => (name.length > 12 ? `${name.slice(0, 12)}\n${name.slice(12)}` : name);

const pieOption = (title: string, items: CountItem[], options?: { compact?: boolean }) => ({
  color: palette,
  title: items.length ? chartTitle(title) : emptyText,
  tooltip: {
    trigger: 'item',
    confine: true,
    formatter: '{b}<br/>数量：{c}<br/>占比：{d}%',
  },
  legend: {
    type: 'scroll',
    orient: 'vertical',
    right: options?.compact ? 18 : 12,
    top: 70,
    bottom: 18,
    itemGap: 12,
    icon: 'roundRect',
    textStyle: { color: '#3f4a43', fontSize: 12, width: options?.compact ? 170 : 120, overflow: 'break' },
  },
  series: [
    {
      type: 'pie',
      center: options?.compact ? ['31%', '56%'] : ['34%', '56%'],
      radius: options?.compact ? ['46%', '67%'] : ['42%', '64%'],
      minShowLabelAngle: 8,
      avoidLabelOverlap: true,
      data: items.map((item) => ({ name: item.name, value: item.count })),
      label: {
        show: !options?.compact,
        formatter: ({ name, percent }: { name: string; percent: number }) => `${labelFormatter(name)}\n${percent}%`,
        color: '#1f2a24',
        fontSize: 12,
        lineHeight: 16,
      },
      emphasis: {
        label: {
          show: true,
          formatter: ({ name, percent }: { name: string; percent: number }) => `${labelFormatter(name)}\n${percent}%`,
          fontSize: 13,
          fontWeight: 800,
        },
      },
      labelLine: { show: !options?.compact, length: 16, length2: 10, maxSurfaceAngle: 80 },
    },
  ],
});

const barOption = (title: string, items: CountItem[], color = '#1f6f68') => ({
  color: [color],
  title: items.length ? chartTitle(title) : emptyText,
  tooltip: {
    trigger: 'axis',
    confine: true,
    axisPointer: { type: 'shadow' },
    formatter: (params: Array<{ name: string; value: number }>) => {
      const item = params[0];
      return `${item.name}<br/>数量：${item.value}`;
    },
  },
  grid: {
    top: 72,
    left: 132,
    right: 32,
    bottom: 30,
    containLabel: true,
  },
  xAxis: {
    type: 'value',
    axisLabel: { color: '#6b6258' },
    splitLine: { lineStyle: { color: '#ece5da' } },
  },
  yAxis: {
    type: 'category',
    data: items.map((item) => item.name).reverse(),
    axisLabel: {
      color: '#2d3932',
      fontSize: 12,
      width: 118,
      overflow: 'break',
      lineHeight: 15,
    },
    axisTick: { show: false },
    axisLine: { show: false },
  },
  series: [
    {
      type: 'bar',
      data: items.map((item) => item.count).reverse(),
      barWidth: 16,
      itemStyle: { borderRadius: [0, 8, 8, 0] },
      label: { show: true, position: 'right', color: '#2d3932', fontWeight: 700 },
    },
  ],
});

const coverageOption = (items: GroupReport['coverage']) => ({
  color: ['#d97706'],
  title: chartTitle('经历覆盖率'),
  tooltip: {
    trigger: 'axis',
    confine: true,
    axisPointer: { type: 'shadow' },
    formatter: (params: Array<{ name: string; value: number }>) => {
      const item = params[0];
      return `${item.name}<br/>覆盖率：${Math.round(item.value * 100)}%`;
    },
  },
  grid: { top: 72, left: 48, right: 28, bottom: 84, containLabel: true },
  xAxis: {
    type: 'category',
    data: items.map((item) => item.label.replace('覆盖率', '')),
    axisLabel: { interval: 0, rotate: 24, color: '#3f4a43', fontSize: 12 },
  },
  yAxis: {
    type: 'value',
    max: 1,
    axisLabel: { formatter: (value: number) => `${Math.round(value * 100)}%`, color: '#6b6258' },
    splitLine: { lineStyle: { color: '#ece5da' } },
  },
  series: [
    {
      type: 'bar',
      data: items.map((item) => item.value),
      barWidth: 24,
      itemStyle: { borderRadius: [10, 10, 0, 0] },
      label: {
        show: true,
        position: 'top',
        formatter: ({ value }: { value: number }) => `${Math.round(value * 100)}%`,
        color: '#2d3932',
        fontWeight: 800,
      },
    },
  ],
});

const wordCloudOption = (title: string, items: WordCloudItem[]) => ({
  title: items.length ? chartTitle(title) : emptyText,
  tooltip: { confine: true },
  series: [
    {
      type: 'wordCloud',
      shape: 'cardioid',
      left: 'center',
      top: 58,
      width: '92%',
      height: '76%',
      gridSize: 8,
      sizeRange: [14, 40],
      rotationRange: [-18, 18],
      textStyle: {
        fontFamily: '"Songti SC", "Noto Serif SC", serif',
        fontWeight: 800,
        color: () => palette[Math.floor(Math.random() * palette.length)],
      },
      emphasis: {
        focus: 'self',
        textStyle: { textShadowBlur: 8, textShadowColor: 'rgba(31,111,104,.25)' },
      },
      data: items,
    },
  ],
});

const heatmapOption = (heatmap: HeatmapPayload) => ({
  title: heatmap.cells.length ? chartTitle(heatmap.title) : emptyText,
  tooltip: {
    position: 'top',
    confine: true,
    formatter: (params: { data: [number, number, number] }) => {
      const [xIndex, yIndex, value] = params.data;
      return `${heatmap.y_labels[yIndex]} × ${heatmap.x_labels[xIndex]}<br/>数量：${value}`;
    },
  },
  grid: { top: 82, left: 142, right: 32, bottom: 106, containLabel: true },
  xAxis: {
    type: 'category',
    data: heatmap.x_labels,
    splitArea: { show: true },
    axisLabel: { interval: 0, rotate: 38, color: '#3f4a43', fontSize: 11, width: 78, overflow: 'break' },
  },
  yAxis: {
    type: 'category',
    data: heatmap.y_labels,
    splitArea: { show: true },
    axisLabel: { color: '#3f4a43', fontSize: 12, width: 124, overflow: 'break', lineHeight: 15 },
  },
  visualMap: {
    min: 0,
    max: Math.max(...heatmap.cells.map((cell) => cell.value), 1),
    calculable: true,
    orient: 'horizontal',
    left: 'center',
    bottom: 18,
    inRange: { color: ['#f7efe2', '#d7a34a', '#1f6f68'] },
  },
  series: [
    {
      type: 'heatmap',
      data: heatmap.cells.map((cell) => [heatmap.x_labels.indexOf(cell.x), heatmap.y_labels.indexOf(cell.y), cell.value]),
      label: { show: true, color: '#1f2a24', fontSize: 11 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(31,111,104,.25)' } },
    },
  ],
});

function ChartCard({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <Card className={`report-chart-card ${className}`} bordered={false}>{children}</Card>;
}

function ReportChart({ option, height = 360 }: { option: object; height?: number }) {
  return <ReactECharts option={option} notMerge style={{ height, width: '100%' }} />;
}

export function GroupReportPage() {
  const [data, setData] = useState<GroupReport | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        setData(await fetchGroupReport());
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  if (loading && !data) {
    return (
      <div className="group-report-shell group-report-loading">
        <Spin size="large" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="group-report-shell">
        <Card bordered={false} className="report-empty-card">
          <Empty description="暂无群体分析数据" />
        </Card>
      </div>
    );
  }

  const statCards = [
    { label: '去重学生数', value: data.summary.student_count, icon: <TeamOutlined /> },
    { label: '原始简历数', value: data.summary.raw_resume_count, icon: <DatabaseOutlined /> },
    { label: '主版本简历数', value: data.summary.primary_resume_count, icon: <FundProjectionScreenOutlined /> },
    { label: '学校数', value: data.summary.school_count, icon: <BarChartOutlined /> },
    { label: '专业数', value: data.summary.major_count, icon: <BarChartOutlined /> },
    { label: '平均项目数', value: data.summary.avg_project_count, precision: 2, icon: <FundProjectionScreenOutlined /> },
  ];

  return (
    <div className="group-report-shell">
      <section className="report-hero">
        <div>
          <Typography.Text className="report-kicker">Student Cohort Observatory</Typography.Text>
          <Typography.Title level={2} className="report-title">
            群体分析报告
          </Typography.Title>
          <Typography.Paragraph className="report-subtitle">
            基于主版本学生简历统计学校、专业、经历覆盖、画像标签和技能方向分布。页面采用完整标签显示策略，图表文字不会被压缩省略。
          </Typography.Paragraph>
        </div>
        <div className="report-meta-card">
          <span>统计口径</span>
          <strong>主版本简历</strong>
          <small>历史版本不计入群体统计</small>
        </div>
      </section>

      <section className="report-stat-grid">
        {statCards.map((item) => (
          <Card bordered={false} className="report-stat-card" key={item.label}>
            <div className="report-stat-icon">{item.icon}</div>
            <Statistic title={item.label} value={item.value} precision={item.precision} />
          </Card>
        ))}
      </section>

      <section className="report-section">
        <div className="report-section-heading">
          <span>01</span>
          <h3>基础分布</h3>
        </div>
        <div className="report-grid report-grid-foundation">
          <ChartCard className="report-chart-large">
            <ReportChart option={pieOption('学校层次分布', data.basic_distribution.school_levels)} height={420} />
          </ChartCard>
          <ChartCard>
            <ReportChart option={barOption('学校 Top 10', data.basic_distribution.schools_top, '#315c9f')} height={420} />
          </ChartCard>
          <ChartCard>
            <ReportChart option={barOption('专业 Top 10', data.basic_distribution.majors_top, '#1f6f68')} height={420} />
          </ChartCard>
        </div>
      </section>

      <section className="report-section">
        <div className="report-section-heading">
          <span>02</span>
          <h3>画像与经历覆盖</h3>
        </div>
        <div className="report-grid report-grid-wide">
          <ChartCard>
            <ReportChart option={pieOption('学生类型分布', data.tag_distribution.student_types, { compact: true })} height={420} />
          </ChartCard>
          <ChartCard className="report-chart-wide">
            <ReportChart option={coverageOption(data.coverage)} height={420} />
          </ChartCard>
        </div>
      </section>

      <section className="report-section">
        <div className="report-section-heading">
          <span>03</span>
          <h3>方向与标签</h3>
        </div>
        <div className="report-grid report-grid-tags">
          <ChartCard>
            <ReportChart option={wordCloudOption('研究方向词云', data.wordcloud.research_direction)} height={390} />
          </ChartCard>
          <ChartCard>
            <ReportChart option={wordCloudOption('岗位方向词云', data.wordcloud.job_direction)} height={390} />
          </ChartCard>
          <ChartCard>
            <ReportChart option={barOption('研究方向 Top 10', data.tag_distribution.research_direction_tags, '#1f6f68')} height={390} />
          </ChartCard>
          <ChartCard>
            <ReportChart option={barOption('岗位方向 Top 10', data.tag_distribution.job_direction_tags, '#8b5cf6')} height={390} />
          </ChartCard>
          <ChartCard>
            <ReportChart option={barOption('方法标签 Top 10', data.tag_distribution.method_tags, '#315c9f')} height={390} />
          </ChartCard>
          <ChartCard>
            <ReportChart option={barOption('学术潜力标签 Top 10', data.tag_distribution.academic_potential_tags, '#d97706')} height={390} />
          </ChartCard>
          <ChartCard>
            <ReportChart option={barOption('能力标签 Top 10', data.tag_distribution.capability_tags, '#276749')} height={390} />
          </ChartCard>
          <ChartCard>
            <ReportChart option={barOption('行为标签 Top 10', data.tag_distribution.behavior_tags, '#9f3a38')} height={390} />
          </ChartCard>
        </div>
      </section>

      <section className="report-section">
        <div className="report-section-heading">
          <span>04</span>
          <h3>技能热力图</h3>
        </div>
        <div className="report-grid report-grid-heatmaps">
          {data.heatmaps.map((heatmap) => (
            <ChartCard key={heatmap.title}>
              {heatmap.cells.length ? (
                <ReportChart option={heatmapOption(heatmap)} height={500} />
              ) : (
                <div className="report-empty-block">
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={`${heatmap.title}暂无数据`} />
                </div>
              )}
            </ChartCard>
          ))}
        </div>
      </section>
    </div>
  );
}
