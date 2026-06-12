import React from 'react';
import { Outlet } from 'react-router-dom';
import { Layout, Card, Typography, theme } from 'antd';

const { Content } = Layout;
const { Title } = Typography;

const AuthLayout: React.FC = () => {
  const { token: themeToken } = theme.useToken();

  return (
    <Layout
      style={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: themeToken.colorBgLayout,
      }}
    >
      <Content
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          width: '100%',
          maxWidth: 420,
          padding: 24,
        }}
      >
        <Title level={2} style={{ marginBottom: 32, textAlign: 'center' }}>
          RAG 智能知识库
        </Title>
        <Card style={{ width: '100%', boxShadow: themeToken.boxShadow }}>
          <Outlet />
        </Card>
      </Content>
    </Layout>
  );
};

export default AuthLayout;
