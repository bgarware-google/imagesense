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

## 🌐 Multi-Zone Redundancy & Automated Failover

Image Studio is engineered for continuous high availability, automated zone-level failover, and strict disaster recovery SLAs:

### 1. 🚀 Compute Layer (Multi-Zone Cloud Run & Warm Provisioning)
* **3 Availability Zones**: Cloud Run microservices are deployed across 3 distinct availability zones in `us-central1` (`us-central1-a`, `us-central1-b`, `us-central1-c`).
* **Automatic Cross-Zone Traffic Balancing**: Serverless Network Endpoint Groups (NEGs) fronted by the Global External HTTPS Load Balancer dynamically distribute traffic across healthy zones with automatic instance health checks and zone-level failure eviction.
* **Warm Instance Provisioning**: Enforced minimum warm instances (`min_instance_count = 2` in production) eliminating cold starts for mission-critical batch and interactive image generation.

### 2. ⚡ Caching & State (Memorystore for Redis HA & <30s Failover)
* **Standard High Availability (HA) Mode**: Memorystore for Redis provisioned in `STANDARD_HA` tier with automated cross-zone replication between Primary (`us-central1-a`) and Replica (`us-central1-b`) nodes.
* **< 30-Second Automated Failover**: Dual-node architecture with automatic health detection guaranteeing sub-30-second failover with zero data loss or session interruption.

### 3. 🛡️ Disaster Recovery (DR: RTO < 15min, RPO < 5min)
* **Explicit SLAs**: Formally engineered and verified for **Recovery Time Objective (RTO) < 15 minutes** and **Recovery Point Objective (RPO) < 5 minutes**.
* **GCS Multi-Region Dual-Bucket Replication**: Continuous cross-region synchronization from Primary artifact storage (`us-central1`) to Secondary Disaster Recovery bucket (`us-east1`) via Google Cloud Storage Transfer Service (`google_storage_transfer_job`) with object versioning and Turbo Replication.
* **Reproducible Infrastructure-as-Code**: Entire multi-region stack is defined declaratively in Terraform (`deployment/terraform/`), enabling instant 1-command environment spin-up in alternative disaster recovery regions.

---

## 🛡️ Reliability & Resilience Engineering

Image Studio is architected in accordance with Google Cloud SRE and enterprise distributed systems resilience principles:

### 1. 📐 Availability Design & Service Level Objectives (SLOs/SLAs)
* **High Availability SLA Target**: **99.95% availability** (<21.9 minutes of allowed downtime per month) backed by multi-zone Cloud Run (`us-central1-a, b, c`), Memorystore Redis HA, and multi-region GCS.
* **Latency SLOs**:
  * **p50 Latency**: $< 1.5\text{s}$ for vector-cached retrieval and closest-candidate multimodal delta editing.
  * **p90 Latency**: $< 4.0\text{s}$ for parallel 4-variation Imagen 4 synthesis.
  * **p99 Latency**: $< 8.0\text{s}$ for the complete end-to-end multi-agent pipeline (Security Guard $\rightarrow$ DLP $\rightarrow$ Search $\rightarrow$ Generation $\rightarrow$ Vision Safety $\rightarrow$ BigQuery FinOps).
* **Distributed Systems Consistency Models**:
  * **Eventual Consistency**: Vector datastore embeddings, Discovery Engine document sync, and BigQuery analytical telemetry streams.
  * **Strong Consistency**: Cloud KMS CMEK encryption state, OAuth 2.0 / OIDC IAM claims, and Cloud Armor security policy enforcement.
* **Secure Inter-Service Communication**: Encrypted over TLS 1.3 with Cloud Armor WAF and OAuth 2.0 / OIDC Bearer token authentication.

### 2. 🧪 Observability, Failure & Chaos Testing (`tests/resilience_and_chaos_test.py`)
Image Studio includes a dedicated automated chaos and failure injection testing suite:
* **Failure Injection**: Simulates Discovery Engine outages, Cloud DLP API network partitions, and transient 503/429 HTTP backpressure.
* **Red Teaming & Security Resilience**: Injects adversarial jailbreaks (DAN mode, instruction override, SQL injection) verifying deterministic blocking by `CloudArmorPromptGuardAgent`.
* **Disaster Recovery Validation**: Validates cross-region replication synchronization from primary (`us-central1`) to secondary DR storage (`us-east1`).
* **Runaway Loop Protection**: Verifies that recursive generation attacks trip the **$0.25 FinOps Circuit Breaker**, halting execution and logging a `CIRCUIT_BREAKER_TRIPPED` audit event.

### 3. ⚡ Graceful Degradation & Fault Tolerance
* **Multi-Tier Model Fallback**:
  * Discovery Engine Outage $\rightarrow$ Fallback to local Multimodal Vector Index (`multimodalembedding@001`) $\rightarrow$ Dense SHA-256 projection.
  * Imagen 4 Rate Limit (429) $\rightarrow$ Fallback to `imagen-3.0-generate-002` $\rightarrow$ Fallback to Gemini Multimodal synthesis (`gemini-2.5-flash-image` / `gemini-3.1-flash-image`).
* **Cloud DLP Failure Isolation**: Defense-in-depth regex de-identification fallback guarantees **0 PII leakage** even during total Cloud DLP service unavailability.
* **Exponential Backoff with Jitter**: Vertex AI and GCP API client calls utilize `@retry_with_backoff(max_retries=3, base_delay=0.5s, jitter=True)` to absorb transient network spikes and rate limits.
* **Timeout Handling**: Strict per-candidate 10-second timeout thresholds prevent cascading thread exhaustion.

---

## ⚡ Performance & Cost Optimization Architecture

Image Studio is engineered to deliver maximum throughput, sub-second latency, and optimized cloud economics:

### 1. 🚀 Scalability & Elasticity
* **Horizontal & Vertical Autoscaling**: Cloud Run services automatically scale horizontally between 1 and 20 instances based on concurrency thresholds (`max_instance_request_concurrency = 40`), provisioned with 4 vCPUs and 8 GiB RAM per instance with dedicated CPU allocation (`cpu_idle = false`) for deterministic latency.
* **Global Load Balancing & Serverless NEGs**: Fronted by a Google Cloud External HTTPS Application Load Balancer with Serverless Network Endpoint Groups (NEGs) and Cloud Armor DDoS mitigation.
* **High-Throughput API Concurrency**: Image generation executes 4 parallel threads per prompt. Asynchronous batch workloads are decoupled through Cloud Pub/Sub queues (`imagesense-batch-jobs`) for non-blocking execution.
* **HPC & GPU Cluster Scaling**: Integrated GKE Autopilot node pools with **NVIDIA L4 GPUs (`g2-standard-4`)** for GPU-accelerated segmentation (`rembg` / ONNX TensorRT) during large-scale catalog processing.

### 2. 💡 Resource Efficiency & Spot/Preemptible Compute
* **Workload-Specific Right-Sizing**: Web ingress and API routing run on lightweight CPU-optimized serverless containers, while heavy batch rendering is offloaded to GPU worker nodes.
* **Spot / Preemptible GPU Pools**: Batch rendering node pools utilize GKE Spot instances (`spot = true`), reducing underlying compute infrastructure expenses by **60% to 80%** compared to standard on-demand pricing.

### 3. 💰 AI Cost Management & Token Optimization
* **Tiered Model Selection Trade-offs**:
  * **Image Refinement & Editing**: Routed to Gemini 2.5 Flash Image ($\sim\$0.02$/image) for cost-effective multimodal delta edits.
  * **Novel Synthesis**: Routed to Imagen 4 (`imagen-4.0-generate-001`) ($\sim\$0.03$/image) when zero matching assets exist.
* **Semantic Caching & Vector Reuse (83% Cost Reduction)**:
  * By searching the datastore before generating, matching assets ($\ge 70\%$ similarity) are edited directly instead of synthesizing 4 images from scratch.
  * **Cost Impact**: Reduces per-request generation cost from **$\sim\$0.12$** down to **$\sim\$0.02$** (**83% savings**).
* **Token Optimization & Context Management**:
  * Structured prompt enrichment enriches only essential visual descriptors (Subject, Action, Environment, Lighting, Quality), eliminating prompt bloat.
  * Cloud DLP tokenization maintains minimal token footprint.
  * In-memory LRU font caching and local vector index memory reduce redundant remote roundtrips.

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
│   ├── cloud-armor-ingress/
│   │   ├── main.tf                     # Terraform IaC for Cloud Armor & Load Balancer
│   │   ├── iam.tf                      # Dedicated Service Accounts & WIF configuration
│   │   ├── cmek.tf                     # Cloud KMS CMEK encryption & persistent storage
│   │   ├── redis_ha.tf                 # Memorystore for Redis HA & <30s failover
│   │   ├── disaster_recovery.tf        # GCS Dual-Bucket replication (RTO<15m, RPO<5m)
│   │   ├── audit_logging.tf            # Cloud Audit Logging for SOC 2 / ISO 27001
│   │   ├── bigquery_finops.tf          # BigQuery Telemetry Table & Looker Views
│   │   ├── gke_spot.tf                 # GKE Spot GPU cluster for batch rendering
│   │   └── deploy-ingress.sh           # Automated Cloud Armor provisioning script
│   ├── cloudbuild-security-scan.yaml   # CI/CD Policy-as-Code (checkov, tfsec, tflint)
│   └── terraform/                      # 7 Decoupled Modules & Dev/Prod Environments
│       ├── environments/
│       │   ├── dev/                    # Development Environment (us-central1)
│       │   └── prod/                   # Production Environment (us-central1 HA)
│       └── modules/                    # Decoupled domains (compute, cache, storage, etc.)
├── tests/
│   └── resilience_and_chaos_test.py    # Chaos, failure injection & resilience test suite
└── README.md                           # Documentation and deployment guide
```

---

## 👤 Author
* **Bhushan Garware**

