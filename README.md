# Iwind: Physics-Informed Wind Turbine Agent



**Iwind** is an autonomous intelligent agent framework designed for the structural analysis and disaster mitigation of offshore wind turbines. Unlike fragmented manual investigations, Iwind establishes a closed-loop engineering workflow that couples domain reasoning with the execution of high-fidelity simulations (such as **Zwind**, **OpenFAST**, and **OpenSees**) and multimodal field evidence interpretation.

By leveraging the **ReAct (Reasoning and Acting)** framework, the agent autonomously plans multi-step tasks, invokes specialized calculation tools, and reflects on observations to provide traceable engineering judgments.



## 1. Core Architecture

- **ReAct Loop**: Implements a "Thought-Action-Observation" cycle to solve engineering problems through dialogue-driven tool invocation.
- **Encapsulated Tools**: Automatically manages dozens of internal tools for load calculation, stress analysis, and structural responses.
- **Multimodal Perception**: Uses a dedicated `Detector` module (YOLOv5 & Qwen3-VL) to extract structured attributes from post-disaster imagery.
- **Hybrid Intelligence**: Supports seamless switching between local **Ollama** deployments and online APIs (Deepseek/Qwen) for reasoning and planning.

## 2. Environment & Setup

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
git clone https://github.com/xzpAM/iwind.git
cd Iwind
pip install -r requirements.txt
cd llm_backend
pip install -r requirements.txt
```

## 3. Configuration

All system parameters are managed in `llm_backend/.env`. The agent uses these settings to determine which local or online service to call during its reasoning process.

#### **Accessing the Models**

Currently, the system is configured to interface with the fine-tuned Iwind models via the local Ollama service.

**Note on Weights and Training Code:** To ensure the integrity of the ongoing peer-review process and to protect proprietary intellectual property related to the offshore wind power failure analysis methodology, the specific model weights and the domain-specific reinforcement learning (RL) training scripts are currently restricted. These assets are undergoing final verification and legal compliance checks.

We are committed to open science and plan to release the full model weights and training pipeline to the research community following the official publication of the associated research paper and the completion of our commercial licensing evaluation.

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

## 4. Running the Agent

The Iwind system is fully encapsulated. Once the backend is launched, all simulations and calculations are performed automatically through agent dialogue.

### Start the System

```
cd llm_backend
python run.py
```

### Usage via Dialogue

The agent autonomously calls its internal simulation and calculation tools based on the conversation context.

**User Question**: "Simulate the foundation response of WT-7 under the 2011 East Japan Earthquake loads." 

**Agent Process**:

1. **Thought**: I need to retrieve seismic PGA data and WT-7's structural parameters from MySQL and Neo4j.
2. **Action**: Calls the internal `Zwind_Engine` tool via the automated interface.
3. **Observation**: Foundation cracks detected; tower remains stable (Strong Tower, Weak Foundation).
4. **Response**: Outputs a detailed report and recommends an **M-shaped** damping strategy.



## 5. License

Licensed under the **MIT License**. 

```
Copyright (c) 2026 ZJU
```