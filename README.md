# 学生简历画像与群体分析系统

面向高校学生材料管理场景的 LLM 创新应用系统。系统将学生简历从非结构化 PDF / DOCX / 图片文件转化为可结构化管理、可语义检索、可群体分析的学生画像数据，适用于学院学生发展分析、实验室人才储备、招生材料初筛和学生能力结构观察。

本项目已接入学校大语言模型 `ECNU-MAX`，用于简历补充抽取、画像标签生成和画像摘要生成。API Key 通过本地 `.env` 配置，不随源码提交。

## 核心能力

- 简历上传：支持单份和批量上传 `PDF / DOCX / 图片`。
- 文档解析：PDF 使用 `PyMuPDF`，DOCX 使用 `python-docx`，图片预留 OCR 处理能力。
- Section 切分：将简历粗层切分为 `basic_info / education / project / internship / paper / patent / competition / award / certificate / skills / self_eval`。
- 结构化抽取：规则抽取确定性字段，LLM 补充抽取复杂语义字段。
- 学生画像：生成学生类型、研究方向、方法能力、学术潜力、岗位方向、能力标签、行为标签、优势、风险和画像摘要。
- 主实体去重：同一学生重复上传时归并到统一 `student` 主实体，默认只展示最新主版本简历。
- 语义搜索：基于 LangChain + Chroma 构建学生简历 chunk 检索。
- 混合检索：Dense 向量检索 + BM25 关键词检索 + RRF 融合 + Qwen3 Reranker 精排。
- 群体分析：展示学校分布、学校层次分布、专业分布、学生类型、经历覆盖率、方向词云、标签分布和技能热力图。
- 人工校正：支持管理员校正结构化字段和画像结果，并保留版本记录。

## 技术架构

```text
frontend/
  React + Vite + TypeScript + Ant Design + ECharts

backend/
  FastAPI + SQLAlchemy + SQLite/PostgreSQL
  PyMuPDF / python-docx
  LangChain + Chroma
  BM25 / RRF / Rerank
  ECNU-MAX LLM Provider

storage/
  本地上传文件、Chroma 持久化目录
```

## 数据流

```text
简历文件
→ 文档解析
→ Section 切分
→ 规则抽取
→ ECNU-MAX 补充抽取
→ 标准化
→ 学生画像生成
→ 主实体去重
→ 经历单元 chunk 构建
→ Embedding 向量化
→ Chroma 入库
→ 语义搜索 / 群体分析
```

## LLM 使用点

项目通过统一 `ModelProvider` 抽象接入学校大语言模型 `ECNU-MAX`，主要用于：

- 从项目经历、实习经历中补充抽取职责、行动、成果、指标和工具。
- 生成学生画像标签候选，包括研究方向、方法能力、能力标签、行为标签等。
- 生成画像摘要，帮助管理员快速理解学生经历结构和发展倾向。

`.env` 示例：

```env
LLM_PROVIDER=openai
LLM_API_KEY=ECNU_MAX_API_KEY
LLM_BASE_URL=学校 ECNU-MAX OpenAI-compatible API 地址
LLM_MODEL=ECNU-MAX
LLM_TIMEOUT_SECONDS=60
LLM_TEMPERATURE=0.2
```

说明：项目使用 OpenAI-compatible 调用格式，因此 `LLM_PROVIDER` 可继续使用 `openai` 兼容适配器，实际底层模型由 `LLM_BASE_URL` 和 `LLM_MODEL` 指向 ECNU-MAX。

## 语义检索逻辑

系统不直接按整份简历检索，而是按经历单元构建 chunk。当前进入向量库的 chunk 类型包括：

```text
education       教育经历
project         项目经历
internship      实习经历
paper           论文成果
patent          专利成果
competition     竞赛经历
award           奖项荣誉
certificate     证书
```

检索流程：

```text
用户 query
→ Chroma Dense 向量召回
→ BM25 Keyword 关键词召回
→ RRF 融合两路候选
→ Qwen3-Reranker 重新排序
→ 按 student_id / resume_id 聚合为学生结果
```

前端会展示：

```text
Rerank：最终相关性分数
RRF：混合检索融合分
Dense：向量检索排名
Keyword：关键词候选排名
```

## 目录结构

```text
backend/
  app/
    api/              # FastAPI 路由
    core/             # 配置、安全、环境变量
    db/               # 数据库初始化和轻量迁移
    models/           # SQLAlchemy 模型
    schemas/          # Pydantic Schema
    services/         # 解析、抽取、画像、检索、报表、审计
    workers/          # 异步任务预留入口
  tests/              # 后端核心服务测试

frontend/
  src/
    api/              # 前端请求封装
    components/       # 通用组件
    layouts/          # 后台布局
    pages/            # 上传、列表、详情、搜索、报表页面
    styles/           # 全局视觉样式
    types/            # TypeScript 类型

sample_resumes/       # 示例简历材料
storage/              # 本地文件和 Chroma 持久化目录，不建议提交真实数据
```

## 本地运行

### 1. 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

编辑 `backend/.env`，至少配置：

```env
SECRET_KEY=请替换
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
DATABASE_URL=sqlite:///./student_portrait.db

LLM_API_KEY=ECNU_MAX_API_KEY
LLM_BASE_URL=学校 ECNU-MAX API 地址
LLM_MODEL=ECNU-MAX
```

启动：

```bash
PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload
```


### 2. 前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```



默认管理员账号由 `backend/.env` 配置：

```text
用户名：admin
密码：admin123
```

## Embedding 与 Rerank 模型

当前默认使用本地 Hugging Face 模型：

```env
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL_PATH=Qwen3-Embedding-0.6B
RERANK_PROVIDER=qwen3_local
RERANK_MODEL_PATH=Qwen3-Reranker-0.6B
```

如果其他机器没有下载本地模型，需要先下载对应模型，或修改 `.env` 中的模型路径。部分测试会真实加载本地模型，因此模型缺失时可临时跳过相关测试或先补齐模型目录。

## 测试

后端：

```bash
cd backend
PYTHONPATH=. .venv/bin/python -m compileall app
PYTHONPATH=. .venv/bin/python -m pytest tests/test_services.py
```

前端：

```bash
cd frontend
npm run build
```

当前已验证：

```text
backend tests/test_services.py：19 passed
frontend npm run build：通过
```


```text
本项目为本地可运行系统，已接入 ECNU-MAX。由于涉及本地数据库、向量库和私有 API Key，线上体验环境以演示视频和源码运行说明方式提交。
```

## 后续规划

- 增加更完整的高校层次与专业标准化词典。
- 增加 rerank 低分过滤，让语义搜索结果更稳定。
- 增加可解释证据高亮，展示画像标签来源。
- 增加面向学院的批量导入与报表导出。
- 扩展更多学生材料类型，例如成绩单、个人陈述、推荐信等。
