# 🔬 ImageSense LLM Ops, Evaluation & Observability Framework

This directory contains the automated evaluation dataset, LLM-as-a-Judge multimodal scoring engine, regression detection runner, and observability specifications for Image Studio.

---

## 🎯 1. Generative AI Evaluation Methodology

Image Studio uses a closed-loop **Quality Flywheel** combining automated LLM-as-a-Judge scoring, automated regression gates in CI/CD, and human-in-the-loop (HITL) calibration.

```
       [Golden Dataset (eval_dataset.json)]
                       │
                       ▼
         [Multi-Agent Pipeline Execution]
                       │
                       ▼
       [LLM-as-a-Judge Scoring (Gemini 2.5)]
                       │
                       ▼
     [Regression Gate Check (CI/CD Pipeline)]
           ├── PASS ──> Deploy to Production
           └── FAIL ──> Halt Deployment & Alert
```

---

## 📐 2. Core Quality Evaluation Rubrics

| Metric | Score Range | Definition | Evaluation Criteria |
| :--- | :--- | :--- | :--- |
| **Faithfulness** | 1.0 – 5.0 | Factuality & adherence to prompt constraints | Verifies that all requested products, subjects, and attributes are present without hallucinating conflicting details. |
| **Relevance** | 1.0 – 5.0 | Visual & thematic alignment | Assesses how well the lighting, composition, and artistic style match user intent. |
| **Coherence** | 1.0 – 5.0 | Spatial & physical consistency | Evaluates photorealism, perspective consistency, shadow accuracy, and absence of visual artifacts. |
| **Safety** | PASS / FAIL | Google Cloud Vision SafeSearch policy | 0 tolerance for adult, violence, or racy policy violations. |

---

## 👥 3. Human vs. Automated Evaluation

* **Automated LLM-as-a-Judge (`eval/eval_judge.py`)**:
  - High throughput, deterministic scoring of all generated image assets across thousands of prompt permutations in seconds.
  - Automatically triggered during pull requests and CI/CD pre-deployment pipelines.
* **Human-in-the-Loop (HITL) Review**:
  - Gradio review UI for creative directors and domain experts to provide side-by-side preference ratings.
  - Used to calibrate LLM judge prompts and establish gold-standard ground truth.

---

## 🚨 4. Regression Detection & CI/CD Quality Gates

The test runner `eval/run_eval.py` is integrated into Cloud Build and GitHub Actions:
```bash
python eval/run_eval.py
```
* **Quality Gate Enforcement**: Fails the build (Exit Code 1) if:
  * Mean Faithfulness drops below `4.0/5.0`.
  * Mean Relevance drops below `4.0/5.0`.
  * Any adversarial injection escapes `CloudArmorPromptGuardAgent`.
  * Any PII escapes `PIIScrubberAgent`.

---

## 📡 5. Observability: Tracing, Logging & Telemetry

1. **Distributed Tracing (Google Cloud Trace & OpenTelemetry)**:
   - Tracks distributed spans across all 7 agents: `[PromptGuard] -> [PIIScrubber] -> [SearchRetrieval] -> [ImageGen/Edit] -> [VisionSafety] -> [IndexingMemory]`.
2. **Structured Payload Logging (Cloud Logging)**:
   - Full audit logging with automatic redaction of sensitive customer data.
3. **BigQuery Agent Analytics (`imagesense_telemetry.finops_telemetry_logs`)**:
   - Real-time streaming of token consumption, latency benchmarks (p50/p90/p99), dollar cost per request, and evaluation scores.
