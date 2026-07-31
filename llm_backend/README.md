## Simulation Engine Deployment

Iwind acts as a central orchestrator that communicates with various physics engines deployed as microservices. Each engine is encapsulated within a Docker container and accessed via specific tool-calling endpoints.

#### **DeepWind (Frontend)**

The primary user interface for the Iwind platform.

- **Source Code Status**: The compiled frontend assets are located in the `static/` directory. **Note: Due to the ongoing patent application process, the raw frontend source code is currently restricted to protect unique UI/UX logic and integrated visualization algorithms.** Full access will be granted upon patent publication.

### **DeepWind (Frontend)**

The primary user interface for the Iwind platform.

- **Launch Command**:

  ```
  python3 flask_app.py
  ```

- **Access Port**: `http://localhost:8009`

### **Openseespy**

Used for structural nonlinear dynamic analysis.

- **Request Endpoint (Agent)**: `/app/tool/opensees`

- **Server Endpoint**: `/servers/opensees-server`

- **Docker Deployment**:

  ```
  cd /servers/opensees-server
  sudo docker-compose up -d --build
  ```

- **Access Port**: `http://localhost:8001`

### **OpenFAST**

The NREL multi-physics simulation tool for wind turbines.

- **Request Endpoint (Agent)**: `/app/tool/openfast`

- **Server Endpoint**: `/servers/openfast-server`

- **Docker Deployment**:

  ```
  cd /servers/openfast-server
  sudo docker-compose up -d --build
  ```

- **Access Port**: `http://localhost:8002`

### **ZWind**

The proprietary multi-body dynamics software developed by Zhejiang University, integrated via the MCP protocol for high-fidelity load analysis.

- **Request Endpoint (Agent)**: `/app/tool/zwind`

- **Server Endpoint**: `/servers/zwind-server`

- **Docker Deployment**:

  ```
  cd /servers/zwind-server
  sudo docker-compose up -d --build
  ```

- 

  **Access Port**: `http://localhost:8003` (or as defined in your local MCP config) 

------

## 5. Usage via Dialogue (The ReAct Loop)

The agent autonomously orchestrates these tools based on the conversation context. You do not need to call these endpoints manually; simply interact with the agent.

**Example Interaction**:

- **User**: "Analyze the tower response of WT-4 during Typhoon Yagi." 
- **Agent Logic**:
  - **Thought**: I need to perform a structural dynamic analysis using the reconstructed typhoon wind field.
  - **Action**: Automatically calls the **ZWind** tool via the `/app/tool/zwind` endpoint.
  - **Observation**: Receives stress profiles showing values exceeding 355 MPa at a 20m height.
  - **Response**: "Tower failure predicted at 20m due to buckling. Implementing a **W-shaped** yaw/pitch countermeasure is recommended." 