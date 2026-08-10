/* Google Cloud Creative Studio — app.js */

document.addEventListener('DOMContentLoaded', () => {
  const personDropzone = document.getElementById('personDropzone');
  const personFileInput = document.getElementById('personFileInput');
  const personPreview = document.getElementById('personPreview');
  const garmentDropzone = document.getElementById('garmentDropzone');
  const garmentFileInput = document.getElementById('garmentFileInput');
  const garmentPreview = document.getElementById('garmentPreview');

  const maxItersSlider = document.getElementById('maxItersSlider');
  const maxItersDisplay = document.getElementById('maxItersDisplay');

  const runAgenticBtn = document.getElementById('runAgenticBtn');
  const clearBtn = document.getElementById('clearBtn');
  const streamingIndicator = document.getElementById('streamingIndicator');
  const iterationStatusChip = document.getElementById('iterationStatusChip');

  const outputPlaceholderText = document.getElementById('outputPlaceholderText');
  const mainOutputImage = document.getElementById('mainOutputImage');
  const poseVisualImage = document.getElementById('poseVisualImage');
  const poseScoreValue = document.getElementById('poseScoreValue');
  const poseScoreStatus = document.getElementById('poseScoreStatus');
  const poseGoalBadge = document.getElementById('poseGoalBadge');
  const diffCountBadge = document.getElementById('diffCountBadge');
  const attributeDiffsContainer = document.getElementById('attributeDiffsContainer');

  const trackerBody = document.getElementById('trackerBody');
  const iterationGalleryStrip = document.getElementById('iterationGalleryStrip');

  let selectedPersonFile = null;
  let selectedGarmentFile = null;

  // Max iterations update
  maxItersSlider.addEventListener('input', (e) => {
    maxItersDisplay.textContent = e.target.value;
  });

  const nanoThresholdSlider = document.getElementById('nanoThresholdSlider');
  const nanoThresholdDisplay = document.getElementById('nanoThresholdDisplay');
  if (nanoThresholdSlider && nanoThresholdDisplay) {
    nanoThresholdSlider.addEventListener('input', (e) => {
      nanoThresholdDisplay.textContent = parseFloat(e.target.value).toFixed(2);
    });
  }

  // Setup dropzone
  function setupDropzone(dropzone, fileInput, previewImg, onFileSelected) {
    dropzone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        const file = e.target.files[0];
        displayFilePreview(file, dropzone, previewImg);
        onFileSelected(file);
      }
    });

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        const file = e.dataTransfer.files[0];
        displayFilePreview(file, dropzone, previewImg);
        onFileSelected(file);
      }
    });
  }

  function displayFilePreview(fileOrUrl, dropzone, previewImg) {
    if (typeof fileOrUrl === 'string') {
      previewImg.src = fileOrUrl;
      dropzone.classList.add('has-image');
    } else {
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImg.src = e.target.result;
        dropzone.classList.add('has-image');
      };
      reader.readAsDataURL(fileOrUrl);
    }
  }

  setupDropzone(personDropzone, personFileInput, personPreview, (file) => {
    selectedPersonFile = file;
  });

  setupDropzone(garmentDropzone, garmentFileInput, garmentPreview, (file) => {
    selectedGarmentFile = file;
  });

  // Load sample Quick Picks
  async function loadSamples() {
    try {
      const response = await fetch('/api/samples');
      if (!response.ok) return;
      const data = await response.json();

      const personContainer = document.getElementById('personSampleChips');
      personContainer.innerHTML = '';
      data.person.forEach((sampleUrl) => {
        const chip = document.createElement('div');
        chip.className = 'sample-chip';
        chip.innerHTML = `<img src="${sampleUrl}" alt="Sample Person">`;
        chip.addEventListener('click', async (e) => {
          e.stopPropagation();
          displayFilePreview(sampleUrl, personDropzone, personPreview);
          const blob = await (await fetch(sampleUrl)).blob();
          const filename = sampleUrl.split('/').pop() || 'person_sample.png';
          selectedPersonFile = new File([blob], filename, { type: blob.type || 'image/png' });
        });
        personContainer.appendChild(chip);
      });

      const garmentContainer = document.getElementById('garmentSampleChips');
      garmentContainer.innerHTML = '';
      data.garments.forEach((sampleUrl) => {
        const chip = document.createElement('div');
        chip.className = 'sample-chip';
        chip.innerHTML = `<img src="${sampleUrl}" alt="Sample Garment">`;
        chip.addEventListener('click', async (e) => {
          e.stopPropagation();
          displayFilePreview(sampleUrl, garmentDropzone, garmentPreview);
          const blob = await (await fetch(sampleUrl)).blob();
          const filename = sampleUrl.split('/').pop() || 'garment_sample.png';
          selectedGarmentFile = new File([blob], filename, { type: blob.type || 'image/png' });
        });
        garmentContainer.appendChild(chip);
      });
    } catch (err) {
      console.warn('Failed to load samples:', err);
    }
  }

  loadSamples();

  // Clear button
  clearBtn.addEventListener('click', () => {
    selectedPersonFile = null;
    selectedGarmentFile = null;
    personPreview.src = '';
    garmentPreview.src = '';
    personDropzone.classList.remove('has-image');
    garmentDropzone.classList.remove('has-image');

    outputPlaceholderText.style.display = 'block';
    mainOutputImage.style.display = 'none';
    poseVisualImage.style.display = 'none';
    poseScoreValue.textContent = '—';
    poseScoreStatus.textContent = 'Waiting for run...';
    attributeDiffsContainer.textContent = 'No attribute differences detected yet.';

    trackerBody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">No iterations executed yet.</td></tr>`;
    iterationGalleryStrip.innerHTML = `<div style="color:var(--text-muted);font-size:0.9rem;padding:12px 0;">Iteration gallery slides appear here as each step completes...</div>`;
    iterationStatusChip.textContent = 'Ready';
  });

  // Run Agentic VTO SSE Loop
  runAgenticBtn.addEventListener('click', async () => {
    if (!selectedPersonFile || !selectedGarmentFile) {
      alert('Please select both a Person reference image and a Garment image first.');
      return;
    }

    const activeProcessingOverlay = document.getElementById('activeProcessingOverlay');
    const processingHeadlineText = document.getElementById('processingHeadlineText');
    const processingSubtext = document.getElementById('processingSubtext');

    runAgenticBtn.disabled = true;
    runAgenticBtn.innerHTML = '<span>⚡</span> AI Processing Active...';
    streamingIndicator.style.display = 'flex';
    iterationStatusChip.textContent = 'Clearing & starting loop...';
    activeProcessingOverlay.style.display = 'flex';
    processingHeadlineText.textContent = '🤖 Autonomous AI Processing Active...';
    processingSubtext.textContent = 'Clearing previous outputs & generating initial try-on...';

    // Clear all output components immediately when button is clicked
    mainOutputImage.src = '';
    mainOutputImage.style.display = 'none';
    outputPlaceholderText.style.display = 'block';
    poseVisualImage.src = '';
    poseVisualImage.style.display = 'none';
    poseScoreValue.textContent = 'N/A';
    poseScoreStatus.textContent = 'Ready';
    poseScoreStatus.style.color = 'var(--text-sub)';
    diffCountBadge.textContent = '0 Diffs';
    attributeDiffsContainer.textContent = 'Run generation to see detailed attribute differences...';
    attributeDiffsContainer.style.color = 'var(--text-sub)';
    trackerBody.innerHTML = '';
    iterationGalleryStrip.innerHTML = '';

    const onlineModeToggle = document.getElementById('onlineModeToggle');
    const formData = new FormData();
    formData.append('person_image', selectedPersonFile);
    formData.append('garment_image', selectedGarmentFile);
    formData.append('max_iterations', maxItersSlider.value);
    formData.append('nano_banana_threshold', nanoThresholdSlider ? nanoThresholdSlider.value : '0.75');
    formData.append('online_mode', onlineModeToggle ? onlineModeToggle.checked : false);

    try {
      const response = await fetch('/api/agentic-vto-stream', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Server error running agentic loop');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n\n');
        buffer = lines.pop();

        for (const block of lines) {
          if (block.startsWith('data: ')) {
            const jsonStr = block.slice(6);
            const update = JSON.parse(jsonStr);
            applyIterationUpdate(update);
          }
        }
      }
    } catch (err) {
      console.error('Agentic run failed:', err);
      iterationStatusChip.textContent = 'Error';
    } finally {
      runAgenticBtn.disabled = false;
      runAgenticBtn.innerHTML = '<span>🚀</span> Start Agentic Try-On Loop';
      streamingIndicator.style.display = 'none';
      const activeProcessingOverlay = document.getElementById('activeProcessingOverlay');
      if (activeProcessingOverlay) activeProcessingOverlay.style.display = 'none';
    }
  });

  function applyIterationUpdate(update) {
    const activeProcessingOverlay = document.getElementById('activeProcessingOverlay');
    const processingHeadlineText = document.getElementById('processingHeadlineText');
    const processingSubtext = document.getElementById('processingSubtext');

    function updateDisplayMetrics(item) {
      mainOutputImage.style.display = 'block';
      mainOutputImage.src = item.image_url;
      if (item.pose_image_url) {
        poseVisualImage.style.display = 'block';
        poseVisualImage.src = item.pose_image_url;
      }
      const s = item.similarity_score;
      poseScoreValue.textContent = s !== null ? s.toFixed(2) : 'N/A';
      if (s !== null && s > 0.90) {
        poseScoreStatus.textContent = 'Target Achieved ✅';
        poseScoreStatus.style.color = 'var(--google-green)';
      } else {
        poseScoreStatus.textContent = 'Refining pose...';
        poseScoreStatus.style.color = 'var(--google-coral)';
      }

      const d = item.attributes || [];
      diffCountBadge.textContent = `${d.length} Diffs Detected`;
      if (d.length === 0) {
        attributeDiffsContainer.textContent = '🎉 0 Attribute Differences (Perfect match!)';
        attributeDiffsContainer.style.color = 'var(--google-green)';
      } else {
        attributeDiffsContainer.textContent = JSON.stringify(d, null, 2);
        attributeDiffsContainer.style.color = 'var(--text-sub)';
      }
    }

    outputPlaceholderText.style.display = 'none';
    updateDisplayMetrics(update);

    if (!update.goal_met) {
      if (activeProcessingOverlay) {
        activeProcessingOverlay.style.display = 'flex';
        activeProcessingOverlay.style.background = 'rgba(11, 14, 20, 0.45)';
        processingHeadlineText.textContent = `⚡ Running Iteration ${update.iteration + 1}...`;
        processingSubtext.textContent = 'Synthesizing anti-mirroring & pose optimization via Nano Banana / VTO...';
      }
    } else {
      if (activeProcessingOverlay) {
        activeProcessingOverlay.style.display = 'none';
      }
    }

    const score = update.similarity_score;
    const diffs = update.attributes || [];

    // Append to tracker table
    const tr = document.createElement('tr');
    const iterNum = update.iteration;
    const toolName = update.tool === 'nano_banana' ? '🍌 Nano Banana' : '👗 Virtual Try-On';
    const actionText = update.prompt || '-';
    const poseOk = score > 0.90 ? '✅' : '⚠️';
    const diffOk = diffs.length === 0 ? '✅' : '⚠️';
    const statusText = (score > 0.90 && diffs.length === 0) ? '🎯 GOAL MET' : 'Iterating';

    tr.innerHTML = `
      <td><strong>Iter ${iterNum}</strong></td>
      <td>${toolName}</td>
      <td style="max-width:320px;overflow:hidden;text-overflow:ellipsis;">${actionText}</td>
      <td><code>${score}</code> ${poseOk}</td>
      <td><code>${diffs.length}</code> ${diffOk}</td>
      <td><strong>${statusText}</strong></td>
    `;
    trackerBody.appendChild(tr);

    // Append to Gallery strip
    const card = document.createElement('div');
    card.className = 'gallery-card';
    card.innerHTML = `
      <img src="${update.image_url}" alt="Iter ${iterNum}">
      <div class="gallery-label">Iter ${iterNum}: ${toolName}</div>
    `;
    card.addEventListener('click', () => {
      updateDisplayMetrics(update);
    });
    iterationGalleryStrip.appendChild(card);

    if (update.is_champion) {
      iterationStatusChip.textContent = '🏆 Overall Champion Selected';
      iterationStatusChip.style.background = 'rgba(251, 188, 4, 0.2)';
      iterationStatusChip.style.color = '#fbbc04';
    } else if (update.goal_met) {
      iterationStatusChip.textContent = '🎯 Target Goal Achieved';
      iterationStatusChip.style.background = 'rgba(129, 201, 149, 0.2)';
      iterationStatusChip.style.color = 'var(--google-green)';
    } else {
      iterationStatusChip.textContent = `Iteration ${iterNum} Complete`;
    }
  }
});

