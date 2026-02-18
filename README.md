# 🛠️ Multi-Agent CAD Framework

An autonomous, multi-agent system designed to transform natural language requirements into high-fidelity 3D CAD models. This framework leverages **LangGraph** for agent orchestration, **PythonOCC** library for the geometry engine, and **Streamlit** for a real-time 3D visual feedback loop.



## 🌟 Overview

This project implements a "human-in-the-loop" CAD factory where specialized AI agents collaborate to design, code, and verify mechanical parts. It moves beyond simple text generation by executing code in a sandboxed environment and performing visual audits of the results.

### The Agent Squad:
* **The Architect**: Analyzes user intent, breaks down complex geometry into logical steps, and maintains the project roadmap.
* **The Coder**: Translates architectural plans into precise PythonOCC scripts.
* **The Executor**: A headless worker that renders models, captures 2D views for the UI, and exports high-resolution STL files.
* **The Inspector (Maverick)**: Performs visual QA by analyzing rendered views to ensure the model matches the original requirements.

---

## 🚀 Key Features

* **Autonomous 3D Modeling**: Generate complex geometries via natural language chat.
* **Integrated 3D Viewer**: Real-time visualization of generated STL models directly in the browser using Three.js and the STLLoader.
* **Visual QA**: Automated multi-angle screen captures (Isometric, Top, Front, Right) for immediate verification.
* **Robust State Management**: Uses a Postgres-backed checkpointing system (LangGraph) to allow for long-running design sessions and persistence.
* **High-Res STL Export**: Optimized triangulation logic via `write_stl_file` with configurable linear and angular deflection for smooth surfaces.

---

## 🏗️ Technical Architecture

The system operates on a cyclic graph where the model is refined until it passes both technical execution and user approval.



### The "Execution-Export" Pipeline
One of the core technical achievements of this framework is the **Atomic Render-Export** process. To ensure the 3D viewer stays in sync with the AI's code:
1.  **Isolation**: The Executor launches an isolated subprocess with a custom `PYTHONPATH`.
2.  **Serialization**: Utilizes `OCC.Extend.DataExchange` for high-speed binary STL serialization.

---

## 🛠️ Installation & Setup

### Prerequisites
* **Python 3.9+**
* **OpenCASCADE (PythonOCC)**
* **PostgreSQL**: For persistent agent memory and LangGraph checkpointer.

### Quick Start
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/EdamChaye/Multi-Agent-CAD-framework.git]
    cd CAD-Framework
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment:**
    Create a `.env` file in the root:
    ```env
    DB_URI=postgresql+psycopg://user:password@localhost:5432/cad_db
    CAD_PYTHON_EXE=path_to_pythonOCC_environment
    GROQ_API_KEY=your_key_here
    ```
4.  **Launch the Framework:**
    ```bash
    streamlit run app.py
    ```

---

## 📂 Project Structure

* `src/graph.py`: The "brain" — defines the LangGraph state machine and agent routing.
* `src/nodes/`: Contains the logic for the Architect, Coder, Executor, and Inspector.
* `src/config.py`: Centralized path and environment management.
* `docs/visual_qa/`: Storage for the `latest_model.stl` and Maverick's camera shots.
* `temp/`: The sandbox where the AI's code is safely executed and tested.

---

## 🛡️ Troubleshooting
* **Viewer Caching?** The Streamlit UI uses a dynamic file-modification-time key to force-refresh the 3D viewer whenever a new model is generated.

---

## 🚀 Future Roadmap & Improvements

The Multi-Agent CAD Framework is an evolving ecosystem. Future development focuses on increasing geometric complexity, reducing latency, and enhancing spatial reasoning capabilities.

### 👁️ Multimodal Input Integration
* **Vision-to-CAD**: Implement capabilities for users to upload sketches, hand-drawn blueprints, or reference photos alongside text prompts.
* **Visual Grounding**: Enabling the Architect agent to "see" and reference specific features in the uploaded images to generate precise constraints.

### 🧠 Enhanced Spatial Reasoning & LLM Upgrades
* **LLM Scaling**: Transitioning the **Coder** and **Inspector** agents to more powerful llms (e.g., Open-AI and Google models) to better handle 3D spatial reasoning.
* **Structural Logic**: Improving the Inspector’s ability to detect structural configuration errors and non-manifold geometry before the user sees the model.
* **Industrial Complexity**: Moving beyond primitive shapes to support advanced industrial features like complex lofts, swept surfaces, and assembly-level logic.

### ⚡ Performance Optimization
* **Removing the Throttler**: Optimizing token usage and implementing local LLM inference options (via Ollama or vLLM) to remove artificial cooldown periods and allow for rapid-fire iterations.


### 📊 Efficiency & Success Metrics
* **CAD-Score**: Implementing a custom metric to measure the "Geometric Accuracy" (code output vs. initial requirements).
* **Iteration-to-Success (ITS)**: Tracking the average number of loops required between the Architect and Coder to reach a "Confirm" state.
* **Token Efficiency**: Measuring the cost-to-model ratio to ensure the system is economically viable for industrial production.

---