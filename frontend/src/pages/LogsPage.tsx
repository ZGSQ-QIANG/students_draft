import { Card, Table, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { fetchResumeLogs, fetchResumes } from '../api/resumes';
import type { ExtractLog } from '../types';

export function LogsPage() {
  const [logs, setLogs] = useState<ExtractLog[]>([]);

  useEffect(() => {
    const load = async () => {
      const resumes = await fetchResumes();
      if (!resumes.length) {
        setLogs([]);
        return;
      }
      setLogs(await fetchResumeLogs(resumes[0].id));
    };
    void load();
  }, []);

  return (
    <Card>
      <Typography.Title level={4}>日志页</Typography.Title>
      <Typography.Paragraph type="secondary">
        当前默认展示最新一份简历的处理日志，用于查看解析、规则抽取、LLM 抽取和失败原因。
      </Typography.Paragraph>
      <Table
        rowKey="id"
        dataSource={logs}
        columns={[
          { title: '阶段', dataIndex: 'stage_name', width: 160 },
          { title: '模型', dataIndex: 'model_name', width: 160 },
          { title: '状态', dataIndex: 'status', width: 120 },
          { title: '错误', dataIndex: 'error_message' },
          { title: '输出', dataIndex: 'output_text', render: (value: string) => <Typography.Paragraph ellipsis={{ rows: 2 }}>{value}</Typography.Paragraph> }
        ]}
      />
    </Card>
  );
}

