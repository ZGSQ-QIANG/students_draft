import { InboxOutlined } from '@ant-design/icons';
import { Button, Card, Space, Typography, Upload, message } from 'antd';
import { useState } from 'react';
import { uploadResumes } from '../api/resumes';

export function UploadPage() {
  const [fileList, setFileList] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);

  return (
    <Space direction="vertical" size={24} style={{ width: '100%' }}>
      <Card>
        <Typography.Title level={4}>上传中心</Typography.Title>
        <Typography.Paragraph type="secondary">
          支持 PDF、DOCX、图片格式。上传后系统会自动完成解析、规则抽取、LLM 补充抽取和画像生成。
        </Typography.Paragraph>
        <Upload.Dragger
          multiple
          beforeUpload={(file) => {
            setFileList((current) => [...current, file as File]);
            return false;
          }}
          fileList={fileList as never[]}
          onRemove={(file) => {
            setFileList((current) => current.filter((item) => item.name !== file.name));
          }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">拖拽文件到这里，或者点击选择文件</p>
          <p className="ant-upload-hint">建议一次上传一批同类型简历，便于对比查看抽取质量。</p>
        </Upload.Dragger>
        <Button
          style={{ marginTop: 16 }}
          type="primary"
          loading={loading}
          disabled={!fileList.length}
          onClick={async () => {
            setLoading(true);
            try {
              const result = await uploadResumes(fileList);
              message.success(`批次 ${result.batch_id} 已创建，${result.items.length} 份简历进入处理流程`);
              setFileList([]);
            } finally {
              setLoading(false);
            }
          }}
        >
          开始处理
        </Button>
      </Card>
    </Space>
  );
}

