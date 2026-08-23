# Iwind: Physics-Informed Wind Turbine Simulation Agent

**Iwind** is an agent designed for structural analysis and simulation of offshore wind turbines under extreme disaster loads. Iwind is responsible for natural language task understanding, simulation parameter organization, workflow orchestration, tool invocation, and result compilation; **Zwind** handles the actual physics simulation, outputting stress and structural response results for subsequent deterministic post-processing.

By leveraging the **ReAct (Reasoning and Acting)** framework, the agent supports planning multi-step tasks, invoking specialized calculation tools, and organizing and recording simulation results.



## 1. Core Architecture

- **ReAct Loop**: Implements a "Thought-Action-Observation" cycle to execute engineering tasks through dialogue-driven tool invocation.
- **Encapsulated Tools**: Manages multiple internal tools for load calculation, stress analysis, and structural response invocation.
- **Multimodal Perception**: Uses a dedicated `Detector` module based on YOLOv8m to extract attributes from field imagery.
- **Hybrid Intelligence**: Supports switching between local **Ollama** deployments and online APIs (Deepseek/Qwen) for reasoning and planning.

## 2. Project Structure

```
iwind/
├── README.md                        # This file
├── requirements.txt                 # Root-level Python dependencies
├── LICENSE
├── .gitattributes
│
├── llm_backend/                     # Core backend (FastAPI + Agent framework)
│   ├── run.py                       # Main entry point: uvicorn server on port 9000
│   ├── run_mcp.py                   # MCP (Model Context Protocol) agent runner
│   ├── main.py                      # FastAPI app: REST API routes, SSE streaming, file upload
│   ├── __init__.py
│   ├── requirements.txt             # Backend Python dependencies
│   ├── .env                         # Environment variables (API keys, DB config)
│   │
│   ├── app/                         # FastAPI application layer
│   │   ├── api/                     # REST API endpoints (auth, chat, search, file upload)
│   │   ├── core/                    # Core utilities: config, database, security, middleware, logger
│   │   ├── models/                  # SQLAlchemy ORM models (User, Message, Conversation, Chat)
│   │   ├── services/                # Business logic services
│   │   │                            #   LLMFactory: chat / reasoner / search service instantiation
│   │   │                            #   ConversationService: message persistence
│   │   │                            #   EmbeddingService: text embedding via Ollama
│   │   │                            #   RedisSemanticCache: semantic caching layer
│   │   │                            #   DeepseekService / OllamaService: model API wrappers
│   │   ├── prompts/                 # Prompt templates for search and general tasks
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── tools/                   # Tool definitions and search utilities
│   │   ├── test/                    # ad-hoc test scripts (DeepSeek streaming, Ollama benchmark)
│   │   └── lg_agent/                # Knowledge-graph-enhanced Agent (GraphRAG + LangGraph)
│   │       ├── lg_builder.py        # LangGraph state graph builder
│   │       ├── lg_states.py         # AgentState / InputState definitions
│   │       ├── lg_prompts.py        # Prompt templates for graph reasoning
│   │       ├── main.py              # Graph reasoning entry point
│   │       └── kg_sub_graph/        # Knowledge graph sub-graph
│   │           ├── kg_builder.py    # KG construction and query orchestration
│   │           ├── kg_neo4j_conn.py # Neo4j connection management
│   │           ├── kg_tools_list.py # Tool registry for KG-based reasoning
│   │           ├── kg_states.py     # KG-specific state definitions
│   │           └── agentic_rag_agents/   # Multi-component agentic RAG system
│   │               ├── agent.py          # Core agentic RAG agent
│   │               ├── components/       # 15+ sub-components (text2cypher, visualize, planner, guardrails...)
│   │               ├── workflows/        # Single-agent and multi-agent workflow definitions
│   │               ├── retrievers/       # Cypher example retrievers (vector store, dynamic schema)
│   │               └── ingest/           # KG data ingestion (Cypher examples)
│   │
│   ├── iwind_app/                   # Agent framework core (multiple agent types; OpenFAST/OpenSees tools are extension components)
│   │   ├── agent/                   # Agent implementations
│   │   │   ├── base.py              # BaseAgent abstract base class
│   │   │   ├── chatAgentBase.py     # Chat-only agent (no tool use)
│   │   │   ├── react.py             # ReActAgent (Thought-Action-Observation loop)
│   │   │   ├── manus.py             # Manus agent (complex task planning)
│   │   │   ├── browser.py           # Browser-use agent
│   │   │   ├── swe.py               # Software engineering agent
│   │   │   ├── twoStageAgent.py     # Two-stage reasoning agent
│   │   │   ├── hybrid.py            # Hybrid reasoning agent
│   │   │   ├── data_analysis.py     # Data analysis agent
│   │   │   ├── toolcall.py          # Tool-calling agent
│   │   │   └── mcp.py               # MCP (Model Context Protocol) agent
│   │   ├── tool/                    # Tool implementations (40+ tools)
│   │   │   ├── base.py              # BaseTool abstract class
│   │   │   ├── tool_collection.py   # Tool registry and loader
│   │   │   ├── python_execute.py    # Python code execution in sandbox
│   │   │   ├── bash.py              # Bash command execution
│   │   │   ├── file_operators.py    # File read/write operations
│   │   │   ├── str_replace_editor.py# String-based file editing
│   │   │   ├── file_saver.py        # File saving utility
│   │   │   ├── web_search.py        # Web search tool
│   │   │   ├── planning.py          # Task planning tool
│   │   │   ├── terminate.py         # Execution termination tool
│   │   │   ├── loader.py            # Tool loader
│   │   │   ├── browser_use_tool.py  # Browser automation tool
│   │   │   ├── create_chat_completion.py  # LLM chat completion tool
│   │   │   ├── mcp.py               # MCP client tool
│   │   │   ├── ask_human.py         # Human-in-the-loop tool
│   │   │   ├── search/              # Search implementations
│   │   │   │   ├── baidu_search.py, bing_search.py, duckduckgo_search.py, google_search.py
│   │   │   ├── openfast/            # OpenFAST simulation wrappers (OC3/OC4 test cases)
│   │   │   │   ├── openfast_5MW_Land_DLL_WTurb/
│   │   │   │   ├── openfast_5MW_ITIBarge_DLL_WTurb_WavesIrr/
│   │   │   │   ├── openfast_5MW_OC3Spar_DLL_WTurb_WavesIrr/
│   │   │   │   ├── openfast_5MW_OC4Jckt_DLL_WTurb_WavesIrr_MGrowth/
│   │   │   │   └── ... (8 test cases total)
│   │   │   ├── yolo/                # YOLOv8 object detection
│   │   │   │   └── yolo_detection/yolo_detection.py
│   │   │   └── zwind/               # Zwind simulation MCP tool
│   │   │       └── wind/test/test.py
│   │   ├── flow/                    # Task flow orchestration
│   │   │   ├── base.py              # BaseFlow abstract class
│   │   │   ├── planning.py          # Task planning flow
│   │   │   └── flow_factory.py      # Flow factory for agent instantiation
│   │   ├── prompt/                  # System prompts for each agent type
│   │   │   ├── react.py, manus.py, browser.py, swe.py, planning.py
│   │   │   ├── toolcall.py, visualization.py, mcp.py, chat.py
│   │   │   └── browser.py, toolExtracter.py
│   │   ├── sandbox/                 # Sandboxed code execution environment
│   │   │   ├── core/
│   │   │   │   ├── sandbox.py       # Sandbox container management
│   │   │   │   ├── manager.py       # Sandbox lifecycle manager
│   │   │   │   ├── terminal.py      # Terminal emulation
│   │   │   │   └── exceptions.py    # Sandbox-specific exceptions
│   │   │   └── client.py            # Sandbox client
│   │   ├── mcp/                     # MCP protocol implementation
│   │   │   └── server.py            # MCP server
│   │   ├── config.py                # Global configuration
│   │   ├── schema.py                # Pydantic schemas (AgentState, Memory)
│   │   ├── llm.py                   # LLM wrapper (Ollama / DeepSeek)
│   │   ├── logger.py                # Logging utility
│   │   ├── bedrock.py               # AWS Bedrock integration
│   │   └── exceptions.py            # Custom exceptions
│   │
│   ├── config/                      # Configuration files
│   │   ├── config.toml              # Main configuration (model, tools, paths)
│   │   ├── tools_config.py          # Tools configuration
│   │   ├── mcp.example.json         # MCP configuration template
│   │   └── config.example*.toml     # Per-model configuration templates
│   │
│   ├── servers/                     # Simulation microservice backends
│   │   └── README.md                # OpenFAST / OpenSees / Zwind server deployment guide
│   │
│   ├── scripts/                     # Utility scripts
│   │   └── init_db.py               # Database initialization
│   │
│   ├── static/                      # Frontend static assets
│   ├── templates/                   # HTML templates
│   └── utils/                       # Shared utilities
│       ├── global_variables.py      # Global session/agent state management
│       ├── config_parser.py         # TOML configuration parser
│       ├── auto_para_generator.py   # Auto parameter generator
│       └── replace_io.py            # I/O redirection utility
│
├── training/                        # Domain model training pipeline (Section 7)
│   ├── data_engineering/            # Dataset construction and benchmark building
│   ├── domain_pretraining/          # Continued domain pretraining
│   ├── instruction_tuning/          # Instruction tuning (LoRA + assistant-only loss)
│   ├── reward_modeling/             # Reward modeling (five-level rubric pairwise learning)
│   ├── policy_optimization/         # Policy optimization (GRPO)
│   ├── evaluation_and_integration/  # Evaluation and integration (GPTQ, RAG)
│   ├── TRAINING_README.md          # Training pipeline overview
│   ├── LOGIC_REVIEW.md             # Logic reconstruction review record
│   ├── requirements.txt             # Training dependencies
│   └── validate_pipeline.py         # Static validation script
│
├── reproduce/                       # Simulation reproduction package (Section 5)
│   ├── README_EN_reproduce.md       # Detailed reproduction guide
│   ├── single_simulation.py         # Single interactive simulation (natural language)
│   ├── batch_simulation.py          # Full batch simulation (336 cases)
│   ├── process_results.py           # Post-processing: extract max stress → CSV
│   ├── visualization.py             # Visualization: optimal pitch curves, heatmaps
│   ├── Iwind_reproduce_v5.tar.gz    # Docker image (~500 MB, auto-loaded by scripts)
│   └── example_case/                # Complete example case
│       └── Earthquake_1g_Pitch90_Yaw-150/
│
├── yolo_fan/                        # YOLOv8m fan detection model
│   ├── README.md                    # Training configuration and usage
│   ├── args.yaml                    # Full training configuration
│   ├── results.csv                  # Training metrics log
│   ├── results.png                  # Training loss curves
│   ├── F1_curve.png, P_curve.png, PR_curve.png, R_curve.png
│   ├── confusion_matrix.png, confusion_matrix_normalized.png
│   ├── labels.jpg                   # Label distribution
│   ├── train_batch*.jpg, val_batch*.jpg  # Training/validation samples
│   └── weights/
│       ├── best.pt                  # Best model checkpoint
│       └── last.pt                  # Last model checkpoint
│
└── qa_data/                         # Benchmark dataset
    └── Public Benchmark Dataset of Offshore Wind Large Model_15000.jsonl  # 15,000 QA pairs
```

### Top-Level Files

| File | Description |
|------|-------------|
| `README.md` | This file — project overview, setup, structure, and reproducibility guide |
| `requirements.txt` | Root-level Python dependencies (FastAPI, LangGraph, LangChain, etc.) |
| `LICENSE` | MIT License |

### Core Directories

| Directory | Description |
|-----------|-------------|
| `llm_backend/` | Main backend: FastAPI REST API + Agent framework (multiple types); OpenFAST/OpenSees/GraphRAG are system extension capabilities |
| `training/` | Domain model training pipeline: data engineering → domain pretraining → instruction tuning → reward modeling → GRPO policy optimization → evaluation and integration |
| `reproduce/` | Simulation reproduction package — single-case and batch simulation scripts, post-processing, and visualization |
| `yolo_fan/` | YOLOv8m object detection model for wind turbine damage inspection |
| `qa_data/` | 15,000-pair public benchmark dataset for offshore wind domain LLM evaluation |

## 3. Environment & Setup

### Prerequisites

- **Ollama**: For hosting local fine-tuned models (e.g., DeepSeek-R1-0528-Qwen3-8B).
- **Python**: 3.10 or higher.
- **Databases**:
  - **MySQL**: For managing project data and agent memory.
  - **Neo4j**: For domain-specific Knowledge Graph (GraphRAG) reasoning.
  - **Redis**: For high-performance conversation caching and history.
- **GraphRAG**: Integrated Microsoft GraphRAG for complex global/local community-based queries.

### Installation

```
conda create -n iwind python=3.10
conda activate iwind
git clone https://github.com/linjunfuzju/iwind.git
cd Iwind
pip install -r requirements.txt
cd llm_backend
pip install -r requirements.txt
```

## 4. Configuration

System connection information (API keys, database addresses, etc.) is primarily managed through `llm_backend/.env`; runtime parameters such as models, tools, and paths are managed through `llm_backend/config/config.toml` and related configuration files.

> **Note**: The `.env` file contains sensitive information (keys, passwords, etc.). Please create your own `.env` locally by referencing `.env.example` (if available), and do not commit a `.env` with real credentials to the repository.

#### **Accessing the Models**

Currently, the system is configured to interface with the fine-tuned Iwind models via the local Ollama service.

**Material Availability**: Model weights and domain-specific RL training scripts are not included in this repository's public scope. Already open-sourced materials include: framework code, simulation reproduction scripts, Docker simulation environment, 15,000-entry benchmark dataset, and complete simulation outputs for all 336 cases.

Code snippet

```
# --- LLM Service Selection ---
# Options: deepseek or ollama
CHAT_SERVICE=ollama
REASON_SERVICE=ollama
AGENT_SERVICE=ollama

# --- Ollama (Local Models) ---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=iwind-chat-v1
OLLAMA_REASON_MODEL=iwind-reasoner-v1
OLLAMA_AGENT_MODEL=iwind-agent-v1
OLLAMA_EMBEDDING_MODEL=m3e-base

# --- Online Model APIs (Optional) ---
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# --- Vision Model (Image Parsing) ---
VISION_API_KEY=your_vision_key
VISION_BASE_URL=https://api.vl-model.com/v1
VISION_MODEL=qwen-vl-max

# --- Search & Tools ---
SERPAPI_KEY=your_serpapi_key
SEARCH_RESULT_COUNT=5

# --- Database: MySQL ---
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=iwind_db

# --- Database: Neo4j (Knowledge Graph) ---
NEO4J_URL=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=iwind_kg

# --- Cache: Redis ---
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

## 5. Running the Agent

### Start the System

```
cd llm_backend
python run.py
```

### Usage via Dialogue

Users describe simulation needs in natural language. Iwind parses the parameters, generates a configuration file, invokes Zwind to run the simulation, and compiles the output results.

**User Question**: "Simulate the structural response of the IEA 10 MW offshore wind turbine under wind speed 40 m/s, 1g earthquake acceleration, 0° pitch angle, and -150° yaw angle."

**Iwind Process**:

1. **Parameter parsing**: Extracts wind speed, acceleration, pitch angle, yaw angle and other simulation parameters from natural language.
2. **Configuration generation**: Generates the Zwind configuration file required for the simulation.
3. **Simulation execution**: Invokes Zwind to perform the structural dynamics simulation.
4. **Result output**: Outputs simulation result files containing time-series data such as structural stress and displacement.



## 6. Reproducibility

Researchers can use the code and supporting materials in the `reproduce` directory of this open-source repository to independently reproduce the complete end-to-end pipeline:

```
Natural language input → Simulation configuration generation → Zwind launch → Simulation result output
```

Running it yields complete simulation results covering **336 cases** (approximately **73 GB**).

> **Important Notes**
> Model weights and domain-specific reinforcement learning training scripts are not yet open-sourced. These files only affect reproduction of the model training process and do not affect verification of the core natural language-driven automatic simulation workflow proposed in this paper.
>
> Related materials are undergoing intellectual property, third-party license, and legal compliance review, and public distribution is temporarily restricted. Once the paper is officially published and the compliance review is completed, we will release eligible model weights and training scripts within the scope of applicable licenses.

### Dataset Download

Notice (Dataset Download):
The complete simulation dataset generated by the natural-language-driven automatic simulation workflow is provided through the download links below. These links are exactly the same as those provided in the Data availability section of the paper.

Due to the large size of the compressed dataset files, the download links may not open correctly when directly clicked from Markdown viewers or web interfaces. Please copy the complete URL (including all parameters) and paste it into the browser address bar manually to start the download.

Please ensure that the entire URL is copied without missing any characters; incomplete URLs may result in download failure.

Complete simulation output files for all 336 cases (approximately 73 GB) can be downloaded here:

```
https://download.scidb.cn/download?fileId=5e3940a6e96d9251f79bce2c9582fb5f&path=/V1/Iwind simulation dataset.tar&username=linjunfu@zju.edu.cn&fileName=Iwind%20simulation%20dataset.tar
```

For local reproduction instructions (single-case interactive simulation and full batch simulation), please refer to [`reproduce/README_EN_reproduce.md`](reproduce/README_EN_reproduce.md).

### The `reproduce/` Directory

This directory contains the complete simulation reproduction package that underpins the paper's experimental validation. It enables researchers to independently reproduce the full end-to-end pipeline from natural language input to simulation output.

```
reproduce/
├── single_simulation.py          # Single interactive simulation
├── batch_simulation.py           # Full batch simulation (336 cases)
├── process_results.py            # Post-processing: extract von Mises stress → CSV
├── visualization.py              # Visualization: optimal pitch curves, heatmaps, 3D plots
├── Iwind_reproduce_v5.tar.gz     # Docker image (~500 MB, auto-detected by scripts)
└── example_case/                 # Complete example case
    └── Earthquake_1g_Pitch90_Yaw-150/
```

**Pipeline stages:**

| Stage | Script | Input | Output |
|-------|--------|-------|--------|
| 1. Simulation launch | `single_simulation.py` or `batch_simulation.py` | Natural language or case list | Zwind simulation output files |
| 2. Stress extraction | `process_results.py` | Zwind simulation results | Maximum structural stress extraction results |
| 3. Optimal pitch analysis | `process_results.py` | Stress extraction results | Optimal pitch angle extraction results (at each fixed yaw angle, selects the pitch angle corresponding to the minimum maximum structural stress across all pitch angle cases) |
| 4. Visualization | `visualization.py` (FastAPI endpoints) | CSV files | PNG plots, optimal pitch curves, heatmaps |

**Batch simulation configuration:**

| Case Type | Parameter | Cases |
|-----------|-----------|-------|
| Typhoon | Wind speed 40 m/s | 84 (7 pitch × 12 yaw angles) |
| Typhoon | Wind speed 60 m/s | 84 |
| Earthquake | Acceleration 9.81 m/s² (1g) | 84 |
| Earthquake | Acceleration 19.62 m/s² (2g) | 84 |
| **Total** | | **336 cases** |

> **Note:** The Docker image (`Iwind_reproduce_v5.tar.gz`, ~500 MB) must be downloaded and placed in this directory before running the scripts. The download link is provided in [`reproduce/README_EN_reproduce.md`](reproduce/README_EN_reproduce.md).

## 7. Supplementary Datasets

### `yolo_fan/` — Wind Turbine Damage Detection Model

A YOLOv8m-based object detection model that supports the system's multimodal perception capability. Model parameters below are reported directly from `args.yaml`, `results.csv`, and training logs; no class extensions are inferred beyond what is documented in these files.

| Item | Value |
|------|-------|
| Architecture | YOLOv8m (medium) |
| Input size | 640 × 640 px |
| Epochs | 50 |
| Batch size | 128 |
| Training device | Multi-GPU (CUDA) |
| Data augmentation | Mosaic 1.0, RandAugment, Random Erasing (p=0.4) |

**Output artifacts:**
- `weights/best.pt` — Best validation checkpoint
- `weights/last.pt` — Last training checkpoint
- `results.csv` — Training metrics (mAP50, mAP50-95, precision, recall per epoch)
- `results.png` — Training loss curves
- `F1_curve.png`, `PR_curve.png`, `P_curve.png`, `R_curve.png` — Evaluation curves
- `confusion_matrix.png`, `confusion_matrix_normalized.png` — Confusion matrices
- `train_batch*.jpg`, `val_batch0_pred.jpg`, `val_batch0_labels.jpg` — Visual samples

**Usage example:**
```python
from ultralytics import YOLO

model = YOLO("yolo_fan/weights/best.pt")
results = model.predict(source="field_image.jpg", conf=0.5)
```

### `qa_data/` — Benchmark Dataset

A public benchmark dataset of **15,000 Chinese QA pairs** covering offshore wind turbine structural analysis, load prediction, failure diagnosis, and related tasks. Each entry contains:

| Field | Description |
|-------|-------------|
| `task_type` | Task category (e.g., `T1 Analysis`; see actual dataset content for all categories) |
| `input` | Natural language question |
| `output` | Reference answer |

This dataset is used to evaluate the domain knowledge and reasoning capabilities of large language models on offshore wind engineering tasks.

## 8. Training Pipeline

This directory contains the source code for the complete Iwind domain model training pipeline. The original notebooks have been reviewed, corrected, and converted into auditable Python modules.

### Pipeline Stages

| Module | Purpose | Primary Model or Artifact |
|---|---|---|
| `data_engineering` | Corpus normalization, filtering, deduplication, splitting, and multilingual benchmark construction | Training and benchmark datasets |
| `domain_pretraining` | Continued autoregressive domain pretraining | `DeepSeek-R1-0528-Qwen3-8B` |
| `instruction_tuning` | Instruction alignment with LoRA and assistant-only loss | Domain SFT model |
| `reward_modeling` | Pairwise preference learning with five-level quality rubric | `QRM-Llama3.1-8B-v2` |
| `policy_optimization` | Group Relative Policy Optimization using the reward model | GRPO policy model |
| `evaluation_and_integration` | Full-cycle evaluation, GPTQ export, and three-path RAG integration | Final Iwind inference model |

### Execution Order

```
data_engineering
  → domain_pretraining
  → instruction_tuning
  → reward_modeling
  → policy_optimization
  → evaluation_and_integration
```

Each module has its own `README.md`, `requirements.txt`, configuration files, Python entry points, and local unit tests. Paths in example configurations are placeholders and must be changed to match the target cluster.

### Module Details

**`data_engineering/`** — Dataset Construction
Uses only the Python standard library. Capabilities: strict frozen dataclass schemas, Unicode and whitespace normalization, stable content/source-derived identifiers, deterministic token-aware chunking (Unicode word/punctuation boundaries), exact SHA-256 and configurable shingle-Jaccard near deduplication, grouped splits, cross-split contamination audits, corpus statistics, and artifact manifests.

**`domain_pretraining/`** — Domain Pretraining
Continued causal language model pretraining on the normalized Iwind corpus. Key design: deterministic global token packing, explicit EOS boundaries, retained-token accounting, validation perplexity from eval loss (not generation output).

**`instruction_tuning/`** — Instruction Tuning
Instruction alignment via LoRA with assistant-only causal LM loss. Key design: tokenizer native chat template, only assistant tokens contribute to loss (user/system/padding labeled `-100`), supervision-preserving truncation.

**`reward_modeling/`** — Reward Modeling
Pairwise preference learning with a five-level rubric (1=Unacceptable, 2=Limited, 3=Competent, 4=Strong, 5=Expert). Key design: question-group-safe splitting before pair expansion, explicit reward boundaries (scalar logits and quantile mean).

**`policy_optimization/`** — Policy Optimization (GRPO)
GRPO with a transport-neutral domain reward boundary. Key design: local and HTTP reward service modes, explicit per-rank device placement, reward failures reported as errors (not silently converted to zero rewards).

**`evaluation_and_integration/`** — Evaluation and Integration
Full-cycle evaluation, GPTQ export, and RAG integration. Capabilities: Wilson intervals (objective accuracy) and bootstrap intervals (expert dimensions), SFT/GRPO paired comparison, atomic GPTQ staging export, BM25/dense/structured multi-path retrieval, citation validation.

### Static Validation

Run all static checks and local logic tests from the repository root:

```bash
python iwind/validate_pipeline.py
```

The validator parses all Python and JSON files, checks that documentation and requirements are present, and runs the six module test suites. It does not download checkpoints or start training.

> **Note**: The training pipeline code is publicly available. Model weights (`DeepSeek-R1-0528-Qwen3-8B`, `QRM-Llama3.1-8B-v2`) and domain-specific reinforcement learning training scripts are not yet open-sourced, as described in Section 6.


## 9. License

Licensed under the **MIT License**.

```
Copyright (c) 2026 ZJU
```
