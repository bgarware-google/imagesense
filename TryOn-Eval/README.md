# Agentic VTO: AutoEval & Self-Heal


A comprehensive tool that not only performs a virtual try-on (VTO) but also provides a detailed, AI-powered evaluation of the results, focusing on pose consistency and garment attribute accuracy.

---

## 🌟 Overview

This application provides an end-to-end solution for virtual try-on and its subsequent analysis. While traditional VTO systems focus solely on generating an output image, **TryOn-Eval** goes a step further. It leverages multimodal AI to critically evaluate the generated image against the originals, offering valuable insights for model developers, fashion brands, and e-commerce platforms.

The core workflow is simple:
1.  **Upload:** Provide an image of a person and an image of a garment.
2.  **Generate:** The VTO model drapes the garment onto the person.
3.  **Evaluate:** The system automatically analyzes the output by:
    *   **Comparing Poses:** It calculates a similarity score between the original pose and the pose in the VTO image, visualizing the skeletons for easy comparison.
    *   **Analyzing Garment Attributes:** It uses a powerful multimodal LLM to compare the garment in the original photo to the one in the VTO result, checking for consistency in color, pattern, style, and other key attributes.

## 🛠️ Technology Stack

*   **Backend:** Python 3.12
*   **AI/ML Models:**
    *   Google Vertex AI: `virtual-try-on-001` for VTO.
    *   Google Vertex AI: `gemini-2.5-flash-image` (Nano Banana) for targeted image repair & pose alignment across iterations.
    *   Google Vertex AI: `gemini-3.5-flash` for attribute analysis and agentic decision planning.
    *   Google MediaPipe: `pose_landmarker_heavy` for pose estimation.
*   **Web Framework:** Gradio

## 🤖 Autonomous Agentic Try-On Loop (VTO + Nano Banana)

TryOn-Eval features an **Agentic Virtual Try-On Engine** with smart priority routing:
- **High Priority — Pose Fixes (`virtual-try-on-001`)**: Whenever the Pose Comparison Similarity Score is `<= 0.90`, fixing the pose takes highest priority and the agent routes to `virtual-try-on-001`.
- **Smart Garment Repair (`gemini-2.5-flash-image` / Nano Banana)**: Whenever Pose Comparison Score is `> 0.90` and garment attribute differences exist, the agent smartly routes to **Nano Banana**, passing strictly **two input images**—the **Target Garment Image** (`Image 1`) and the **Current VTO Generated Image** (`Image 2`), with the original Person Image removed—to repair garment attribute discrepancies directly on the VTO image without destabilizing pose.





At each iteration, an AI Agent evaluates:
1. **Pose Comparison Similarity Score** against the target threshold (> 0.90)
2. **Attribute Differences** against the target of zero differences (`[]`), enforcing strict inspection of:
   - **Color Fidelity**: Preventing any shift in hue, saturation, or shade between the target garment and VTO output.
   - **Side Mirroring & Orientation**: Preventing horizontal flipping or left/right inversion of asymmetric features (sleeves, straps, pockets, logos, slits).
   - **Accessory Exclusion Rule**: Completely ignores carried/worn accessories such as handbags, purses, bags, sunglasses, or jewelry during both evaluation and corrective prompt generation.

At the **prompt level**, the **Effective Recovery Prompt Engine (`craft_effective_recovery_prompt`)** dynamically learns corrective prompts directly from the **Garment Attribute Differences** of the previous iteration without hardcoded phrases:
- **Dynamic Learning Without Hardcoding**: Rather than static phrases, prompts extract exact attribute discrepancies (`sleeve length`, `neckline`, `fabric pattern`, `color shade`) detected in the previous evaluation.
- **Iteration Adaptation Strategy**: Subsequent iterations (`iteration >= 2`) use significantly different phrasing and heightened structural constraints to overcome persistent failures.
- **Tailored for Target Architecture**:
  - **For `virtual-try-on-001` (Diffusion/Recontext)**: Generates concise **10 to 15 word prompts** directly incorporating the hint learned from `difference` in the earlier iteration.


  - **For `gemini-2.5-flash-image` (Image-to-Image Editor)**: Generates localized, concrete visual diff edits referencing Image 1 (Person) and Image 2 (Garment).
- **Overall Champion Output Selection**: Upon completing all iterations (or reaching the target goals), the system automatically selects and presents the **Overall Champion Output**—the candidate image from across all completed iterations that achieved the highest Pose Comparison Similarity Score and lowest Garment Attribute Differences.
- **Monotonic Non-Degrading Pose Guarantee**: Keeps track of the Pose Score across all iterations. If a corrective prompt improves or maintains the pose score, its successful pose clause is retained and prepended to the next iteration's prompt alongside new corrective measures. If an iteration yields a degraded pose score, the input base reverts to the best non-degraded candidate so the pose score never degrades across iterations.










## 🚀 Getting Started
### 1. Clone the Repository
```bash 
git clone <repository-url> cd TryOn-Eval
```

### 2. Configure Your Project

Update the `config.yaml` file with your Google Cloud project and other details.

### 3. Local Installation & Run

**Install dependencies:**
```bash 
pip install -r requirements.txt
```

**Run the Google Cloud Creative Studio Web Application (Recommended):**
```bash
python server.py
```
Open `http://localhost:8080` in your browser for the full Google Cloud Creative Studio dark-theme web experience with real-time SSE streaming.

**Run the Gradio application:**
```bash
python app.py
```

