import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Table,
  Tag,
  Button,
  Space,
  Spin,
  message,
  Modal,
  Popconfirm,
  Breadcrumb,
  Descriptions,
  Empty,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  FileTextOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { datasetsApi } from '../../api/datasets';
import { documentsApi } from '../../api/documents';
import type { Dataset, Document } from '../../types';
import FileUploader from '../../components/FileUploader';

const { Title, Text } = Typography;

const statusConfig: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '待处理' },
  parsing: { color: 'processing', text: '解析中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
};

const statusColorMap: Record<string, string> = {
  pending: 'default',
  parsing: 'processing',
  completed: 'success',
  failed: 'error',
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const DatasetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadVisible, setUploadVisible] = useState(false);

  const loadData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [ds, docs] = await Promise.all([
        datasetsApi.get(id),
        documentsApi.list(id),
      ]);
      setDataset(ds);
      setDocuments(docs);
    } catch (err: any) {
      message.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleDeleteDoc = async (docId: string) => {
    try {
      await documentsApi.delete(docId);
      message.success('文档已删除');
      loadData();
    } catch (err: any) {
      message.error(err.message);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!dataset) {
    return <Empty description="数据集不存在" />;
  }

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (name: string) => (
        <Space>
          <FileTextOutlined />
          <Text>{name}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'fileType',
      key: 'fileType',
      width: 100,
      render: (type: string) => <Tag>{type?.toUpperCase()}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'fileSize',
      key: 'fileSize',
      width: 120,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const config = statusConfig[status] || { color: 'default', text: status };
        return <Tag color={statusColorMap[status]}>{config.text}</Tag>;
      },
    },
    {
      title: '切片数',
      dataIndex: 'chunkCount',
      key: 'chunkCount',
      width: 100,
    },
    {
      title: '上传时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 180,
      render: (t: string) => new Date(t).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_: any, record: Document) => (
        <Popconfirm
          title="确定删除此文档？"
          onConfirm={() => handleDeleteDoc(record.id)}
        >
          <Button type="link" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Breadcrumb
        items={[
          { title: <a onClick={() => navigate('/datasets')}>数据集</a> },
          { title: dataset.name },
        ]}
        style={{ marginBottom: 16 }}
      />

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: 24,
        }}
      >
        <div>
          <Title level={4} style={{ margin: 0 }}>
            {dataset.name}
          </Title>
          <Text type="secondary">{dataset.description || '暂无描述'}</Text>
        </div>
        <Space>
          <Button icon={<UploadOutlined />} type="primary" onClick={() => setUploadVisible(true)}>
            上传文档
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadData}>
            刷新
          </Button>
        </Space>
      </div>

      <Descriptions
        size="small"
        column={3}
        style={{ marginBottom: 24 }}
        bordered
      >
        <Descriptions.Item label="文档数">{dataset.documentCount}</Descriptions.Item>
        <Descriptions.Item label="切片数">{dataset.chunkCount}</Descriptions.Item>
        <Descriptions.Item label="创建时间">
          {new Date(dataset.createdAt).toLocaleString('zh-CN')}
        </Descriptions.Item>
      </Descriptions>

      <Title level={5}>文档列表</Title>
      <Table
        dataSource={documents}
        columns={columns}
        rowKey="id"
        pagination={{ pageSize: 10, showSizeChanger: true }}
        size="middle"
      />

      <Modal
        title="上传文档"
        open={uploadVisible}
        onCancel={() => setUploadVisible(false)}
        footer={null}
        width={520}
        destroyOnClose
      >
        {id && (
          <FileUploader
            datasetId={id}
            onSuccess={() => {
              setUploadVisible(false);
              loadData();
            }}
          />
        )}
      </Modal>
    </div>
  );
};

export default DatasetDetail;
