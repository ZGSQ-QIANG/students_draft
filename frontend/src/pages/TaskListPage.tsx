import { Button, Card, Space, Table, Tag, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchResumes, reprocessResume } from '../api/resumes';
import type { ResumeListItem } from '../types';

export function TaskListPage() {
  const [data, setData] = useState<ResumeListItem[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setData(await fetchResumes());
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
            任务列表
          </Typography.Title>
          <Typography.Text type="secondary">查看上传记录、当前状态、错误原因和重跑入口。</Typography.Text>
        </div>
        <Button onClick={() => void load()}>刷新</Button>
      </Space>
      <Table
        rowKey="id"
        loading={loading}
        dataSource={data}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 80 },
          { title: '文件名', dataIndex: 'source_file_name' },
          { title: '批次号', dataIndex: 'batch_id', width: 140 },
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

