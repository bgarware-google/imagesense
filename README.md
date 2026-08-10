# 🎨 ImageSense: AI-Powered Creative Image Studio

ImageSense is an enterprise multimodal image generation, background synthesis, and creative product compositing suite powered by **Google Cloud Vertex AI** and Gradio.

---

## 📂 Repository Contents

* **`ImageStudio/`**: Complete web application, Jupyter notebook, Dockerfile, TrueType fonts, Cloud Armor Terraform configs, and source code.
* **`PRD.pdf`**: Product Requirements Document and architectural specifications.

---

## ☁️ Google Cloud Run & Ingress Security

### 1. Deploy Cloud Run Service
```bash
cd ImageStudio
agents-cli deploy --project YOUR_PROJECT_ID --region us-central1 --no-confirm-project
```

### 2. Provision Cloud Armor Ingress Protection
```bash
cd ImageStudio/deployment/cloud-armor-ingress
./deploy-ingress.sh YOUR_PROJECT_ID us-central1
```

For full setup and local development instructions, see [ImageStudio/README.md](ImageStudio/README.md).

---

## 👤 Author
* **Bhushan Garware**
