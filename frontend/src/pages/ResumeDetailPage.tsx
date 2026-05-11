import { Button, Card, Col, Divider, Form, Input, Row, Space, Tag, Typography, message } from 'antd';
import TextArea from 'antd/es/input/TextArea';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchResumeDetail, saveReview } from '../api/resumes';
import type { ResumeDetail } from '../types';

const SECTION_LABELS: Array<{ key: string; label: string }> = [
  { key: 'basic_info', label: '基本信息' },
  { key: 'education', label: '教育经历' },
  { key: 'project', label: '项目经历' },
  { key: 'internship', label: '实习经历' },
  { key: 'paper', label: '论文成果' },
  { key: 'patent', label: '专利成果' },
  { key: 'competition', label: '竞赛经历' },
  { key: 'award', label: '获奖经历' },
  { key: 'certificate', label: '证书经历' },
  { key: 'skills', label: '技能证书' },
  { key: 'self_eval', label: '自我评价' }
];

export function ResumeDetailPage() {
  const params = useParams();
  const resumeId = Number(params.id);
  const [detail, setDetail] = useState<ResumeDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try {
      const result = await fetchResumeDetail(resumeId);
      setDetail(result);
      form.setFieldsValue({
        basic_info: result.basic_info,
        portrait: {
          ...result.portrait,
          capability_tags: (result.portrait?.capability_tags || []).join('，'),
          behavior_tags: (result.portrait?.behavior_tags || []).join('，'),
          job_direction_tags: (result.portrait?.job_direction_tags || []).join('，'),
          research_direction_tags: (result.portrait?.research_direction_tags || []).join('，'),
          method_tags: (result.portrait?.method_tags || []).join('，'),
          academic_potential_tags: (result.portrait?.academic_potential_tags || []).join('，')
        }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [resumeId]);

  if (!detail) {
    return <Card loading={loading} />;
  }

  const sectionMap = detail.sections.reduce<Map<string, ResumeDetail['sections']>>((map, section) => {
    const current = map.get(section.section_type) || [];
    current.push(section);
    map.set(section.section_type, current);
    return map;
  }, new Map());

  return (
    <Space direction="vertical" size={24} style={{ width: '100%' }}>
      <Card>
        <Space direction="vertical" size={4}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            {detail.source_file_name}
          </Typography.Title>
          <Space>
            <Tag color="gold">{detail.analysis_status}</Tag>
            <Tag>{detail.parse_status}</Tag>
            <Tag color="blue">{detail.extract_status}</Tag>
            <Tag color="gold">版本 {detail.current_version}</Tag>
          </Space>
        </Space>
      </Card>

      <Row gutter={24} align="top">
        <Col span={10}>
          <Card title="原文分块" extra={<Button onClick={() => void load()}>刷新</Button>}>
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              {SECTION_LABELS.map((sectionGroup) => {
                const items = sectionMap.get(sectionGroup.key) || [];
                return (
                  <Card key={sectionGroup.key} size="small" style={{ background: '#fafafa' }}>
                    <Typography.Text strong>{sectionGroup.label}</Typography.Text>
                    <Divider style={{ margin: '12px 0' }} />
                    {items.length ? (
                      <Space direction="vertical" size={12} style={{ width: '100%' }}>
                        {items.map((section) => (
                          <Typography.Paragraph key={section.id} style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                            {section.raw_content}
                          </Typography.Paragraph>
                        ))}
                      </Space>
                    ) : (
                      <Typography.Text type="secondary">无</Typography.Text>
                    )}
                  </Card>
                );
              })}
            </Space>
          </Card>
        </Col>
        <Col span={14}>
          <Space direction="vertical" size={24} style={{ width: '100%' }}>
            <Card title="结构化结果">
              <Typography.Paragraph>
                姓名：{detail.basic_info?.name || '-'}，学历：{detail.basic_info?.highest_degree || '-'}，毕业时间：
                {detail.basic_info?.graduation_date || '-'}
              </Typography.Paragraph>
              <Typography.Paragraph>技能：{detail.skills.map((item) => item.skill_name).join('、') || '-'}</Typography.Paragraph>
              <Typography.Paragraph>研究兴趣：{detail.basic_info?.research_interest || '-'}</Typography.Paragraph>
              <Typography.Paragraph>目标方向：{detail.basic_info?.target_research_direction || '-'}</Typography.Paragraph>
              <Typography.Paragraph>教育经历数：{detail.educations.length}</Typography.Paragraph>
              <Typography.Paragraph>项目经历数：{detail.projects.length}</Typography.Paragraph>
              <Typography.Paragraph>实习经历数：{detail.internships.length}</Typography.Paragraph>
              <Typography.Paragraph>论文成果数：{detail.papers.length}</Typography.Paragraph>
              <Typography.Paragraph>专利成果数：{detail.patents.length}</Typography.Paragraph>
              <Typography.Paragraph>竞赛成果数：{detail.competitions.length}</Typography.Paragraph>
            </Card>

            <Card title="画像结果">
              <Typography.Paragraph>学生类型：{detail.portrait?.student_type || '-'}</Typography.Paragraph>
              <Typography.Paragraph>
                研究方向：
                {(detail.portrait?.research_direction_tags || []).map((item) => (
                  <Tag color="geekblue" key={item}>{item}</Tag>
                ))}
              </Typography.Paragraph>
              <Typography.Paragraph>
                方法能力：
                {(detail.portrait?.method_tags || []).map((item) => (
                  <Tag color="cyan" key={item}>{item}</Tag>
                ))}
              </Typography.Paragraph>
              <Typography.Paragraph>
                学术潜力：
                {(detail.portrait?.academic_potential_tags || []).map((item) => (
                  <Tag color="green" key={item}>{item}</Tag>
                ))}
              </Typography.Paragraph>
              <Typography.Paragraph>
                能力标签：
                {(detail.portrait?.capability_tags || []).map((item) => (
                  <Tag key={item}>{item}</Tag>
                ))}
              </Typography.Paragraph>
              <Typography.Paragraph>
                行为标签：
                {(detail.portrait?.behavior_tags || []).map((item) => (
                  <Tag color="green" key={item}>{item}</Tag>
                ))}
              </Typography.Paragraph>
              <Typography.Paragraph>
                岗位方向：
                {(detail.portrait?.job_direction_tags || []).map((item) => (
                  <Tag color="purple" key={item}>{item}</Tag>
                ))}
              </Typography.Paragraph>
              <Typography.Paragraph style={{ whiteSpace: 'pre-wrap' }}>{detail.portrait?.portrait_summary || '-'}</Typography.Paragraph>
            </Card>

            <Card title="人工校正">
              <Form
                form={form}
                layout="vertical"
                onFinish={async (values) => {
                  const payload = {
                    editor: 'admin',
                    basic_info: values.basic_info,
                    portrait: {
                      ...detail.portrait,
                      ...values.portrait,
                      capability_tags: (values.portrait?.capability_tags || '')
                        .split(/[，,]/)
                        .map((item: string) => item.trim())
                        .filter(Boolean),
                      behavior_tags: (values.portrait?.behavior_tags || '')
                        .split(/[，,]/)
                        .map((item: string) => item.trim())
                        .filter(Boolean),
                      job_direction_tags: (values.portrait?.job_direction_tags || '')
                        .split(/[，,]/)
                        .map((item: string) => item.trim())
                        .filter(Boolean),
                      research_direction_tags: (values.portrait?.research_direction_tags || '')
                        .split(/[，,]/)
                        .map((item: string) => item.trim())
                        .filter(Boolean),
                      method_tags: (values.portrait?.method_tags || '')
                        .split(/[，,]/)
                        .map((item: string) => item.trim())
                        .filter(Boolean),
                      academic_potential_tags: (values.portrait?.academic_potential_tags || '')
                        .split(/[，,]/)
                        .map((item: string) => item.trim())
                        .filter(Boolean),
                      strengths: detail.portrait?.strengths || [],
                      risks_or_gaps: detail.portrait?.risks_or_gaps || []
                    },
                    educations: detail.educations,
                    internships: detail.internships,
                    projects: detail.projects,
                    awards: detail.awards,
                    papers: detail.papers,
                    patents: detail.patents,
                    competitions: detail.competitions,
                    skills: detail.skills
                  };
                  const result = await saveReview(resumeId, payload);
                  setDetail(result);
                  message.success('人工校正已保存');
                }}
              >
                <Form.Item label="姓名" name={['basic_info', 'name']}>
                  <Input />
                </Form.Item>
                <Form.Item label="学历" name={['basic_info', 'highest_degree']}>
                  <Input />
                </Form.Item>
                <Form.Item label="毕业时间" name={['basic_info', 'graduation_date']}>
                  <Input />
                </Form.Item>
                <Form.Item label="研究兴趣" name={['basic_info', 'research_interest']}>
                  <Input />
                </Form.Item>
                <Form.Item label="目标研究方向" name={['basic_info', 'target_research_direction']}>
                  <Input />
                </Form.Item>
                <Form.Item label="学生类型" name={['portrait', 'student_type']}>
                  <Input />
                </Form.Item>
                <Form.Item label="研究方向标签" name={['portrait', 'research_direction_tags']}>
                  <Input />
                </Form.Item>
                <Form.Item label="方法能力标签" name={['portrait', 'method_tags']}>
                  <Input />
                </Form.Item>
                <Form.Item label="学术潜力标签" name={['portrait', 'academic_potential_tags']}>
                  <Input />
                </Form.Item>
                <Form.Item label="能力标签" name={['portrait', 'capability_tags']}>
                  <Input />
                </Form.Item>
                <Form.Item label="行为标签" name={['portrait', 'behavior_tags']}>
                  <Input />
                </Form.Item>
                <Form.Item label="岗位方向标签" name={['portrait', 'job_direction_tags']}>
                  <Input />
                </Form.Item>
                <Form.Item label="画像摘要" name={['portrait', 'portrait_summary']}>
                  <TextArea rows={6} />
                </Form.Item>
                <Button type="primary" htmlType="submit">
                  保存人工校正
                </Button>
              </Form>
            </Card>
          </Space>
        </Col>
      </Row>
    </Space>
  );
}
