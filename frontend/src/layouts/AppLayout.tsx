import { FileSearchOutlined, FileTextOutlined, LogoutOutlined, UploadOutlined } from '@ant-design/icons';
import { Button, Layout, Menu, Typography } from 'antd';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { logout } from '../api/auth';

const { Header, Sider, Content } = Layout;

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: 24 }}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            学生简历画像系统
          </Typography.Title>
          <Typography.Text type="secondary">内部管理后台</Typography.Text>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={[
            { key: '/upload', icon: <UploadOutlined />, label: <Link to="/upload">上传中心</Link> },
            { key: '/tasks', icon: <FileSearchOutlined />, label: <Link to="/tasks">任务列表</Link> },
            { key: '/logs', icon: <FileTextOutlined />, label: <Link to="/logs">日志说明</Link> }
          ]}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <Typography.Text>上传、解析、画像、校正一体化工作台</Typography.Text>
          <Button
            icon={<LogoutOutlined />}
            onClick={() => {
              logout();
              navigate('/login');
            }}
          >
            退出登录
          </Button>
        </Header>
        <Content style={{ padding: 24, background: '#f7f8fa' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

