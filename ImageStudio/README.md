# 🎨 Image Studio

Image Studio is an end-to-end suite for AI-powered image generation, background synthesis, product placement, watermark/logo insertion, and typography rendering.

---

## 🚀 Getting Started Locally

### 1. Prerequisites
- **Python 3.10+** (Python 3.11 / 3.12 recommended)
- **Google Cloud Platform Account** with Vertex AI API enabled (for Imagen 3 & Gemini prompt enrichment)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated

---

### 2. Environment Setup

#### Option A: Using `uv` (Recommended - fast)
```bash
cd ImageStudio
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

#### Option B: Using standard `venv` & `pip`
```bash
cd ImageStudio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 3. Google Cloud Authentication & Configuration

1. **Log in to Google Cloud**:
   ```bash
   gcloud auth application-default login
   ```

2. **Configure your `.env` file**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your GCP Project ID:
   ```env
   GOOGLE_CLOUD_PROJECT=your-actual-gcp-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   PORT=8080
   ```

---

### 4. Running the Application Locally

#### Method 1: Run as a Standalone Web Application
```bash
python app.py
```
Open your browser at `http://localhost:8080`.

#### Method 2: Run via Jupyter Notebook
Start JupyterLab / Notebook:
```bash
jupyter lab ImageStudio.ipynb
# or
jupyter notebook ImageStudio.ipynb
```
Run all cells in `ImageStudio.ipynb`. The Gradio interface will launch inside the notebook as well as provide a local URL (`http://localhost:8080`).

---

## 🛠️ Features & Tabs Overview

1. **✨ Image Generation**:
   - Compose rich prompts with Subject, Action, Theme, Lighting, and Quality modifiers.
   - Enriched using Gemini (`gemini-1.5-flash`) on Vertex AI.
   - Generates 4 high-fidelity images using Google's **Imagen 3** model.

2. **🖼️ Background Generation**:
   - Upload any product image and describe a target scene/background.
   - Uses Vertex AI Imagen product-editing capability to generate 3 contextual background variations.

3. **✂️ Insert Image (Compositing)**:
   - Upload a base background and a foreground product.
   - Background removal is automatically performed via `rembg`.
   - Adjust scale, rotation angle, and XY placement coordinates.
   - Chain multiple insertions onto the same canvas with "Insert Another Product".

4. **🏷️ Insert Logo**:
   - Add logos or watermarks with customizable scaling factor (0.1x - 5x) and opacity (0% - 100%).
   - Position branding precisely at custom XY coordinates.

5. **✍️ Insert Text**:
   - Render ad headlines, marketing callouts, and banners.
   - Supports bundled and system TrueType fonts (`Arial`, `Impact`, etc.), font size, RGB color pickers, and XY positioning.

---

## 📁 Directory Structure
```
ImageStudio/
├── app.py                  # Standalone Gradio application
├── ImageStudio.ipynb       # Jupyter Notebook version
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variable template
├── fonts/                  # TrueType fonts for text rendering
├── tmp/                    # Temporary working directory for image buffers
└── README.md               # Setup and usage guide
```
