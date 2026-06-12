import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Button,
  Modal,
  Form,
  Input,
  Typography,
  Spin,
  Empty,
  message,
  Popconfirm,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  DeleteOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { datasetsApi } from '../../api/datasets';
import type { Dataset, CreateDatasetRequest } from '../../types';

const { Title, Paragraph } = Typography;

const DatasetsPage: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm<CreateDatasetRequest>();
  const navigate = useNavigate();

  const loadDatasets = async () => {
    setLoading(true);
    try {
      const data = await datasetsApi.list();
      setDatasets(data);
    } catch (err: any) {
      message.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  const handleCreate = async (values: CreateDatasetRequest) => {
    setSubmitting(true);
    try {
      await datasetsApi.create(values);
      message.success('数据集创建成功');
      setModalOpen(false);
      form.resetFields();
      loadDatasets();
    } catch (err: any) {
      message.error(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await datasetsApi.delete(id);
      message.success('数据集已删除');
      loadDatasets();
    } catch (err: any) {
      message.error(err.message);
    }
  };

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <Title level={4} style={{ margin: 0 }}>
          数据集
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          创建数据集
        </Button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" />
        </div>
      ) : datasets.length === 0 ? (
        <Empty description="暂无数据集，点击上方按钮创建" />
      ) : (
        <Row gutter={[16, 16]}>
          {datasets.map((ds) => (
            <Col key={ds.id} xs={24} sm={12} lg={8} xl={6}>
              <Card
                hoverable
                actions={[
                  <EyeOutlined
                    key="view"
                    onClick={() => navigate(`/datasets/${ds.id}`)}
                  />,
                  <Popconfirm
                    key="delete"
                    title="确定删除此数据集？"
                    description="删除后无法恢复，包含的所有文档也会被删除。"
                    onConfirm={() => handleDelete(ds.id)}
                  >
                    <DeleteOutlined />
                  </Popconfirm>,
                ]}
              >
                <Card.Meta
                  avatar={
                    <DatabaseOutlined
                      style={{ fontSize: 28, color: '#1677ff' }}
                    />
                  }
                  title={ds.name}
                  description={
                    <Paragraph
                      ellipsis={{ rows: 2 }}
                      type="secondary"
                      style={{ marginBottom: 12, minHeight: 40 }}
                    >
                      {ds.description || '暂无描述'}
                    </Paragraph>
                  }
                />
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-around',
                    marginTop: 12,
                    paddingTop: 12,
                    borderTop: '1px solid #f0f0f0',
                  }}
                >
                  <Statistic
                    title="文档数"
                    value={ds.documentCount}
                    prefix={<FileTextOutlined />}
                    valueStyle={{ fontSize: 18 }}
                  />
                  <Statistic
                    title="切片数"
                    value={ds.chunkCount}
                    valueStyle={{ fontSize: 18 }}
                  />
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <Modal
        title="创建数据集"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          preserve={false}
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入数据集名称' }]}
          >
            <Input placeholder="数据集名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="数据集描述（可选）" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={submitting}>
              创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DatasetsPage;
