import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, List, Typography, Spin, message } from 'antd';
import { PlusOutlined, MessageOutlined, DeleteOutlined } from '@ant-design/icons';
import { conversationsApi } from '../../api/conversations';
import type { Conversation } from '../../types';
const { Text } = Typography;

const AppSidebar: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const loadConversations = async () => {
    setLoading(true);
    try {
      const list = await conversationsApi.list();
      setConversations(list);
    } catch (err: any) {
      message.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  const handleCreate = async () => {
    try {
      const conv = await conversationsApi.create({ title: '新对话' });
      setConversations((prev) => [conv, ...prev]);
      navigate(`/conversations/${conv.id}`);
    } catch (err: any) {
      message.error(err.message);
    }
  };

  const handleDelete = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    try {
      await conversationsApi.delete(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (id === convId) {
        navigate('/conversations');
      }
    } catch (err: any) {
      message.error(err.message);
    }
  };

  return (
    <div style={{ padding: '0 8px' }}>
      <Button
        type="primary"
        block
        icon={<PlusOutlined />}
        onClick={handleCreate}
        style={{ marginBottom: 12 }}
      >
        新对话
      </Button>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 20 }}>
          <Spin size="small" />
        </div>
      ) : conversations.length === 0 ? (
        <Text type="secondary" style={{ display: 'block', textAlign: 'center', padding: 20 }}>
          暂无对话
        </Text>
      ) : (
        <div style={{ maxHeight: 'calc(100vh - 220px)', overflowY: 'auto' }}>
          <List
            dataSource={conversations}
            renderItem={(conv) => (
              <List.Item
                key={conv.id}
                onClick={() => navigate(`/conversations/${conv.id}`)}
                style={{
                  cursor: 'pointer',
                  padding: '8px 12px',
                  borderRadius: 6,
                  backgroundColor: id === conv.id ? '#e6f4ff' : undefined,
                  marginBottom: 2,
                }}
                actions={[
                  <Button
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => handleDelete(e, conv.id)}
                  />,
                ]}
              >
                <List.Item.Meta
                  avatar={<MessageOutlined />}
                  title={
                    <Text
                      ellipsis
                      style={{ maxWidth: 140, fontSize: 13 }}
                    >
                      {conv.title}
                    </Text>
                  }
                />
              </List.Item>
            )}
          />
        </div>
      )}
    </div>
  );
};

export default AppSidebar;
