import React, { useState } from 'react';
import { Upload, Progress, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { documentsApi } from '../../api/documents';

const { Dragger } = Upload;

interface FileUploaderProps {
  datasetId: string;
  onSuccess: () => void;
}

const ACCEPTED_TYPES = [
  '.txt', '.md', '.pdf', '.doc', '.docx',
  '.csv', '.xlsx', '.xls', '.json', '.xml',
  '.html', '.htm',
];

const FileUploader: React.FC<FileUploaderProps> = ({ datasetId, onSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleUpload = async (file: File) => {
    // 文件类型校验
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      message.error(`不支持的文件类型: ${ext}，支持的类型: ${ACCEPTED_TYPES.join(', ')}`);
      return false;
    }

    // 文件大小校验（100MB）
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      message.error('文件大小不能超过 100MB');
      return false;
    }

    setUploading(true);
    setProgress(0);

    try {
      await documentsApi.upload(datasetId, file, (pct) => {
        setProgress(pct);
      });
      message.success(`"${file.name}" 上传成功！`);
      onSuccess();
    } catch (err: any) {
      message.error(err.message);
    } finally {
      setUploading(false);
      setProgress(0);
    }

    return false; // 阻止默认上传行为
  };

  const uploadProps: UploadProps = {
    beforeUpload: handleUpload as any,
    showUploadList: false,
    multiple: true,
    accept: ACCEPTED_TYPES.join(','),
    disabled: uploading,
  };

  return (
    <div>
      <Dragger {...uploadProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持 {ACCEPTED_TYPES.join(', ')} 格式，单个文件最大 100MB
        </p>
      </Dragger>

      {uploading && (
        <Progress
          percent={progress}
          status="active"
          style={{ marginTop: 16 }}
        />
      )}
    </div>
  );
};

export default FileUploader;
