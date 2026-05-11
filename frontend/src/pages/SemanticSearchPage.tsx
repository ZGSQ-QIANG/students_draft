import { Button, Card, Empty, Form, Input, List, Select, Space, Tag, Typography } from 'antd';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { semanticSearchResumes, type ResumeSemanticSearchParams } from '../api/resumes';
import type { SemanticSearchResult } from '../types';

const CHUNK_TYPE_OPTIONS = [
  { label: '教育经历', value: 'education' },
  { label: '项目经历', value: 'project' },
  { label: '实习经历', value: 'internship' },
  { label: '论文成果', value: 'paper' },
  { label: '专利成果', value: 'patent' },
  { label: '竞赛经历', value: 'competition' },
  { label: '奖项荣誉', value: 'award' },
  { label: '证书', value: 'certificate' }
];

const CHUNK_TYPE_LABELS: Record<string, string> = Object.fromEntries(CHUNK_TYPE_OPTIONS.map((item) => [item.value, item.label]));
const formatPercent = (value: number) => `${Math.round(value * 100)}%`;
const formatScoreBreakdown = (hit: SemanticSearchResult['hits'][number]) => {
  const rrfText = hit.rrf_score !== null && hit.rrf_score !== undefined ? `RRF ${hit.rrf_score.toFixed(3)}` : 'RRF -';
  const denseText = hit.dense_rank ? `Dense #${hit.dense_rank}` : 'Dense -';
  const keywordText = hit.keyword_rank ? `Keyword #${hit.keyword_rank}` : 'Keyword -';
  if (hit.score_source === 'rerank' && hit.rerank_score !== null && hit.rerank_score !== undefined) {
    return `Rerank ${formatPercent(hit.rerank_score)} · ${rrfText} · ${denseText} · ${keywordText}`;
  }
  return `${rrfText} · ${denseText} · ${keywordText} · Rerank 未启用/失败`;
};

export function SemanticSearchPage() {
  const [form] = Form.useForm<ResumeSemanticSearchParams>();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SemanticSearchResult[]>([]);

  const onFinish = async (values: ResumeSemanticSearchParams) => {
    setLoading(true);
    try {
      setResults(await semanticSearchResumes(values));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card>
        <Typography.Title level={4} style={{ marginBottom: 8 }}>
          学生语义搜索
        </Typography.Title>
        <Typography.Text type="secondary">
          使用 LangChain + Chroma 在学生简历经历块中做语义检索，适合搜索研究主题、项目方向和成果线索。
        </Typography.Text>
        <Form
          form={form}
          layout="vertical"
          initialValues={{ top_k: 5, chunk_types: [] }}
          onFinish={(values) => void onFinish(values)}
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="query"
            label="查询文本"
            rules={[{ required: true, message: '请输入查询内容' }]}
          >
            <Input.TextArea rows={3} placeholder="例如：找做过教育数据挖掘或推荐系统项目的学生" />
          </Form.Item>
          <Space align="start" wrap>
            <Form.Item name="top_k" label="返回数量">
              <Select
                style={{ width: 120 }}
                options={[3, 5, 8, 10].map((value) => ({ label: `${value}`, value }))}
              />
            </Form.Item>
            <Form.Item name="chunk_types" label="限定块类型">
              <Select
                mode="multiple"
                allowClear
                style={{ width: 360 }}
                placeholder="不选则全类型搜索"
                options={CHUNK_TYPE_OPTIONS}
              />
            </Form.Item>
            <Form.Item label=" ">
              <Space>
                <Button type="primary" htmlType="submit" loading={loading}>
                  开始搜索
                </Button>
                <Button
                  onClick={() => {
                    form.resetFields();
                    setResults([]);
                  }}
                >
                  重置
                </Button>
              </Space>
            </Form.Item>
          </Space>
        </Form>
      </Card>

      <Card loading={loading} title="搜索结果">
        {results.length === 0 ? (
          <Empty description="暂无结果，输入查询后开始语义检索" />
        ) : (
          <List
            itemLayout="vertical"
            dataSource={results}
            renderItem={(item) => (
              <List.Item
                key={item.resume_id}
                extra={
                  <Space direction="vertical" size={4}>
                    <Typography.Text strong>最高匹配分 {formatPercent(item.best_score)}</Typography.Text>
                    <Link to={`/resumes/${item.resume_id}`}>查看详情</Link>
                  </Space>
                }
              >
                <List.Item.Meta
                  title={`${item.student_name || '未命名学生'}  /  ${item.school_name || '学校未知'}  /  ${item.major || '专业未知'}`}
                  description={item.student_type || '暂无画像类型'}
                />
                <Space wrap size={[8, 8]} style={{ marginBottom: 12 }}>
                  {item.hits.map((hit) => (
                    <Tag key={hit.chunk_id}>{CHUNK_TYPE_LABELS[hit.chunk_type] || hit.chunk_type}</Tag>
                  ))}
                </Space>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {item.hits.map((hit) => (
                    <Card
                      key={hit.chunk_id}
                      size="small"
                      type="inner"
                      title={`${CHUNK_TYPE_LABELS[hit.chunk_type] || hit.chunk_type} · ${formatScoreBreakdown(hit)}`}
                    >
                      <Typography.Paragraph style={{ marginBottom: 0 }}>
                        {hit.content_text}
                      </Typography.Paragraph>
                    </Card>
                  ))}
                </Space>
              </List.Item>
            )}
          />
        )}
      </Card>
    </Space>
  );
}
