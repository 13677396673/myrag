# F01：前端开发模块

**阶段**: Phase 8 | **优先级**: P0 | **状态**: ✅ 已完成

**依赖模块**: M22 API Routes（需要后端接口就绪）

---

## 任务清单

### 1. 项目初始化

- [x] 创建 `frontend/` 目录
- [x] 使用 `npm create vite@latest . -- --template react-ts` 初始化
- [x] 安装依赖：
  - [x] `antd` — UI 组件库
  - [x] `@ant-design/icons` — 图标
  - [x] `axios` — HTTP 客户端
  - [x] `react-router-dom` — 路由
  - [x] `dayjs` — 日期处理
  - [x] `zustand` — 状态管理（可选）
- [x] 配置文件：`vite.config.ts`（配置代理到后端 8000 端口）

### 2. 基础设施

- [x] 创建 `src/api/client.ts` — Axios 实例（baseURL、拦截器自动带 Token）
- [x] 创建 `src/api/auth.ts` — 认证 API
- [x] 创建 `src/api/datasets.ts` — 数据集 API
- [x] 创建 `src/api/documents.ts` — 文档 API
- [x] 创建 `src/api/conversations.ts` — 对话 API
- [x] 创建 `src/types/index.ts` — TypeScript 类型定义
- [x] 创建 `src/store/authStore.ts` — 认证状态管理
- [x] 创建 `src/components/Layout/` — 布局组件
  - [x] MainLayout（侧边栏 + 头部 + 内容区）
  - [x] AuthLayout（居中卡片布局）
- [x] 创建 `src/components/Sidebar/` — 侧边栏组件

### 3. 页面 - 认证

- [x] 登录页：`src/pages/Login/index.tsx`
  - [x] 用户名/密码输入
  - [x] 登录按钮
  - [x] 跳转注册
  - [x] 调用 auth API
- [x] 注册页：`src/pages/Register/index.tsx`
  - [x] 用户名/邮箱/密码输入
  - [x] 注册成功后跳转登录
- [x] 实现路由守卫（未登录跳转登录页）

### 4. 页面 - 数据集管理

- [x] 数据集列表页：`src/pages/Datasets/index.tsx`
  - [x] 卡片/列表展示数据集
  - [x] 创建数据集的 Dialog
  - [x] 删除确认
- [x] 数据集详情页：`src/pages/Datasets/Detail.tsx`
  - [x] 展示数据集信息
  - [x] 文档列表表格

### 5. 页面 - 文档管理

- [x] 文档上传组件：`src/components/FileUploader/index.tsx`
  - [x] 拖拽上传区域
  - [x] 文件类型校验
  - [x] 上传进度显示
  - [x] 上传后自动刷新列表
- [x] 文档列表表格：显示文件名、类型、大小、状态（带图标）、上传时间、操作按钮
- [x] 文档状态 Tag：pending→灰色、parsing→蓝色、completed→绿色、failed→红色
- [x] 文档删除确认

### 6. 页面 - 对话

- [x] 对话列表（侧边栏）：显示历史对话列表、创建新对话按钮
- [x] 对话页：`src/pages/Chat/index.tsx`
  - [x] 消息列表（用户消息右对齐、助理消息左对齐）
  - [x] 消息输入框（支持 Enter 发送）
  - [x] 知识库选择器（选择数据集或不选）
  - [x] SSE 流式展示（打字机效果）
  - [x] 来源引用展示（可折叠的面板或卡片）
  - [x] 对话标题显示
- [x] SSE 解析工具函数：`src/utils/sse.ts`

### 7. 页面 - 个人设置

- [x] `src/pages/Settings/index.tsx`
  - [x] 修改密码表单

### 8. 页面 - 管理后台

- [x] `src/pages/Admin/index.tsx`
  - [x] 用户列表表格
  - [x] 系统统计卡片

### 9. 路由配置

- [x] `src/App.tsx` — 路由配置
  - [x] `/login`、`/register` → AuthLayout
  - [x] `/datasets` → MainLayout（默认页）
  - [x] `/datasets/:id` → MainLayout
  - [x] `/conversations` → MainLayout
  - [x] `/conversations/:id` → MainLayout
  - [x] `/admin` → MainLayout（需 admin 角色）
  - [x] `/settings` → MainLayout

### 10. 验证

- [x] `npm run dev` 可正常启动
- [x] 登录→跳转首页
- [x] 上传文档→显示进度→状态变更
- [x] 对话→流式展示
- [x] 代理后端 API 正常

---

## 验收标准

- [x] 完整聊天 UI（含来源引用）
- [x] 文档管理界面（上传/列表/状态/删除）
- [x] 数据集管理（创建/切换）
- [x] 登录/注册流程
- [x] SSE 流式打字机效果
- [x] 路由守卫（未登录拦截）
