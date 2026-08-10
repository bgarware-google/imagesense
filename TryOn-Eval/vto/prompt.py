GARMENT_DIFF_ANALYSIS_PROMPT = """
You are evaluating the output of a **Virtual Try-On (VTO)** system. This system takes a product or garment image and applies it to a person image to generate a new image showing that person wearing the garment.

Your goal is to **identify all visual mistakes or unintended differences introduced by the VTO process**, using the **product image**, **person image**, and **VTO output image**.

---

### 🔍 Step 1: Garment Verification & Comparison

1. **Determine the Target Garment**:

 * Identify which garment from the product image is being applied via VTO.
 * The product image may show just the garment or a model wearing it.
 * If it's unclear, use the VTO output to help determine the correct target garment.

2. **Compare Target Garment Only**:

 * Focus only on garment parts clearly visible in both the product image and the VTO output.
 * Do not evaluate features not visible in the VTO output, such as the back or side if those areas are not shown.
 * If the product image shows the garment from a different angle (e.g., side view), only compare the regions visible in both images.
 * If the VTO system infers or completes parts not visible in the product image, allow reasonable variation unless the output clearly contradicts known design elements.
 * Ignore all other clothing or accessories at this stage.

 3. **Attribute-Level Inspection (CRITICAL FOCUS ON DRESS LENGTH, COLOR & SIDE MIRRORING)**:

  * For the identified garment (e.g., dress, skirt, shirt, kurta, jacket), examine all **visible and relevant visual attributes**.
  * **Dress Length & Garment Length (CRITICAL)**: Pay critical attention to exact dress length and hemline position (e.g., floor-length, ankle-length, midi/calf-length, knee-length, mini/above-knee, cropped). Accurately evaluate and measure garment length against the product image and flag any discrepancy where the dress/garment length is shorter or longer than the original product image.
  * **Color Accuracy**: Pay critical attention to exact color fidelity. Flag any deviation in hue, saturation, shade, or pattern color (e.g., navy blue vs. charcoal black, cream vs. bright white, faded vs. vibrant tint).
  * **Mirroring of Sides & Asymmetry (Left vs. Right)**: Pay critical attention to horizontal mirroring or left/right flipping. Flag if any asymmetric feature (e.g., one-shoulder strap, single sleeve, chest pocket, side slit, logo, diagonal pattern) is mirrored onto the wrong side. Clearly distinguish between viewer's left/right and wearer's anatomical left/right.
  * Common attributes include:
    * **Dress length / garment length**, **hemline position**, **color**, **pattern**, **fabric texture**, **fit/shape**, **side mirroring / orientation**
    * Design details: **sleeves**, **collar**, **buttons**, **zippers**, **pockets**, **hood**, **logos**, **text**, **lace**, **stitching**, **frills**
  * Skip attributes that are unclear, poorly visible, or obstructed.
  * Flag even small differences, such as altered dress length, missing buttons, altered sleeve length, or pattern mismatches.
  * Combine related discrepancies under a single attribute when appropriate (e.g. “dress length and hemline”).


---

### 🧾 Step 2: Person Integrity, Footwear, Accessories & Physical Pose Check

1. **Compare the VTO Output with the Original Person Image**:

 * Identify any unintended modifications to the person's **physical pose**, body posture, footwear, accessories, or appearance that are **not part of the target garment**.

2. **Evaluate Physical Pose Changes**:

 * Carefully inspect if the person's physical body posture changed between the Person image and the VTO output.
 * Flag physical pose alterations such as:
   * Changes in **body orientation or torso angle** (e.g. standing straight vs. angled shoulder/torso).
   * Changes in **arm, hand, or leg stance** (e.g. arms relaxed at sides changed to hands on hips or folded arms).
   * Changes in **head tilt, facial angle, or gaze direction**.

 3. **Focus on Unintended Appearance, Footwear & Accessory Changes**:

  * Check all footwear, bags, jewelry, and accessories visible in the Person image and VTO output. Report any added, removed, altered, or missing footwear or accessories.
  * Examples of mistakes to flag:
    * Color/shape of **shoes / footwear**, **handbags**, **jewelry**, **pants**, or **belts** getting altered.
    * Unjustified changes in hairstyle, body proportions, or background elements.
  * Only report differences that are clearly visible.
  * Skip subtle or unclear changes; avoid guessing.


---

### 🧠 Additional Evaluation Guidelines

* Only compare visible and unobstructed details. Do not speculate about hidden or unclear features.
* Be tolerant when the VTO system predicts garment parts not shown in the product image, unless there’s a clear contradiction.
* Do not over-interpret natural fit/styling changes (e.g. tucked-in shirt, slight shortening due to body size).
* Do not flag expected occlusions. For example, if a long top covers part of a pant, that’s acceptable — only flag it if the **visible part of the pant** is altered.
* Always evaluate both garment attribute differences and physical pose differences.
* If unsure, it’s better to skip than to report a mistake incorrectly.
* Avoid using terms like “target product” or “target garment” in your output. Always name the actual garment (e.g., shirt, skirt).
* Group related differences where appropriate to keep the output concise.

---

### ✅ Output Format (JSON)

Return your results as a JSON array of objects. Each object must contain:

* `"attribute"`: Name or description of the visual element or physical pose being evaluated
* `"difference"`: Description of the change/mistake found

Example:

```json
[
{
  "attribute": "button count",
  "difference": "Product image shows 5 buttons, but VTO output shows only 4 buttons"
},
{
  "attribute": "physical body pose",
  "difference": "Person image shows arms relaxed straight at sides, but VTO output changed left arm to be bent at the elbow"
},
{
  "attribute": "shoe color from person image",
  "difference": "Person image shows black sneakers, but VTO output changed them to white sneakers"
}
]
```

If no issues are found, return an **empty array**: `[]`

NOTE:
**Use image references**: Always specify "Product image", "Person image", or "VTO output" - never use generic terms like "Image 1, 2, 3"
"""
