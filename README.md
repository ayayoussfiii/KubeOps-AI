
KubeOps-AI: Intelligent Log Analysis & Remediation

 Overview

KubeOps-AI is an applied research Proof of Concept (PoC) designed to bridge the gap between retrospective root-cause analysis and prospective system remediation.

By analyzing highly heterogeneous and noisy digital traces (event logs), KubeOps-AI couples Graph Neural Networks (GNNs) with Agentic Large Language Models (LLMs). It reconstructs behavioral models from raw IT logs, identifies the root causes of system failures, and automatically generates reliable, uncertainty-calibrated remediation strategies.

 Key Features

Causal Graph Extraction: Transforms raw, noisy event logs (e.g., GAIA datasets) into structured behavioral graphs.

GNN-Based Root Cause Analysis: Utilizes PyTorch Geometric to traverse spatial and topological data, pinpointing anomalies retrospectively.

Agentic Orchestration: Employs LangGraph to manage intelligent agents that coordinate the extraction, analysis, and generation pipelines.

LLM Fine-Tuning (QLoRA): Integrates parameter-efficient fine-tuned LLMs to understand complex IT contexts and generate prospective corrective patches.

Explainable AI (XAI) & Uncertainty Calibration: Leverages Conformal Prediction via the MAPIE library to evaluate the statistical uncertainty of the generated predictions, ensuring high reliability for decision support.

Tech Stack

Core: Python

Deep Learning / GNN: PyTorch, PyTorch Geometric

Generative AI / Orchestration: LangGraph, Hugging Face Transformers, QLoRA

Explainability (XAI): MAPIE (Conformal Prediction)

Data Processing: Pandas, NetworkX

 Quick Start

Prerequisites

Python 3.10 or higher

CUDA-enabled GPU (Highly recommended for GNN and LLM inference/fine-tuning)

Installation

Clone the repository:

git clone https://github.com/ayayoussfiii/KubeOps-AI.git
cd KubeOps-AI


Create a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`


Install dependencies:

pip install -r requirements.txt


 Dataset

This project utilizes datasets inspired by the GAIA (Graph-based Artificial Intelligence Analysis) IT operations logs. Due to privacy and size constraints, raw datasets are not included in this repository.

Place your formatted .csv or .json log files in the data/raw/ directory before running the pipeline.

 Pipeline Architecture

Data Ingestion: Parses noisy as-is event logs.

Graph Construction (NetworkX -> PyG): Builds nodes (events) and edges (temporal/causal links).

GNN Inference: Detects sub-graph anomalies.

LangGraph Agents:

Analyzer Agent: Summarizes the GNN anomaly.

Remediation Agent: Uses QLoRA fine-tuned LLM to propose a to-be fix.

Uncertainty Output: MAPIE wraps the prediction to provide a confidence interval (Conformal Prediction).

 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to check the issues page.





Built as part of an applied research engineering project.
