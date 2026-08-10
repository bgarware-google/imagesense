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
├── deployment/
│   └── cloud-armor-ingress/
│       ├── main.tf                     # Terraform IaC for Cloud Armor & Load Balancer
│       ├── iam.tf                      # Dedicated Service Accounts & WIF configuration
│       └── deploy-ingress.sh           # Automated Cloud Armor provisioning script
└── README.md                           # Documentation and deployment guide
```

---

## 👤 Author
* **Bhushan Garware**

