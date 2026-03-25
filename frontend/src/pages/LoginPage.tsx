import { Button, Card, Form, Input, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';

export function LoginPage() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #f3efe0 0%, #d7e4f2 100%)'
      }}
    >
      <Card title="管理员登录" style={{ width: 420, borderRadius: 16 }}>
        <Typography.Paragraph type="secondary">
          使用内部管理员账号登录后，即可上传简历、查看画像结果并执行人工校正。
        </Typography.Paragraph>
        <Form
          layout="vertical"
          onFinish={async (values) => {
            await login(values.username, values.password);
            navigate('/upload');
          }}
          initialValues={{ username: 'admin', password: 'admin123' }}
        >
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Button block type="primary" htmlType="submit">
            登录
          </Button>
        </Form>
      </Card>
    </div>
  );
}

