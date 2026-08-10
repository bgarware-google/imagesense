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

## ☁️ Deploying to Google Cloud Run

Image Studio is pre-configured with a production-ready `Dockerfile` and optimized for Google Cloud Run serverless container hosting.

### 1. Prerequisites
- Google Cloud Platform account with **Cloud Run**, **Cloud Build**, and **Vertex AI** APIs enabled:
  ```bash
  gcloud services enable run.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com
  ```
- Authenticate with GCP:
  ```bash
  gcloud auth application-default login
  ```

### 2. Deploy from Source
Run the following command from the `ImageStudio/` directory:

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
├── app.py                  # Standalone production Gradio web application
├── ImageStudio.ipynb       # Interactive Jupyter Notebook version
├── Dockerfile              # Production container definition for Cloud Run
├── .dockerignore           # Container build exclusion rules
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variable template
├── fonts/                  # TrueType fonts (Arial, Bold, Black, Italic, Narrow)
├── tmp/                    # Thread-safe runtime buffer directory (auto-cleaned)
└── README.md               # Documentation and deployment guide
```

---

## 👤 Author
* **Bhushan Garware**

