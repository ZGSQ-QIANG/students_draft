import { SearchOutlined, FileSearchOutlined, FileTextOutlined, LogoutOutlined, UploadOutlined, BarChartOutlined } from '@ant-design/icons';
import { Button, Layout, Menu, Typography } from 'antd';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { logout } from '../api/auth';

const { Header, Sider, Content } = Layout;

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Layout className="app-shell">
      <Sider width={252} theme="light" className="app-sider">
        <div className="app-brand">
          <Typography.Text className="app-brand-kicker">Resume Atlas</Typography.Text>
          <Typography.Title level={4} className="app-brand-title">
            学生简历画像系统
          </Typography.Title>
          <Typography.Text className="app-brand-subtitle">内部管理后台</Typography.Text>
        </div>
        <Menu
          className="app-menu"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={[
            { key: '/upload', icon: <UploadOutlined />, label: <Link to="/upload">上传中心</Link> },
            { key: '/tasks', icon: <FileSearchOutlined />, label: <Link to="/tasks">任务列表</Link> },
            { key: '/semantic-search', icon: <SearchOutlined />, label: <Link to="/semantic-search">语义搜索</Link> },
            { key: '/reports/group', icon: <BarChartOutlined />, label: <Link to="/reports/group">群体分析报告</Link> },
            { key: '/logs', icon: <FileTextOutlined />, label: <Link to="/logs">日志说明</Link> }
          ]}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Typography.Text className="app-header-title">上传、解析、画像、校正一体化工作台</Typography.Text>
          <Button
            className="app-logout"
            icon={<LogoutOutlined />}
            onClick={() => {
              logout();
              navigate('/login');
            }}
          >
            退出登录
          </Button>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
