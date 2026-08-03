# Iwind：面向海上风电的智能体

**Iwind** 是一个智能体，专注于海上风电结构在极端灾害载荷下的动力学响应仿真。Iwind 负责自然语言任务理解、仿真参数组织、工作流编排、工具调用和结果整理；**Zwind** 负责实际物理仿真计算，输出应力、结构响应等结果供后续确定性后处理使用。

基于 **ReAct（Reasoning and Acting）** 框架，Agent 支持规划多步骤任务、调用专业计算工具，并对仿真结果进行整理和记录。

## 1. 核心架构

- **ReAct 推理循环**：通过"思考（Thought）—行动（Action）—观察（Observation）"循环，以对话驱动工具调用的方式执行工程任务。
- **封装工具集**：管理多种内部工具，支持载荷计算、应力分析和结构响应调用等。
- **多模态感知**：基于 YOLOv8m 的专用检测模块，从现场图像中提取目标属性。
- **混合智能**：支持在本地 **Ollama** 部署与在线 API（DeepSeek / Qwen）之间切换，用于推理和规划。

## 2. 项目结构

```
iwind/
├── README.md                        # 项目主文件（本文件）
├── README_CN.md                     # 中文版说明文档
├── requirements.txt                 # 根目录 Python 依赖
├── LICENSE
├── .gitattributes
│
├── llm_backend/                     # 核心后端（FastAPI + Agent 框架）
│   ├── run.py                       # 主入口：uvicorn 服务器，监听端口 9000
│   ├── run_mcp.py                   # MCP（Model Context Protocol）Agent 运行器
│   ├── main.py                      # FastAPI 应用：REST API 路由、SSE 流式响应、文件上传
│   ├── __init__.py
│   ├── requirements.txt             # 后端 Python 依赖
│   ├── .env                         # 环境变量（API 密钥、数据库配置等）
│   │
│   ├── app/                         # FastAPI 应用层
│   │   ├── api/                     # REST API 端点（认证、聊天、搜索、文件上传）
│   │   ├── core/                    # 核心工具：配置、数据库、安全认证、中间件、日志
│   │   ├── models/                  # SQLAlchemy ORM 模型（User、Message、Conversation、Chat）
│   │   ├── services/                # 业务逻辑服务层
│   │   │                            #   LLMFactory：chat / reasoner / search 服务的实例化工厂
│   │   │                            #   ConversationService：消息持久化
│   │   │                            #   EmbeddingService：基于 Ollama 的文本向量嵌入
│   │   │                            #   RedisSemanticCache：语义缓存层
│   │   │                            #   DeepseekService / OllamaService：模型 API 封装
│   │   ├── prompts/                 # 搜索及通用任务的 Prompt 模板
│   │   ├── schemas/                 # Pydantic 请求/响应模型
│   │   ├── tools/                   # 工具定义与搜索工具
│   │   ├── test/                    # 临时测试脚本（DeepSeek 流式调用、Ollama 基准测试）
│   │   └── lg_agent/                # 知识图谱增强 Agent（GraphRAG + LangGraph）
│   │       ├── lg_builder.py        # LangGraph 状态图构建器
│   │       ├── lg_states.py         # AgentState / InputState 定义
│   │       ├── lg_prompts.py        # 图推理 Prompt 模板
│   │       ├── main.py              # 图推理入口
│   │       └── kg_sub_graph/        # 知识图谱子图
│   │           ├── kg_builder.py    # 知识图谱构建与查询编排
│   │           ├── kg_neo4j_conn.py # Neo4j 连接管理
│   │           ├── kg_tools_list.py # 知识图谱推理工具注册表
│   │           ├── kg_states.py     # 知识图谱状态定义
│   │           └── agentic_rag_agents/   # 多组件 Agentic RAG 系统
│   │               ├── agent.py          # Agentic RAG 核心 Agent
│   │               ├── components/       # 15+ 子组件（text2cypher、visualize、planner、guardrails 等）
│   │               ├── workflows/        # 单 Agent 与多 Agent 工作流定义
│   │               ├── retrievers/       # Cypher 示例检索器（向量库、动态Schema）
│   │               └── ingest/           # 知识图谱数据导入（Cypher 示例）
│   │
│   ├── iwind_app/                   # Agent 框架核心（含多种 Agent 类型，OpenFAST/OpenSees 工具为扩展组件）
│   │   ├── agent/                   # Agent 实现
│   │   │   ├── base.py              # BaseAgent 抽象基类
│   │   │   ├── chatAgentBase.py     # 纯聊天 Agent（不调用工具）
│   │   │   ├── react.py             # ReActAgent（思考—行动—观察循环）
│   │   │   ├── manus.py             # Manus Agent（复杂任务规划）
│   │   │   ├── browser.py           # 浏览器自动化 Agent
│   │   │   ├── swe.py               # 软件工程 Agent
│   │   │   ├── twoStageAgent.py     # 两阶段推理 Agent
│   │   │   ├── hybrid.py            # 混合推理 Agent
│   │   │   ├── data_analysis.py     # 数据分析 Agent
│   │   │   ├── toolcall.py          # 工具调用 Agent
│   │   │   └── mcp.py               # MCP（Model Context Protocol）Agent
│   │   ├── tool/                    # 工具实现（40+ 工具）
│   │   │   ├── base.py              # BaseTool 抽象基类
│   │   │   ├── tool_collection.py   # 工具注册与加载器
│   │   │   ├── python_execute.py    # 沙箱内 Python 代码执行
│   │   │   ├── bash.py              # Bash 命令执行
│   │   │   ├── file_operators.py    # 文件读写操作
│   │   │   ├── str_replace_editor.py# 字符串替换式文件编辑
│   │   │   ├── file_saver.py        # 文件保存工具
│   │   │   ├── web_search.py        # 网页搜索工具
│   │   │   ├── planning.py          # 任务规划工具
│   │   │   ├── terminate.py         # 执行终止工具
│   │   │   ├── loader.py            # 工具加载器
│   │   │   ├── browser_use_tool.py  # 浏览器自动化工具
│   │   │   ├── create_chat_completion.py  # LLM 对话补全工具
│   │   │   ├── mcp.py               # MCP 客户端工具
│   │   │   ├── ask_human.py         # 人工介入工具
│   │   │   ├── search/              # 搜索引擎实现
│   │   │   │   ├── baidu_search.py, bing_search.py, duckduckgo_search.py, google_search.py
│   │   │   ├── openfast/            # OpenFAST 仿真封装（OC3/OC4 系列测试用例）
│   │   │   │   ├── openfast_5MW_Land_DLL_WTurb/
│   │   │   │   ├── openfast_5MW_ITIBarge_DLL_WTurb_WavesIrr/
│   │   │   │   ├── openfast_5MW_OC3Spar_DLL_WTurb_WavesIrr/
│   │   │   │   ├── openfast_5MW_OC4Jckt_DLL_WTurb_WavesIrr_MGrowth/
│   │   │   │   └── ...（共 8 个测试用例）
│   │   │   ├── yolo/                # YOLOv8 目标检测
│   │   │   │   └── yolo_detection/yolo_detection.py
│   │   │   └── zwind/               # Zwind 风电仿真 MCP 工具
│   │   │       └── wind/test/test.py
│   │   ├── flow/                    # 任务流程编排
│   │   │   ├── base.py              # BaseFlow 抽象基类
│   │   │   ├── planning.py          # 任务规划流程
│   │   │   └── flow_factory.py      # Agent 实例化工厂
│   │   ├── prompt/                  # 各类型 Agent 的系统提示词模板
│   │   │   ├── react.py, manus.py, browser.py, swe.py, planning.py
│   │   │   ├── toolcall.py, visualization.py, mcp.py, chat.py
│   │   │   └── browser.py, toolExtracter.py
│   │   ├── sandbox/                 # 沙箱代码执行环境
│   │   │   ├── core/
│   │   │   │   ├── sandbox.py       # 沙箱容器管理
│   │   │   │   ├── manager.py       # 沙箱生命周期管理器
│   │   │   │   ├── terminal.py      # 终端仿真
│   │   │   │   └── exceptions.py    # 沙箱异常定义
│   │   │   └── client.py            # 沙箱客户端
│   │   ├── mcp/                     # MCP 协议实现
│   │   │   └── server.py            # MCP 服务器
│   │   ├── config.py                # 全局配置
│   │   ├── schema.py                # Pydantic 模型（AgentState、Memory）
│   │   ├── llm.py                   # LLM 封装（Ollama / DeepSeek）
│   │   ├── logger.py                # 日志工具
│   │   ├── bedrock.py               # AWS Bedrock 集成
│   │   └── exceptions.py            # 自定义异常
│   │
│   ├── config/                      # 配置文件
│   │   ├── config.toml              # 主配置文件（模型、工具、路径等）
│   │   ├── tools_config.py          # 工具配置
│   │   ├── mcp.example.json         # MCP 配置模板
│   │   └── config.example*.toml     # 各模型的配置模板
│   │
│   ├── servers/                     # 仿真微服务后端
│   │   └── README.md                # OpenFAST / OpenSees / Zwind 服务部署指南
│   │
│   ├── scripts/                     # 工具脚本
│   │   └── init_db.py               # 数据库初始化脚本
│   │
│   ├── static/                      # 前端静态资源
│   ├── templates/                   # HTML 模板
│   └── utils/                       # 共享工具函数
│       ├── global_variables.py      # 全局会话/Agent 状态管理
│       ├── config_parser.py         # TOML 配置文件解析器
│       ├── auto_para_generator.py   # 自动参数生成器
│       └── replace_io.py            # I/O 重定向工具
│
├── training/                        # 领域模型训练流水线（第 7 节）
│   ├── data_engineering/            # 数据工程：语料处理、基准数据集构建
│   ├── domain_pretraining/         # 领域继续预训练
│   ├── instruction_tuning/          # 指令微调（LoRA + assistant-only loss）
│   ├── reward_modeling/             # 奖励建模（五级评分偏好学习）
│   ├── policy_optimization/         # 策略优化（GRPO）
│   ├── evaluation_and_integration/  # 评测与集成（GPTQ、RAG）
│   ├── TRAINING_README.md          # 训练流水线总览
│   ├── LOGIC_REVIEW.md             # 逻辑重构审查记录
│   ├── requirements.txt             # 训练依赖
│   └── validate_pipeline.py         # 静态验证脚本
│
├── reproduce/                       # 仿真复现包（第 6 节）
│   ├── README_EN_reproduce.md       # 详细复现指南（英文）
│   ├── single_simulation.py         # 交互式单次仿真（自然语言输入）
│   ├── batch_simulation.py          # 全量批量仿真（336 算例）
│   ├── process_results.py           # 后处理：从 .out 文件提取最大应力 → CSV
│   ├── visualization.py             # 可视化：最优桨距角曲线、热力图、3D 图表
│   ├── Iwind_reproduce_v5.tar.gz    # Docker 镜像（约 500 MB，脚本自动识别加载）
│   └── example_case/                # 完整示例算例
│       └── Earthquake_1g_Pitch90_Yaw-150/
│
├── yolo_fan/                        # YOLOv8m 风机损伤检测模型
│   ├── README.md                    # 训练配置与使用说明
│   ├── args.yaml                    # 完整训练配置
│   ├── results.csv                  # 训练指标日志
│   ├── results.png                  # 训练损失曲线
│   ├── F1_curve.png, P_curve.png, PR_curve.png, R_curve.png
│   ├── confusion_matrix.png, confusion_matrix_normalized.png
│   ├── labels.jpg                   # 标签分布图
│   ├── train_batch*.jpg, val_batch*.jpg  # 训练/验证样本可视化
│   └── weights/
│       ├── best.pt                  # 最佳验证checkpoint
│       └── last.pt                  # 最终训练checkpoint
│
└── qa_data/                         # 基准评测数据集
    └── Public Benchmark Dataset of Offshore Wind Large Model_15000.jsonl  # 15,000 条中文问答对
```

### 顶层文件

| 文件 | 说明 |
|------|------|
| `README.md` | 英文版项目说明（概述、安装、结构、可复现性指南） |
| `README_CN.md` | 本文件 — 中文版项目说明 |
| `requirements.txt` | 根目录 Python 依赖（FastAPI、LangGraph、LangChain 等） |
| `LICENSE` | MIT 开源许可证 |

### 核心目录

| 目录 | 说明 |
|------|------|
| `llm_backend/` | 主后端：FastAPI REST API + Agent 框架（含多种类型）；OpenFAST/OpenSees/GraphRAG 等为系统扩展能力 |
| `training/` | 领域模型训练流水线：数据工程 → 领域预训练 → 指令微调 → 奖励建模 → GRPO 策略优化 → 评测与集成 |
| `reproduce/` | 仿真复现包：单次及批量仿真脚本、后处理与可视化 |
| `yolo_fan/` | YOLOv8m 目标检测模型，用于风机损伤检测 |
| `qa_data/` | 15,000 条风电领域中文基准评测问答数据集 |

## 3. 环境与安装

### 前置依赖

- **Ollama**：用于运行本地微调的模型（如 DeepSeek-R1-0528-Qwen3-8B）。
- **Python**：3.10 及以上版本。
- **数据库**：
  - **MySQL**：管理项目数据和 Agent 记忆。
  - **Neo4j**：用于领域知识图谱（GraphRAG）推理。
  - **Redis**：高性能对话缓存与历史管理。
- **GraphRAG**：集成 Microsoft GraphRAG，支持全局/局部社区查询。

### 安装步骤

```
conda create -n iwind python=3.10
conda activate iwind
git clone https://github.com/xzpAM/iwind.git
cd Iwind
pip install -r requirements.txt
cd llm_backend
pip install -r requirements.txt
```

## 4. 配置

系统连接信息（API 密钥、数据库地址等）主要通过 `llm_backend/.env` 管理；模型、工具和路径等运行参数通过 `llm_backend/config/config.toml` 及相关配置文件管理。

> **注意**：`.env` 文件包含敏感信息（密钥、密码等），请在本地参考 `.env.example`（如存在）创建自己的 `.env` 文件，不要将包含真实密钥的 `.env` 直接提交到仓库。

#### **模型访问方式**

当前系统配置为通过本地 Ollama 服务与微调 Iwind 模型交互。

**材料可用性说明**：模型权重与领域强化学习训练脚本不在本仓库公开范围内。本仓库已开源的内容包括：框架代码、仿真复现脚本、Docker 仿真环境、15,000 条基准测试数据和 336 个算例的完整仿真输出。

配置示例

```
# --- LLM 服务选择 ---
# 选项：deepseek 或 ollama
CHAT_SERVICE=ollama
REASON_SERVICE=ollama
AGENT_SERVICE=ollama

# --- Ollama（本地模型）---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=iwind-chat-v1
OLLAMA_REASON_MODEL=iwind-reasoner-v1
OLLAMA_AGENT_MODEL=iwind-agent-v1
OLLAMA_EMBEDDING_MODEL=m3e-base

# --- 在线模型 API（可选）---
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# --- 视觉模型（图像解析）---
VISION_API_KEY=your_vision_key
VISION_BASE_URL=https://api.vl-model.com/v1
VISION_MODEL=qwen-vl-max

# --- 搜索与工具 ---
SERPAPI_KEY=your_serpapi_key
SEARCH_RESULT_COUNT=5

# --- 数据库：MySQL ---
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=iwind_db

# --- 数据库：Neo4j（知识图谱）---
NEO4J_URL=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=iwind_kg

# --- 缓存：Redis ---
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_CACHE_EXPIRE=3600

# --- Microsoft GraphRAG ---
GRAPHRAG_PROJECT_DIR=./graphrag_storage
GRAPHRAG_QUERY_TYPE=local
GRAPHRAG_COMMUNITY_LEVEL=2
```

## 5. 运行 Agent

### 启动系统

```
cd llm_backend
python run.py
```

### 对话使用方式

用户以自然语言描述仿真需求，Iwind 解析参数、生成配置文件、调用 Zwind 执行仿真，并整理输出结果。

**用户提问**："模拟 IEA 10 MW 海上风机在风速 40 m/s、1g 地震加速度、桨距角 0°、偏航角 -150° 条件下的结构响应。"

**Iwind 处理流程**：

1. **参数解析**：从自然语言中提取风速、加速度、桨距角、偏航角等仿真参数。
2. **配置生成**：生成 Zwind 所需的仿真配置文件。
3. **仿真执行**：调用 Zwind 执行结构动力学仿真。
4. **结果输出**：输出包含结构应力、位移等时序数据的仿真结果文件。

## 6. 可复现性

研究者可借助本开源仓库 `reproduce` 目录下的代码与配套材料，独立复现完整端到端链路：

```
自然语言输入 → 仿真配置生成 → Zwind 启动 → 仿真结果输出
```

运行后可得到包含 **336 个工况**、约 **73 GB** 完整仿真结果。

> **重要说明**
> 模型权重、领域强化学习训练脚本暂未开源。上述文件仅影响模型训练过程复现，不影响验证本文提出的自然语言驱动自动仿真核心工作流。
>
> 相关材料正在进行知识产权、第三方许可与法律合规审查，暂时限制公开分发。论文正式发表且合规审查结束后，我们将在许可范围内开放可公开的权重与训练脚本。

### 数据集下载

336 个工况完整仿真输出文件（约 73 GB）下载地址：

```
https://download.scidb.cn/download?fileId=8d299dd8a428ffdce4a961cf290ff34c&path=/V1/IWind_IEA10MW_Offshore_Wind_Turbine_Extreme_Loading_Dataset.tar&username=linjunfu@zju.edu.cn&fileName=IWind_IEA10MW_Offshore_Wind_Turbine_Extreme_Loading_Dataset.tar
```

本地复现的详细说明（交互式单次仿真和全量批量仿真），请参阅 [`reproduce/README_EN_reproduce.md`](reproduce/README_EN_reproduce.md)。

### `reproduce/` 目录说明

该目录包含支撑论文实验验证的完整仿真复现包，使研究者能够独立复现从自然语言输入到仿真输出的全流程。

```
reproduce/
├── single_simulation.py          # 交互式单次仿真
├── batch_simulation.py           # 全量批量仿真（336 算例）
├── process_results.py            # 后处理：从 .out 提取 von Mises 应力 → CSV
├── visualization.py              # 可视化：最优桨距角曲线、热力图、3D 图表
├── Iwind_reproduce_v5.tar.gz     # Docker 镜像（约 500 MB，脚本自动识别加载）
└── example_case/                 # 预配置仿真环境示例 Docker 容器
    └── Earthquake_1g_Pitch90_Yaw-150/
```

**流程阶段：**

| 阶段 | 脚本 | 输入 | 输出 |
|------|------|------|------|
| 1. 仿真启动 | `single_simulation.py` 或 `batch_simulation.py` | 自然语言或算例列表 | Zwind 仿真输出文件 |
| 2. 应力提取 | `process_results.py` | Zwind 仿真结果 | 最大结构应力提取结果 |
| 3. 最优桨距角分析 | `process_results.py` | 应力提取结果 | 最优桨距角提取结果（在固定偏航角下，从不同桨距角工况的最大结构应力中选取最小值对应的桨距角） |
| 4. 可视化 | `visualization.py`（FastAPI 端点） | CSV 文件 | PNG 图、最优桨距角曲线、热力图 |

**批量仿真配置：**

| 算例类型 | 参数 | 算例数 |
|---------|------|--------|
| 台风 | 风速 40 m/s | 84（7 桨距角 × 12 偏航角） |
| 台风 | 风速 60 m/s | 84 |
| 地震 | 加速度 9.81 m/s²（1g） | 84 |
| 地震 | 加速度 19.62 m/s²（2g） | 84 |
| **合计** | | **336 算例** |

> **注意**：Docker 镜像（`Iwind_reproduce_v5.tar.gz`，约 500 MB）必须先下载并放置在本目录下才能运行脚本。下载地址见 [`reproduce/README_EN_reproduce.md`](reproduce/README_EN_reproduce.md)。

## 7. 补充数据集

### `yolo_fan/` — 风机损伤检测模型

YOLOv8m 目标检测模型，为系统多模态感知能力提供支持。以下模型参数均基于 `args.yaml`、`results.csv` 和训练日志直接报告，不作类别扩展推断。

| 项目 | 值 |
|------|---|
| 模型架构 | YOLOv8m（medium） |
| 输入尺寸 | 640 × 640 px |
| 训练轮次 | 50 |
| 批大小 | 128 |
| 训练设备 | 多卡 GPU（CUDA） |
| 数据增强 | Mosaic 1.0、RandAugment、Random Erasing（p=0.4） |

**输出产物：**
- `weights/best.pt` — 最佳验证 checkpoint
- `weights/last.pt` — 最终训练 checkpoint
- `results.csv` — 训练指标（每轮 mAP50、mAP50-95、precision、recall）
- `results.png` — 训练损失曲线
- `F1_curve.png`、`PR_curve.png`、`P_curve.png`、`R_curve.png` — 评估曲线
- `confusion_matrix.png`、`confusion_matrix_normalized.png` — 混淆矩阵
- `train_batch*.jpg`、`val_batch0_pred.jpg`、`val_batch0_labels.jpg` — 可视化样本

**使用示例：**
```python
from ultralytics import YOLO

model = YOLO("yolo_fan/weights/best.pt")
results = model.predict(source="field_image.jpg", conf=0.5)
```

### `qa_data/` — 基准评测数据集

包含 **15,000 条中文问答对**的公开基准数据集，涵盖海上风电结构分析、载荷预测、故障诊断等任务类型。每个条目包含：

| 字段 | 说明 |
|------|------|
| `task_type` | 任务类别（如 `T1 Analysis`，类别见数据集实际内容） |
| `input` | 自然语言问题 |
| `output` | 参考答案 |

该数据集用于评估大语言模型在风电工程领域的领域知识与推理能力。

## 8. 训练流水线

本目录包含 Iwind 领域模型的完整训练流水线源代码。原始 notebook 已将逻辑提取、重构并转换为可审计的 Python 模块。

### 流水线构成

| 模块 | 作用 | 主要模型或产物 |
|------|------|----------------|
| `data_engineering` | 语料标准化、过滤、去重、分段及多语言基准数据集构建 | 训练数据集与基准数据集 |
| `domain_pretraining` | 领域继续预训练（因果语言建模） | `DeepSeek-R1-0528-Qwen3-8B` |
| `instruction_tuning` | 基于 LoRA 和仅 assistant token 损失的指令对齐 | 领域 SFT 模型 |
| `reward_modeling` | 五级评分体系的两两偏好学习 | `QRM-Llama3.1-8B-v2` |
| `policy_optimization` | 基于奖励模型的 GRPO（Group Relative Policy Optimization）策略优化 | GRPO 策略模型 |
| `evaluation_and_integration` | 全周期评测、GPTQ 导出及三路径 RAG 集成 | 最终 Iwind 推理模型 |

### 执行顺序

```
data_engineering
  → domain_pretraining
  → instruction_tuning
  → reward_modeling
  → policy_optimization
  → evaluation_and_integration
```

各模块均包含独立的 `README.md`、`requirements.txt`、配置文件、Python 入口及本地单元测试。配置示例中的路径为占位符，需根据目标集群环境修改。

### 各模块说明

**`data_engineering/`** — 数据工程
仅使用 Python 标准库。功能包括：严格的 frozen dataclass schema、Unicode 与空格标准化、稳定的内容/来源派生 ID、确定性 token 分块（Unicode 词/标点边界）、精确 SHA-256 与可配置 shingle-Jaccard 近重复检测、按记录分组的平衡分割、跨分割组污染审计、语料库统计与 manifest 清单。

**`domain_pretraining/`** — 领域预训练
在标准化语料上进行继续因果语言模型预训练。关键设计：确定性全局 token packing、显式 EOS 边界、保留 token 核算、验证 perplexity 从验证 loss 而非生成输出推导。

**`instruction_tuning/`** — 指令微调
基于 LoRA 和仅 assistant 因果语言建模损失进行指令对齐。关键设计：tokenizer 原生 chat template、仅 assistant token 贡献损失（user/system/padding 标记为 `-100`）、监督保留截断。

**`reward_modeling/`** — 奖励建模
五级评分体系的两两偏好学习 pipeline。评分标准：1=不可接受、2=有限、3=合格、4=强、5=专家。关键设计：问题组分块后展开偏好对、显式奖励边界（scalar logits 与 quantile mean）。

**`policy_optimization/`** — 策略优化（GRPO）
使用 transport-neutral 领域奖励边界的 GRPO 策略优化。关键设计：本地与 HTTP 两种奖励服务模式、显式 per-rank 设备放置、奖励失败上报为错误而非静默零值奖励。

**`evaluation_and_integration/`** — 评测与集成
全周期评测、GPTQ 导出及 RAG 集成。功能包括：Wilson 区间（客观题准确率）与 bootstrap 区间（专家维度）、SFT/GRPO 对比评测、原子 GPTQ 分阶段导出、BM25/dense/structured 多路径检索召回、引用验证。

### 静态验证

从仓库根目录运行全部静态检查与本地逻辑测试：

```bash
python iwind/validate_pipeline.py
```

该验证器解析所有 Python 与 JSON 文件，检查文档和 requirements 是否存在，并运行六个模块的测试套件。验证器不下载 checkpoint 也不启动训练。

> **注意**：本训练流水线代码已公开。模型权重（`DeepSeek-R1-0528-Qwen3-8B`、`QRM-Llama3.1-8B-v2`）及领域强化学习训练脚本暂未公开，详见第 6 节材料可用性说明。

## 9. 许可证

基于 **MIT 许可证**开源。

```
Copyright (c) 2026 ZJU
```
