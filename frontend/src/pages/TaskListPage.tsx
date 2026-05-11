import { Button, Card, Form, Input, Space, Table, Tag, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchResumes, reprocessResume, type ResumeSearchParams } from '../api/resumes';
import type { ResumeListItem } from '../types';

export function TaskListPage() {
  const [data, setData] = useState<ResumeListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm<ResumeSearchParams>();

  const load = async (params?: ResumeSearchParams) => {
    setLoading(true);
    try {
      const searchValues = params ?? form.getFieldsValue();
      setData(await fetchResumes(searchValues));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  return (
    <Card>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <Typography.Title level={4} style={{ marginBottom: 0 }}>
            学生搜索
          </Typography.Title>
          <Typography.Text type="secondary">按姓名、学校、专业和画像标签筛选学生，并继续查看处理状态。</Typography.Text>
        </div>
        <Button onClick={() => void load()}>刷新</Button>
      </Space>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="inline"
          onFinish={(values) => void load(values)}
        >
          <Form.Item name="name" label="姓名">
            <Input placeholder="学生姓名" allowClear />
          </Form.Item>
          <Form.Item name="school_name" label="学校">
            <Input placeholder="学校名称" allowClear />
          </Form.Item>
          <Form.Item name="major" label="专业">
            <Input placeholder="专业名称" allowClear />
          </Form.Item>
          <Form.Item name="student_type" label="画像类型">
            <Input placeholder="如学术型/实践型" allowClear />
          </Form.Item>
          <Form.Item name="keyword" label="关键词">
            <Input placeholder="姓名/学校/专业/画像摘要" allowClear />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                搜索
              </Button>
              <Button
                onClick={() => {
                  form.resetFields();
                  void load({});
                }}
              >
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
      <Table
        rowKey="id"
        loading={loading}
        dataSource={data}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 80 },
          { title: '姓名', dataIndex: 'student_name', width: 120, render: (value?: string) => value || '-' },
          { title: '学校', dataIndex: 'school_name', width: 180, render: (value?: string) => value || '-' },
          { title: '专业', dataIndex: 'major', width: 160, render: (value?: string) => value || '-' },
          { title: '画像类型', dataIndex: 'student_type', width: 120, render: (value?: string) => value || '-' },
          { title: '文件名', dataIndex: 'source_file_name' },
          { title: '批次号', dataIndex: 'batch_id', width: 140 },
          { title: '整体状态', dataIndex: 'analysis_status', render: (value: string) => <Tag color="gold">{value}</Tag> },
          { title: '解析状态', dataIndex: 'parse_status', render: (value: string) => <Tag>{value}</Tag> },
          { title: '抽取状态', dataIndex: 'extract_status', render: (value: string) => <Tag color="blue">{value}</Tag> },
          { title: '版本', dataIndex: 'current_version', width: 80 },
          {
            title: '异常',
            render: (_, record) => (record.last_error_message ? <Typography.Text type="danger">{record.last_error_message}</Typography.Text> : '-')
          },
          {
            title: '操作',
            render: (_, record) => (
              <Space>
                <Link to={`/resumes/${record.id}`}>查看详情</Link>
                <Button type="link" onClick={() => void reprocessResume(record.id)}>
                  重跑
                </Button>
              </Space>
            )
          }
        ]}
      />
    </Card>
  );
}
