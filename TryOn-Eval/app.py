from pathlib import Path
import gradio as gr

from vto.virtual_try_on import perform_vto_with_eval
from vto.agentic_vto import run_agentic_try_on_loop



IMAGE_WIDTH = 500
IMAGE_HEIGHT = 530

css = """
body {
    font-family: 'Poppins', sans-serif;
    background-color: #F0F4F8;
    color: #2596be;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    text-align: center;
    background-color: #4F47E6;
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 30px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
"""

with (gr.Blocks(theme=gr.themes.Soft(), css=css) as demo):
    # Header
    gr.HTML("""
        <div class='header' style='display:flex;align-items:center;justify-content:center;gap:14px;'>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" fill="url(#gemGrad)"/>
              <defs>
                <linearGradient id="gemGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#8AB4F8"/>
                  <stop offset="50%" stop-color="#C58AF9"/>
                  <stop offset="100%" stop-color="#F28B82"/>
                </linearGradient>
              </defs>
            </svg>
            <div>
              <h2 style='margin:0;'>Agentic VTO: AutoEval & Self-Heal</h2>
              <p style='margin:4px 0 0 0;opacity:0.9;'>Instantly visualize new outfits and get AI-powered feedback on pose similarity and garment attribute consistency.</p>
            </div>
        </div>
        """)

    # Main VTO Flow
    with gr.Row(equal_height=True):
        # PERSON
        with gr.Column(scale=1):
            gr.Markdown("### 1. Upload Person")
            person_image = gr.Image(
                type="pil",
                label="Person Image",
                width=IMAGE_WIDTH,
                height=IMAGE_HEIGHT
            )

        # GARMENT
        with gr.Column(scale=1):
            gr.Markdown("### 2. Upload Garment")
            garment_image = gr.Image(
                type="pil",
                label="Garment Image",
                width=IMAGE_WIDTH,
                height=IMAGE_HEIGHT
            )

        # VTO Output
        with gr.Column(scale=1, visible=True) as vto_output_col:
            gr.Markdown("### 3. VTO Result")
            vto_output_image = gr.Image(
                label="Virtual Try-On Output",
                width=IMAGE_WIDTH,
                height=IMAGE_HEIGHT
            )

    # Examples
    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            gr.Examples(
                examples=[str(p) for p in Path("assets/sample_images/person").iterdir()],
                inputs=person_image,
                label="Person Examples"
            )

        with gr.Column(scale=1):
            gr.Examples(
                examples=[str(p) for p in Path("assets/sample_images/garments").iterdir()],
                inputs=garment_image,
                label="Garment Examples"
            )

        with gr.Column(scale=1):
            gr.Markdown()

    # VTO action buttons
    with gr.Row():
        clear_button = gr.Button("Clear", variant="secondary", scale=1)
        vto_button = gr.Button("Perform Virtual Try-On", variant="primary", scale=1)

    # EVALUATION
    with gr.Column(visible=True) as eval_output_group:
        gr.Markdown("---")
        gr.Markdown("## Evaluation Details")
        with gr.Row(equal_height=False):
            with gr.Column(scale=1):
                gr.Markdown("### Pose Comparison")
                similarity_score = gr.Label(label="Similarity Score", container=True)
                pose_output_image = gr.Image(
                    label="Pose Visualization",
                    interactive=False,
                    width=IMAGE_WIDTH,
                    height=IMAGE_HEIGHT
                )
            with gr.Column(scale=1):
                gr.Markdown("### Attribute Differences")
                json_output = gr.JSON(label="Evaluation Metrics")

    # AGENTIC ITERATIVE TRY-ON (VTO + NANO BANANA)

    with gr.Column(visible=True) as agentic_group:
        gr.Markdown("---")
        gr.Markdown("## 🤖 Agentic Iterative Try-On (VTO + Nano Banana)")
        gr.Markdown(
            "Runs an autonomous agentic loop alternating between **Virtual Try-On (`virtual-try-on-001`)** "
            "and **Nano Banana (`gemini-2.5-flash-image`)** until achieving:\n"
            "- **Pose Comparison Score > 0.90**\n"
            "- **Attribute Differences: None (0)**\n"
            "Each iteration improves the image and streams live progress below."
        )
        with gr.Row():
            agentic_max_iters = gr.Slider(
                minimum=1,
                maximum=7,
                value=4,
                step=1,
                label="Max Iterations",
                scale=1
            )
            agentic_online_mode = gr.Checkbox(
                value=True,
                label="Online Mode (Live API vs Static Output folder)",
                scale=1
            )
            agentic_run_button = gr.Button(
                "🚀 Start Agentic Try-On Loop (VTO + Nano Banana)",
                variant="primary",
                scale=2
            )

        agentic_status_table = gr.Markdown("### Click 'Start Agentic Try-On Loop' to begin iterative generation...")

        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                gr.Markdown("### Current Iteration Output Image")
                agentic_output_image = gr.Image(
                    label="Iteration Result (Updated Live)",
                    width=IMAGE_WIDTH,
                    height=IMAGE_HEIGHT
                )
            with gr.Column(scale=1):
                gr.Markdown("### Current Iteration Pose Comparison")
                agentic_similarity_score = gr.Label(label="Pose Similarity Score (>0.90 Target)", container=True)
                agentic_pose_image = gr.Image(
                    label="Pose Visualization (Updated Live)",
                    interactive=False,
                    width=IMAGE_WIDTH,
                    height=IMAGE_HEIGHT
                )
            with gr.Column(scale=1):
                gr.Markdown("### Current Iteration Attribute Differences")
                agentic_json_output = gr.JSON(label="Evaluation Metrics (Updated Live)")


        gr.Markdown("### 🖼️ Iteration Progression Gallery")
        agentic_gallery = gr.Gallery(
            label="Visual Improvements Across Iterations (Click any thumbnail to inspect)",
            show_label=True,
            columns=4,
            height=IMAGE_HEIGHT
        )
        agentic_gallery_metadata = gr.State([])

    # Button Click Event
    vto_button.click(
        fn=perform_vto_with_eval,
        inputs=[person_image, garment_image],
        outputs=[vto_output_image, similarity_score, pose_output_image, json_output]
    )

    def on_gallery_select(evt: gr.SelectData, metadata_list):
        if metadata_list and isinstance(metadata_list, list) and 0 <= evt.index < len(metadata_list):
            item = metadata_list[evt.index]
            return item.get("image"), item.get("similarity_score"), item.get("pose_img"), item.get("attributes", [])
        return None, None, None, None

    agentic_gallery.select(
        fn=on_gallery_select,
        inputs=[agentic_gallery_metadata],
        outputs=[agentic_output_image, agentic_similarity_score, agentic_pose_image, agentic_json_output]
    )

    agentic_nano_threshold_state = gr.State(0.75)
    agentic_run_button.click(
        fn=run_agentic_try_on_loop,
        inputs=[person_image, garment_image, agentic_max_iters, agentic_nano_threshold_state, agentic_online_mode],
        outputs=[
            agentic_status_table,
            agentic_output_image,
            agentic_similarity_score,
            agentic_pose_image,
            agentic_json_output,
            agentic_gallery,
            agentic_gallery_metadata,
        ]
    )

    clear_button.click(
        fn=lambda: (
            None, None, None, None, None, None,
            "### Click 'Start Agentic Try-On Loop' to begin iterative generation...",
            None, None, None, None, None, []
        ),
        inputs=None,
        outputs=[
            person_image,
            garment_image,
            vto_output_image,
            similarity_score,
            pose_output_image,
            json_output,
            agentic_status_table,
            agentic_output_image,
            agentic_similarity_score,
            agentic_pose_image,
            agentic_json_output,
            agentic_gallery,
            agentic_gallery_metadata,
        ]
    )



    with gr.Row():
        gr.Markdown(
            "Authors: "
            "[Darshan Barapatre](http://who/mrdarshan@google.com), "
            "[Bhushan Garware](http://who/bgarware), "
            "[Anibha Athalye](http://who/anibhaa)")

import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    demo.queue().launch(server_name="0.0.0.0", server_port=port)

