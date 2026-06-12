import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Input,
  Button,
  Typography,
  Space,
  Spin,
  message,
  Select,
  Collapse,
  List,
  Tag,
  Empty,
  Divider,
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { conversationsApi } from '../../api/conversations';
import { datasetsApi } from '../../api/datasets';
import { parseSSEStream } from '../../utils/sse';
import type { Message, Dataset, SourceReference } from '../../types';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const ChatPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [datasetList, setDatasetList] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | undefined>(undefined);
  const [convTitle, setConvTitle] = useState('对话');
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamContentRef = useRef('');

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 50);
  }, []);

  // 加载数据集列表（用于选择器）
  useEffect(() => {
    datasetsApi.list().then(setDatasetList).catch(() => {});
  }, []);

  // 加载历史消息
  useEffect(() => {
    if (!id) {
      setMessages([]);
      setConvTitle('新对话');
      return;
    }

    const loadMessages = async () => {
      setLoading(true);
      try {
        const [conv, msgs] = await Promise.all([
          conversationsApi.get(id),
          conversationsApi.getMessages(id),
        ]);
        setConvTitle(conv.title);
        setMessages(msgs);
        setSelectedDatasetId(conv.datasetId);
      } catch (err: any) {
        message.error(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadMessages();
  }, [id]);

  // 消息更新后滚动
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 发送消息
  const handleSend = async () => {
    const content = inputValue.trim();
    if (!content || streaming) return;

    // 如果没有对话 ID，先创建
    let convId = id;
    if (!convId) {
      try {
        const conv = await conversationsApi.create({
          title: content.slice(0, 50),
          datasetId: selectedDatasetId,
        });
        setConvTitle(conv.title);
        navigate(`/conversations/${conv.id}`, { replace: true });
        convId = conv.id;
      } catch (err: any) {
        message.error('创建对话失败: ' + err.message);
        return;
      }
    }

    // 添加用户消息到界面
    const userMsg: Message = {
      id: 'temp-' + Date.now(),
      conversationId: convId,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setStreaming(true);
    streamContentRef.current = '';

    // 添加占位助手消息
    const assistantMsg: Message = {
      id: 'temp-assistant',
      conversationId: convId,
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    const controller = new AbortController();
    setAbortController(controller);

    try {
      const response = await conversationsApi.sendMessage(convId, {
        content,
        datasetId: selectedDatasetId,
        stream: true,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `请求失败 (${response.status})`);
      }

      await parseSSEStream(response, {
        onChunk: (chunk) => {
          streamContentRef.current += chunk;
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last && last.role === 'assistant') {
              copy[copy.length - 1] = { ...last, content: streamContentRef.current };
            }
            return copy;
          });
        },
        onSources: (sources) => {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last && last.role === 'assistant') {
              copy[copy.length - 1] = { ...last, sources };
            }
            return copy;
          });
        },
        onError: (errMsg) => {
          message.error(errMsg);
        },
        onDone: () => {
          // 流结束——刷新完整消息列表以获取正确 ID
          if (convId) {
            conversationsApi.getMessages(convId).then((msgs) => {
              setMessages(msgs);
            }).catch(() => {});
          }
        },
      });
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        message.error(err.message);
        // 移除占位消息
        setMessages((prev) => prev.filter((m) => m.id !== 'temp-assistant'));
      }
    } finally {
      setStreaming(false);
      setAbortController(null);
    }
  };

  const handleStop = () => {
    abortController?.abort();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)' }}>
      {/* 顶部：标题 + 知识库选择 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Title level={4} style={{ margin: 0 }} ellipsis>
          {convTitle}
        </Title>
        <Space>
          <Select
            placeholder="选择知识库（可选）"
            allowClear
            style={{ width: 200 }}
            value={selectedDatasetId}
            onChange={setSelectedDatasetId}
            options={datasetList.map((ds) => ({
              value: ds.id,
              label: ds.name,
            }))}
          />
        </Space>
      </div>

      <Divider style={{ margin: '0 0 16px' }} />

      {/* 消息列表 */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0 16px',
          marginBottom: 16,
        }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
          </div>
        ) : messages.length === 0 ? (
          <Empty
            description="开始你的第一次对话吧！"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: 16,
              }}
            >
              <div
                style={{
                  maxWidth: '75%',
                  minWidth: 60,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 4,
                    flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                  }}
                >
                  {msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {msg.role === 'user' ? '你' : 'AI 助手'}
                  </Text>
                </div>

                <div
                  style={{
                    padding: '12px 16px',
                    borderRadius: 12,
                    backgroundColor:
                      msg.role === 'user' ? '#1677ff' : '#f5f5f5',
                    color: msg.role === 'user' ? '#fff' : undefined,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {msg.content || (msg.id === 'temp-assistant' ? <Spin size="small" /> : null)}
                </div>

                {/* 来源引用 */}
                {msg.sources && msg.sources.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <Collapse
                      ghost
                      size="small"
                      items={[
                        {
                          key: 'sources',
                          label: (
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              来源引用 ({msg.sources.length} 条)
                            </Text>
                          ),
                          children: (
                            <List
                              size="small"
                              dataSource={msg.sources}
                              renderItem={(src: SourceReference) => (
                                <List.Item>
                                  <div>
                                    <Text strong style={{ fontSize: 12 }}>
                                      {src.documentName}
                                    </Text>
                                    <Tag style={{ marginLeft: 8 }} color="blue">
                                      {(src.score * 100).toFixed(0)}%
                                    </Tag>
                                    <Paragraph
                                      ellipsis={{ rows: 2 }}
                                      type="secondary"
                                      style={{ fontSize: 12, margin: '4px 0 0' }}
                                    >
                                      {src.content}
                                    </Paragraph>
                                  </div>
                                </List.Item>
                              )}
                            />
                          ),
                        },
                      ]}
                    />
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区 */}
      <div
        style={{
          borderTop: '1px solid #f0f0f0',
          paddingTop: 12,
        }}
      >
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息，Enter 发送，Shift+Enter 换行"
            rows={2}
            disabled={streaming}
            style={{ resize: 'none' }}
          />
          {streaming ? (
            <Button danger onClick={handleStop}>
              停止
            </Button>
          ) : (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!inputValue.trim()}
            >
              发送
            </Button>
          )}
        </Space.Compact>
      </div>
    </div>
  );
};

export default ChatPage;
