# 🎨 ImageSense: AI-Powered Creative Image Studio

ImageSense is an enterprise multimodal image generation, background synthesis, and creative product compositing suite powered by **Google Cloud Vertex AI** and Gradio.

---

## 📂 Repository Contents

* **`ImageStudio/`**: Complete web application, Jupyter notebook, Dockerfile, TrueType fonts, and source code.
* **`PRD.pdf`**: Product Requirements Document and architectural specifications.

---

## ☁️ Google Cloud Run Deployment

Deploy `ImageStudio` directly from source with a single command:

```bash
cd ImageStudio

gcloud run deploy image-studio \
  --source . \
  --region us-central1 \
  --project YOUR_PROJECT_ID \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1
```

For full setup and local development instructions, see [ImageStudio/README.md](ImageStudio/README.md).
