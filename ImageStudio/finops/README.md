# 📊 ImageSense FinOps & Telemetry Dashboard

This directory contains the Looker Studio dashboard configurations, BigQuery schema specifications, and SQL analytical views for real-time FinOps cost tracking, token consumption monitoring, and security audit analytics.

---

## 📈 Dashboard Key Performance Indicators (KPIs)

1. **💰 Total Spend & Run Rate (USD)**: Real-time cost breakdown across Vertex AI foundation models (Imagen 4, Gemini 2.5/3.1, Multimodal Embeddings), Cloud Vision API, and Cloud DLP.
2. **💵 Semantic Cache & Editing Cost Savings**: Total dollars saved by editing closest candidate assets ($\sim\$0.02$/edit) instead of generating 4 full variations from scratch ($\sim\$0.12$/generation).
3. **🔢 Token Consumption & Growth Trends**: Daily input prompt tokens and completion tokens consumed across users and departments.
4. **⚡ Latency & SLA Performance**: p50, p90, and p99 request latency benchmarks across features.
5. **🛡️ Security & Compliance Metrics**: Real-time counter of Cloud Armor prompt injection blocks, Cloud DLP PII redactions, and Cloud Vision SafeSearch flags.

---

## 🗄️ BigQuery Schema (`imagesense_telemetry.finops_telemetry_logs`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | `TIMESTAMP` | Execution UTC timestamp (Partitioned by Day) |
| `request_id` | `STRING` | Unique execution trace ID |
| `user_id` | `STRING` | Authenticated user email or service account (Clustered) |
| `feature` | `STRING` | Feature called (`image_generation`, `background_generation`, etc.) |
| `model_name` | `STRING` | Foundation model (`imagen-4.0-generate-001`, `gemini-2.5-flash-image`) |
| `prompt_tokens` | `INTEGER` | Input token count |
| `completion_tokens`| `INTEGER` | Output token count |
| `total_tokens` | `INTEGER` | Combined token consumption |
| `images_count` | `INTEGER` | Number of image variations produced |
| `latency_ms` | `FLOAT` | End-to-end processing latency in ms |
| `estimated_cost_usd`| `FLOAT` | Calculated cost in USD |
| `action_taken` | `STRING` | `EDIT_EXISTING`, `GENERATE_SCRATCH`, `SECURITY_BLOCKED` |
| `similarity_score` | `FLOAT` | Semantic cosine similarity score (0.0 - 1.0) |
| `pii_redacted` | `BOOLEAN` | Cloud DLP PII redaction trigger |
| `vision_safe` | `BOOLEAN` | Cloud Vision SafeSearch compliance |
| `status` | `STRING` | `SUCCESS`, `BLOCKED`, `ERROR` |

---

## 🚀 Setting Up Looker Studio Dashboard

### Step 1: Connect BigQuery to Looker Studio
1. Open [Looker Studio](https://lookerstudio.google.com/).
2. Click **Create** > **Data Source**.
3. Select **BigQuery** connector > Your GCP Project (`gdc-ai-playground`).
4. Choose Dataset `imagesense_telemetry` and View `v_finops_daily_summary`.

### Step 2: Dashboard Visual Components
* **Scorecards**:
  * `SUM(total_cost_usd)` -> Total Cloud Spend ($)
  * `SUM(estimated_savings_usd)` -> FinOps Savings from Vector Cache ($)
  * `SUM(total_tokens_consumed)` -> Total Tokens Consumed
  * `SUM(total_requests)` -> Total Executions
* **Time Series Charts**:
  * Daily Cost ($) & Token Volume over time.
* **Bar Charts**:
  * Spend by User / Service Account (`v_finops_user_breakdown`).
  * Cost by Model (`imagen-4.0` vs `gemini-2.5-flash-image`).
* **Pie Chart**:
  * Action Distribution (`EDIT_EXISTING` vs `GENERATE_SCRATCH`).
* **Security Table**:
  * Real-time audit log of PII redactions and security blocks.
