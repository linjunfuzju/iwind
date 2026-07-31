#  Iwind Simulation Services

This directory contains the computational backends and specialized simulation environments that power the Iwind agent's physics-informed reasoning. To maintain structural integrity and system security, these services are encapsulated as isolated microservices.

## Architecture Overview

Each service within this directory is designed to handle specific structural analysis tasks—ranging from multi-body dynamics to nonlinear finite element analysis. The Iwind agent interacts with these servers through standardized API protocols, ensuring a decoupled and secure execution environment.

1. DeepWind (User Interface & Orchestration) The primary gateway for the Iwind platform, managing the frontend interaction and orchestrating tool-calling sequences.

- Port: 8009
- Execution: python3 flask_app.py

1. Specialized Simulation Backends The following services provide high-fidelity physical simulations. Note: To protect proprietary methodology and intellectual property, the internal source code and specific implementation logic for these solvers are currently not public.

ZWind Server A proprietary multi-body dynamics solver developed by Zhejiang University and optimized for offshore wind turbine load analysis.

- Role: High-fidelity load prediction and fatigue analysis.
- Access: Managed via internal Model Context Protocol (MCP) gateway.
- Status: Private Implementation (Access via /app/tool/zwind).

OpenFAST Server

An encapsulated environment for the NREL OpenFAST whole-turbine simulation tool.

- Role: Multi-physics aero-hydro-servo-elastic simulation.
- Interface: REST API at Port 8002.
- Deployment: Local Docker Container (proprietary configuration).

OpenSees Server A specialized server for the OpenSees framework, focused on structural nonlinear dynamic analysis, such as seismic response.

- Role: Foundation and structural failure mechanism modeling.
- Interface: REST API at Port 8001.
- Status: Secure Backend Execution.

Deployment via Docker

The simulation environment is containerized to ensure consistency and prevent environment leakage. While implementation details are restricted, authorized users can deploy the service containers using the provided Docker configurations:

cd /servers/[service-name]-server

sudo docker-compose up -d --build

Security & Intellectual Property Notice

The analytical cores contained within this directory involve confidential algorithms and domain-specific knowledge belonging to HICAI-ZJU.

- Internal Details: The core solvers are pre-compiled or obfuscated within the production containers to prevent unauthorized reverse engineering.
- API Use: External researchers are encouraged to interact with these services exclusively through the Iwind Agent interface or the documented API endpoints.

Copyright (c) 2026 ZJU. All rights reserved.