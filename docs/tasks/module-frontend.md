# F01：前端开发模块

**阶段**: Phase 8 | **优先级**: P0 | **状态**: 🔲 未开始

**依赖模块**: M22 API Routes（需要后端接口就绪）

---

## 任务清单

### 1. 项目初始化

- [ ] 创建 `frontend/` 目录
- [ ] 使用 `npm create vite@latest . -- --template react-ts` 初始化
- [ ] 安装依赖：
  - [ ] `antd` — UI 组件库
  - [ ] `@ant-design/icons` — 图标
  - [ ] `axios` — HTTP 客户端
  - [ ] `react-router-dom` — 路由
  - [ ] `dayjs` — 日期处理
  - [ ] `zustand` — 状态管理（可选）
- [ ] 配置文件：`vite.config.ts`（配置代理到后端 8000 端口）

### 2. 基础设施

- [ ] 创建 `src/api/client.ts` — Axios 实例（baseURL、拦截器自动带 Token）
- [ ] 创建 `src/api/auth.ts` — 认证 API
- [ ] 创建 `src/api/datasets.ts` — 数据集 API
- [ ] 创建 `src/api/documents.ts` — 文档 API
- [ ] 创建 `src/api/conversations.ts` — 对话 API
- [ ] 创建 `src/types/index.ts` — TypeScript 类型定义
- [ ] 创建 `src/store/authStore.ts` — 认证状态管理
- [ ] 创建 `src/components/Layout/` — 布局组件
  - [ ] MainLayout（侧边栏 + 头部 + 内容区）
  - [ ] AuthLayout（居中卡片布局）
- [ ] 创建 `src/components/Sidebar/` — 侧边栏组件

### 3. 页面 - 认证

- [ ] 登录页：`src/pages/Login/index.tsx`
  - [ ] 用户名/密码输入
  - [ ] 登录按钮
  - [ ] 跳转注册
  - [ ] 调用 auth API
- [ ] 注册页：`src/pages/Register/index.tsx`
  - [ ] 用户名/邮箱/密码输入
  - [ ] 注册成功后跳转登录
- [ ] 实现路由守卫（未登录跳转登录页）

### 4. 页面 - 数据集管理

- [ ] 数据集列表页：`src/pages/Datasets/index.tsx`
  - [ ] 卡片/列表展示数据集
  - [ ] 创建数据集的 Dialog
  - [ ] 删除确认
- [ ] 数据集详情页：`src/pages/Datasets/Detail.tsx`
  - [ ] 展示数据集信息
  - [ ] 文档列表表格

### 5. 页面 - 文档管理

- [ ] 文档上传组件：`src/components/FileUploader/index.tsx`
  - [ ] 拖拽上传区域
  - [ ] 文件类型校验
  - [ ] 上传进度显示
  - [ ] 上传后自动刷新列表
- [ ] 文档列表表格：显示文件名、类型、大小、状态（带图标）、上传时间、操作按钮
- [ ] 文档状态 Tag：pending→灰色、parsing→蓝色、completed→绿色、failed→红色
- [ ] 文档删除确认

### 6. 页面 - 对话

- [ ] 对话列表（侧边栏）：显示历史对话列表、创建新对话按钮
- [ ] 对话页：`src/pages/Chat/index.tsx`
  - [ ] 消息列表（用户消息右对齐、助理消息左对齐）
  - [ ] 消息输入框（支持 Enter 发送）
  - [ ] 知识库选择器（选择数据集或不选）
  - [ ] SSE 流式展示（打字机效果）
  - [ ] 来源引用展示（可折叠的面板或卡片）
  - [ ] 对话标题显示
- [ ] SSE 解析工具函数：`src/utils/sse.ts`

### 7. 页面 - 个人设置

- [ ] `src/pages/Settings/index.tsx`
  - [ ] 修改密码表单

### 8. 页面 - 管理后台

- [ ] `src/pages/Admin/index.tsx`
  - [ ] 用户列表表格
  - [ ] 系统统计卡片

### 9. 路由配置

- [ ] `src/App.tsx` — 路由配置
  - [ ] `/login`、`/register` → AuthLayout
  - [ ] `/datasets` → MainLayout（默认页）
  - [ ] `/datasets/:id` → MainLayout
  - [ ] `/conversations` → MainLayout
  - [ ] `/conversations/:id` → MainLayout
  - [ ] `/admin` → MainLayout（需 admin 角色）
  - [ ] `/settings` → MainLayout

### 10. 验证

- [ ] `npm run dev` 可正常启动
- [ ] 登录→跳转首页
- [ ] 上传文档→显示进度→状态变更
- [ ] 对话→流式展示
- [ ] 代理后端 API 正常

---

## 验收标准

- [ ] 完整聊天 UI（含来源引用）
- [ ] 文档管理界面（上传/列表/状态/删除）
- [ ] 数据集管理（创建/切换）
- [ ] 登录/注册流程
- [ ] SSE 流式打字机效果
- [ ] 路由守卫（未登录拦截）
