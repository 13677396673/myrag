import React, { useEffect, useState } from 'react';
import { Typography, Table, Card, Row, Col, Statistic, Spin, message, Tag } from 'antd';
import {
  UserOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  MessageOutlined,
  // TeamOutlined removed — used conceptually
} from '@ant-design/icons';
import { adminApi } from '../../api/admin';
import type { User, AdminStats } from '../../types';

const { Title } = Typography;

const AdminPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [userList, statsData] = await Promise.all([
          adminApi.getUsers(),
          adminApi.getStats(),
        ]);
        setUsers(userList);
        setStats(statsData);
      } catch (err: any) {
        message.error(err.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }

  const userColumns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'red' : 'blue'}>
          {role === 'admin' ? '管理员' : '用户'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'isActive',
      key: 'isActive',
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'default'}>
          {active ? '活跃' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '注册时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (t: string) => new Date(t).toLocaleString('zh-CN'),
    },
  ];

  const statsCards = [
    { title: '用户数', value: stats?.totalUsers || 0, icon: <UserOutlined />, color: '#1677ff' },
    { title: '数据集', value: stats?.totalDatasets || 0, icon: <DatabaseOutlined />, color: '#52c41a' },
    { title: '文档数', value: stats?.totalDocuments || 0, icon: <FileTextOutlined />, color: '#faad14' },
    { title: '对话数', value: stats?.totalConversations || 0, icon: <MessageOutlined />, color: '#722ed1' },
  ];

  return (
    <div>
      <Title level={4}>管理后台</Title>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {statsCards.map((card) => (
          <Col key={card.title} xs={12} sm={6}>
            <Card hoverable>
              <Statistic
                title={card.title}
                value={card.value}
                prefix={React.cloneElement(card.icon, { style: { color: card.color } })}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 用户列表 */}
      <Card title="用户列表">
        <Table
          dataSource={users}
          columns={userColumns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="middle"
        />
      </Card>
    </div>
  );
};

export default AdminPage;
