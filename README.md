# 学生简历画像系统 v1

这是一个从零实现的学生简历解析与画像后台系统，包含：

- `backend/`：`FastAPI + SQLAlchemy` 后端，负责上传、解析、规则抽取、LLM 补充抽取、画像生成、人工校正和日志
- `frontend/`：`React + Vite + Ant Design` 管理后台，负责登录、上传、任务列表、简历详情、人工校正和日志查看

## 当前能力

- 支持 `PDF / DOCX / 图片` 文件上传
- 支持单份和批量导入
- 支持简历文本解析、模块切分、规则抽取
- 提供可替换的 LLM Provider 抽象，默认使用真实 OpenAI 兼容接口完成补充抽取
- 自动生成学生类型、能力标签、行为标签、岗位方向标签和画像摘要
- 支持人工校正后生成新版本
- 记录处理日志并生成向量索引占位数据

## 目录结构

```text
backend/
  app/
    api/          # 路由
    core/         # 配置和安全
    db/           # 数据库初始化
    models/       # SQLAlchemy 模型
    schemas/      # Pydantic schema
    services/     # 解析、抽取、画像、审计、向量化
    workers/      # Celery 任务入口
  tests/
frontend/
  src/
    api/          # 请求封装
    components/
    layouts/
    pages/
    types/
```

## 本地启动

### 1. 启动后端

```bash
cd /Users/zgsq/students_draft/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
uvicorn app.main:app --reload
```

默认管理员账号：

- 用户名：`admin`
- 密码：`admin123`

### 2. 启动前端

```bash
cd /Users/zgsq/students_draft/frontend
npm install
cp .env.example .env
npm run dev
```

## API 概览

- `POST /api/auth/login`
- `POST /api/resumes/upload`
- `GET /api/resumes`
- `GET /api/resumes/{resume_id}`
- `POST /api/resumes/{resume_id}/reprocess`
- `PUT /api/resumes/{resume_id}/review`
- `GET /api/resumes/{resume_id}/logs`
- `GET /api/dictionaries`

## 验证

已完成：

- `python3 -m compileall backend/app`

如安装依赖后，可继续执行：

```bash
cd /Users/zgsq/students_draft/backend
pytest
```

## 已知说明

- 当前 LLM Provider 默认是 `openai`，请在 `.env` 中配置 `LLM_API_KEY/LLM_BASE_URL/LLM_MODEL`
- 当前向量索引使用哈希向量占位，方便先完成数据流；接入真实 embedding 模型时只需替换 `app/services/vectorize.py`
- Celery 任务入口已预留，未安装 Celery 时默认通过 FastAPI `BackgroundTasks` 同步触发处理
