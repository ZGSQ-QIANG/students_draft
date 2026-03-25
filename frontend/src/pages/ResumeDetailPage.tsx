import { Button, Card, Col, Divider, Form, Input, Row, Space, Tag, Typography, message } from 'antd';
import TextArea from 'antd/es/input/TextArea';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchResumeDetail, saveReview } from '../api/resumes';
import type { ResumeDetail } from '../types';

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
          job_direction_tags: (result.portrait?.job_direction_tags || []).join('，')
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

  return (
    <Space direction="vertical" size={24} style={{ width: '100%' }}>
      <Card>
        <Space direction="vertical" size={4}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            {detail.source_file_name}
          </Typography.Title>
          <Space>
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
              {detail.sections.map((section) => (
                <Card key={section.id} size="small" style={{ background: '#fafafa' }}>
                  <Typography.Text strong>{section.section_type}</Typography.Text>
                  <Divider style={{ margin: '12px 0' }} />
                  <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                    {section.raw_content}
                  </Typography.Paragraph>
                </Card>
              ))}
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
              <Typography.Paragraph>教育经历数：{detail.educations.length}</Typography.Paragraph>
              <Typography.Paragraph>实习经历数：{detail.internships.length}</Typography.Paragraph>
              <Typography.Paragraph>项目经历数：{detail.projects.length}</Typography.Paragraph>
            </Card>

            <Card title="画像结果">
              <Typography.Paragraph>学生类型：{detail.portrait?.student_type || '-'}</Typography.Paragraph>
              <Typography.Paragraph>
                能力标签：
                {(detail.portrait?.capability_tags || []).map((item) => (
                  <Tag key={item}>{item}</Tag>
                ))}
              </Typography.Paragraph>
              <Typography.Paragraph>
                行为标签：
                {(detail.portrait?.behavior_tags || []).map((item) => (
                  <Tag color="green" key={item}>
                    {item}
                  </Tag>
                ))}
              </Typography.Paragraph>
              <Typography.Paragraph>
                岗位方向：
                {(detail.portrait?.job_direction_tags || []).map((item) => (
                  <Tag color="purple" key={item}>
                    {item}
                  </Tag>
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
                      strengths: detail.portrait?.strengths || [],
                      risks_or_gaps: detail.portrait?.risks_or_gaps || []
                    },
                    educations: detail.educations,
                    internships: detail.internships,
                    projects: detail.projects,
                    awards: detail.awards,
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
                <Form.Item label="学生类型" name={['portrait', 'student_type']}>
                  <Input />
                </Form.Item>
                <Form.Item
                  label="能力标签"
                  name={['portrait', 'capability_tags']}
                >
                  <Input />
                </Form.Item>
                <Form.Item
                  label="行为标签"
                  name={['portrait', 'behavior_tags']}
                >
                  <Input />
                </Form.Item>
                <Form.Item
                  label="岗位方向标签"
                  name={['portrait', 'job_direction_tags']}
                >
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
