# 🎨 Image Studio

Image Studio is an enterprise-grade suite for AI-powered image generation, background synthesis, product placement, watermark/logo overlay, and typography rendering powered by **Google Cloud Vertex AI** (Imagen 4, Gemini 2.5/3.1 Flash Image) and Gradio.

---

## 🌟 Key Features

1. **✨ Image Generation (4 Variations in Parallel)**:
   - Enriches prompt inputs (Subject, Action, Environment, Lighting, Quality Modifiers) using Vertex AI Gemini models.
   - Generates 4 high-fidelity images simultaneously via multi-threaded concurrent requests (`gemini-2.5-flash-image`, `imagen-4.0-generate-001`).

2. **🖼️ Background Generation & Scene Synthesis**:
   - Seamlessly isolates foreground products and creates contextual, photorealistic background variations.
   - Dual-engine fallback: Vertex AI Imagen capability models + Gemini Multimodal scene synthesis (`gemini-2.5-flash-image`).

3. **✂️ Insert Image (Compositing & Auto-Segmentation)**:
   - Automatic background removal on uploaded products powered by `rembg` (U2Net ONNX).
   - Precise affine transformations: resize, rotate, and pixel-accurate XY placement.
   - Chaining workflow: composite multiple products sequentially onto the same canvas.

4. **🏷️ Insert Logo & Watermarking**:
   - Overlay brand watermarks with adjustable scale multiplier (0.1x - 5.0x) and alpha transparency (0% - 100%).

5. **✍️ Typography & Marketing Copy**:
   - Render ad copy, discount badges, and headlines with bundled TrueType fonts, LRU font cache, and full RGB color controls.

6. **🔍 Vertex AI Search (Discovery Engine) & Multimodal Vector Retrieval**:
   - **Vertex AI Search (Discovery Engine)**: Native connector (`google.cloud.discoveryengine_v1.SearchServiceClient`) to search and retrieve image documents from Discovery Engine structured/unstructured Data Stores.
   - **Multimodal Dense Embeddings**: Generates 1408-dimensional vector embeddings via Vertex AI `multimodalembedding@001`.
   - **Semantic Pre-Generation Search**: Automatically searches the asset datastore for similar prompts/images (>= 70% cosine similarity) before generating.
   - **Closest-Candidate Image Refinement**: If a match exists, edits and refines the existing candidate image directly instead of synthesizing from scratch.
   - **Continuous Auto-Indexing**: All newly generated and edited visual assets are indexed into the datastore and Discovery Engine for instant subsequent retrieval and iterative refinement.

---

## 🤖 Multi-Agent Collaborative System Architecture

Image Studio coordinates an autonomous multi-agent pipeline orchestrated by the **`ImageSenseMultiAgentOrchestrator`**:

1. **🛡️ Cloud Armor Prompt Guard Agent (`CloudArmorPromptGuardAgent`)**:
   - Analyzes incoming prompts against Cloud Armor / Model Armor rules, blocking prompt injection, jailbreaks (e.g. DAN mode, system prompt override), and exploit payloads.
2. **🔒 Cloud DLP PII Scrubbing Agent (`PIIScrubberAgent`)**:
   - Uses Google Cloud DLP (`dlp_v2`) and regex filters to automatically detect, mask, and redact sensitive personal information (names, emails, phone numbers, credit card numbers, SSNs, physical addresses, IP addresses).
3. **🔍 Search & Retrieval Agent (`SearchRetrievalAgent`)**:
   - Queries Vertex AI Search (Discovery Engine) and dense 1408-d Multimodal Embeddings (`multimodalembedding@001`).
   - If cosine similarity >= 70%, delegates to the **Image Editing Agent**; otherwise delegates to the **Image Generation Agent**.
4. **🎨 Image Editing Agent (`ImageEditingAgent`)**:
   - Takes the closest matching candidate image and executes targeted multimodal delta modifications via `gemini-2.5-flash-image`.
5. **✨ Image Generation Agent (`ImageGenerationAgent`)**:
   - Synthesizes 4 high-fidelity candidate images from scratch using Imagen 4 (`imagen-4.0-generate-001`) or Gemini Native Image models.
6. **👁️ Google Cloud Vision Safety Agent (`CloudVisionSafetyAgent`)**:
   - Performs automated vision safety moderation via Google Cloud Vision API (`SafeSearchDetection`), validating that no images contain adult, violence, or racy policy violations.
7. **💾 Continuous Indexing & Memory Agent (`IndexingMemoryAgent`)**:
   - Embeds and indexes all verified safe output images into the vector datastore and Discovery Engine data store for subsequent retrieval loops.

---

## 📊 BigQuery Telemetry, Token Tracking & Looker FinOps Dashboard

Image Studio automatically streams rich runtime execution telemetry, token consumption, and cost calculations asynchronously to **Google BigQuery** for real-time FinOps monitoring in **Looker Studio**:

### Streamed Telemetry Fields (`imagesense_telemetry.finops_telemetry_logs`):
* **Execution Identity & Timing**: `timestamp`, `request_id`, `user_id` (authenticated caller/service account), `client_ip`.
* **Token & Computation Metrics**: `prompt_tokens`, `completion_tokens`, `total_tokens`, `images_count`, `latency_ms`.
* **Cost & Model Attribution**: `model_name` (e.g. `imagen-4.0-generate-001`, `gemini-2.5-flash-image`), `estimated_cost_usd`.
* **Semantic Routing & Safety Auditing**: `action_taken` (`EDIT_EXISTING`, `GENERATE_SCRATCH`, `SECURITY_BLOCKED`), `similarity_score`, `pii_redacted`, `vision_safe`, `status`.

### Looker Studio FinOps Analytics:
* **Total Spend & Run Rate ($)**: Aggregated spend across Vertex AI Imagen, Gemini, Vision API, and Discovery Engine.
* **Semantic Cache Savings ($)**: Calculated dollar savings from editing closest matches ($\sim\$0.02$/edit) versus synthesizing from scratch ($\sim\$0.12$/generation).
* **Token Volume Trends**: User and department token consumption growth.
* **Security & Compliance Audits**: Real-time monitor of prompt injection blocks and Cloud DLP PII redactions.

---

## 🏛️ Compliance & Governance

Image Studio implements an enterprise compliance and governance framework across four critical operational pillars:

### 1. 💰 FinOps Governance & Session Budget Enforcement
* **Real-Time Streaming Telemetry**: Telemetry streaming directly into BigQuery tracking token consumption, compute cost, and latency per request.
* **Automated Circuit Breaker ($0.25 Cap)**: Programmed strict session budget guardrails with an automated circuit breaker capping individual session spend at **$0.25 USD**, halting execution when exceeded to prevent unbounded recursive execution loops and unexpected cloud charges.

### 2. 📋 Comprehensive Cloud Audit Logging (SOC 2, ISO 27001)
* **Complete Audit Coverage**: Enabled Admin Activity, Data Access, and System Event audit logs across all VPC-SC enclosed resources (`allServices`), creating tamper-proof audit trails for enterprise compliance (SOC 2, ISO 27001).
* **Immutable Storage Sink**: Configured dedicated audit log sink routing to CMEK-encrypted GCS buckets with 30-day retention locks (`retention_policy`).

### 3. 🔍 Policy-as-Code & Pre-Deployment Scanning
* **7 Decoupled Terraform Domains**: Declarative security standards partitioned across 7 decoupled Terraform domains (`networking`, `security`, `compute`, `storage`, `iam`, `messaging`, `cache`).
* **Automated CI/CD Scanning**: Integrated automated pre-deployment scanning via **`checkov`**, **`tfsec`**, and **`tflint`** in Cloud Build pipelines (`cloudbuild-security-scan.yaml`).

### 4. 🌍 Strict Regional Data Residency & Immutability
* **Strict Regional Pinning**: Enforced strict regional data residency pinned to **`us-central1`** across compute, storage, KMS, and Vertex AI workloads.
* **Zero Configuration Drift**: Fully parameterized `environments/dev/` and `environments/prod/` configurations ensuring zero configuration drift between development and production.

---

## 🔐 Authentication & Authorization

Image Studio enforces an enterprise security architecture adhering to zero-trust and least-privilege principles:

### Least-Privilege Dedicated Service Accounts
* **`sa-imagesense-api`**: Dedicated Ingress API service account with granular role bindings strictly scoped to:
  * `roles/aiplatform.user` — Execute Vertex AI foundation models (Imagen 4, Gemini 2.5/3.1).
  * `roles/storage.objectViewer` — Read assets and model weights from Cloud Storage.
  * `roles/logging.logWriter` — Stream structured audit and telemetry logs to Cloud Logging.
* **`sa-imagesense-worker`**: Asynchronous batch worker service account strictly scoped to:
  * `roles/pubsub.subscriber` — Pull asynchronous batch jobs from Pub/Sub topic queues.
  * `roles/bigquery.dataEditor` — Store analytical telemetry and batch job metrics in BigQuery.
  * `roles/secretmanager.secretAccessor` — Read runtime credentials and API secrets on demand.
  * `roles/logging.logWriter` — Write execution logs.

### OAuth 2.0 / OIDC & Keyless Federation
* **OIDC Bearer Token Authentication**: Enforced OAuth 2.0 / OIDC Bearer token authentication on the FastAPI ingress gateway for all `/api/v1/batch/*` and `/api/v1/jobs/*` endpoints. Incoming requests must supply a valid Google Cloud IAM / OIDC Bearer token verified against Google's public key infrastructure.
* **Workload Identity Federation (WIF)**: Integrated Workload Identity Federation (`imagesense-cicd-pool`) for automated CI/CD pipelines (Cloud Build / GitHub Actions), eliminating long-lived service account JSON keys in favor of short-lived federated STS tokens.

---

## 🔒 Data Protection & Privacy

### Managed Encryption Keys (Cloud KMS CMEK)
* **CMEK Across All Persistent Layers**: Enforced Customer-Managed Encryption Key (CMEK) encryption across all data storage layers:
  * **GCS Image Artifact Buckets** (`imagesense-artifacts-*`): All generated and uploaded images encrypted with dedicated CMEK key (`imagesense-gcs-cmek-key`).
  * **BigQuery Telemetry & Analytics**: Analytical logs, latency telemetry, and audit traces encrypted with `imagesense-bq-cmek-key`.
  * **Vertex AI Vector Search**: Embedding indices and vector metadata protected with `imagesense-vertex-cmek-key`.
* **Automated Key Rotation**: Automated 90-day (`7776000s`) crypto key rotation policy configured on the `imagesense-keyring` key ring.

### Automated PII Scrubbing via Cloud DLP
* **Sensitive Data Redaction**: Integrated Google Cloud Data Loss Prevention (Cloud DLP `dlp_v2`) pre-processing templates to automatically detect, mask, and redact Sensitive Data / PII (person names, emails, phone numbers, street addresses, credit card numbers, US SSNs, and IP addresses) from user prompts and metadata prior to LLM and Imagen model processing.
* **Defense-in-Depth Sanitization**: Coupled Cloud DLP inspection with high-performance regex de-identification fallback filters to ensure zero PII leakage during network interruptions.

---

## 🛡️ Ingress Security with Google Cloud Armor

Image Studio includes infrastructure configurations to front Cloud Run with **Google Cloud Armor** and an **External HTTPS Application Load Balancer**.

### Protections Enabled
* **Adaptive Layer 7 DDoS Defense**: Machine-learning backed traffic anomaly mitigation.
* **WAF OWASP Top 10 Core Rules**: Blocks Cross-Site Scripting (XSS), SQL Injection (SQLi), and protocol exploits.
* **Rate Limiting**: Enforces max 120 requests/minute per client IP to prevent quota abuse and brute force.
* **Scanner & Bot Detection**: Blocks automated vulnerability scanners.
* **Ingress Lockdown**: Cloud Run is configured with `--ingress=internal-and-cloud-load-balancing` so direct `.run.app` URLs are unreachable, forcing all ingress through Cloud Armor.

### Deploying Cloud Armor Ingress

#### Option 1: Automated Script
```bash
cd deployment/cloud-armor-ingress
./deploy-ingress.sh <YOUR_PROJECT_ID> <YOUR_REGION>
```

#### Option 2: Terraform (IaC)
```bash
cd deployment/cloud-armor-ingress
terraform init
terraform apply -var="project_id=YOUR_PROJECT_ID" -var="region=us-central1"
```

---

## ☁️ Deploying to Google Cloud Run

Image Studio is pre-configured with a production-ready `Dockerfile` and optimized for Google Cloud Run serverless container hosting.

### 1. Prerequisites
- Google Cloud Platform account with **Cloud Run**, **Cloud Build**, and **Vertex AI** APIs enabled:
  ```bash
  gcloud services enable run.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com compute.googleapis.com
  ```
- Authenticate with GCP:
  ```bash
  gcloud auth application-default login
  ```

### 2. Deploy from Source (Agent CLI or gcloud)

#### Using Agent CLI:
```bash
agents-cli deploy --project YOUR_PROJECT_ID --region us-central1 --no-confirm-project
```

#### Using gcloud CLI:
```bash
gcloud run deploy image-studio \
  --source . \
  --region us-central1 \
  --project YOUR_PROJECT_ID \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1
```

### 3. Resource Sizing Recommendations
- **CPU**: `2 vCPU` (recommended for responsive `rembg` ONNX neural network inference)
- **Memory**: `4 GiB` (handles high-resolution 4K PIL image alpha compositing and concurrent user requests)
- **Concurrency**: Cloud Run automatically scales instances based on incoming request traffic.

---

## 🚀 Running Locally

### 1. Environment Setup

#### Option A: Using `uv` (Fast)
```bash
cd ImageStudio
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

#### Option B: Standard Python `venv`
```bash
cd ImageStudio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your project configuration:
```env
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
PORT=8080
GRADIO_SHARE=false
```

### 3. Start the Web Application
```bash
python app.py
```
Open your browser at `http://localhost:8080`.

### 4. Running in Jupyter Notebook
```bash
jupyter lab ImageStudio.ipynb
```
Run all cells to launch the interactive Gradio interface directly inside Jupyter.

---

## 📁 Project Structure

```
ImageStudio/
├── app.py                              # Standalone production Gradio web application
├── ImageStudio.ipynb                   # Interactive Jupyter Notebook version
├── Dockerfile                          # Production container definition for Cloud Run
├── .dockerignore                       # Container build exclusion rules
├── agents-cli-manifest.yaml            # Google Agents CLI manifest
├── requirements.txt                    # Python package dependencies
├── .env.example                        # Environment variable template
├── fonts/                              # TrueType fonts (Arial, Bold, Black, Italic, Narrow)
├── tmp/                                # Thread-safe runtime buffer directory (auto-cleaned)
├── finops/
│   └── README.md                       # Looker Studio setup, schema, and KPI guide
├── deployment/
│   └── cloud-armor-ingress/
│       ├── main.tf                     # Terraform IaC for Cloud Armor & Load Balancer
│       ├── iam.tf                      # Dedicated Service Accounts & WIF configuration
│       ├── cmek.tf                     # Cloud KMS CMEK encryption & persistent storage
│       ├── bigquery_finops.tf          # BigQuery Telemetry Table & Looker Views
│       └── deploy-ingress.sh           # Automated Cloud Armor provisioning script
└── README.md                           # Documentation and deployment guide
```

---

## 👤 Author
* **Bhushan Garware**

