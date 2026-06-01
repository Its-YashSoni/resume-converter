const dropZone          = document.getElementById('dropZone');
const browseBtn         = document.getElementById('browseBtn');
const fileInput         = document.getElementById('fileInput');
const fileName          = document.getElementById('fileName');
const convertBtn        = document.getElementById('convertBtn');
const btnText           = document.getElementById('btnText');
const btnSpinner        = document.getElementById('btnSpinner');
const errorBox          = document.getElementById('errorBox');
const errorMsg          = document.getElementById('errorMsg');
const stepsView         = document.getElementById('stepsView');
const processingView    = document.getElementById('processingView');
const successView       = document.getElementById('successView');
const successName       = document.getElementById('successName');
const downloadBtn       = document.getElementById('downloadBtn');
const convertAnotherBtn = document.getElementById('convertAnotherBtn');

const procSteps = [
  document.getElementById('proc1'),
  document.getElementById('proc2'),
  document.getElementById('proc3'),
  document.getElementById('proc4'),
];

let selectedFile = null;
let stepAnimationActive = false;

// Browse button opens file picker
browseBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  fileInput.value = '';
  fileInput.click();
});

// File selected from picker
fileInput.addEventListener('change', () => {
  if (fileInput.files && fileInput.files[0]) {
    selectFile(fileInput.files[0]);
  }
});

// Drop zone click (anywhere except the button)
dropZone.addEventListener('click', (e) => {
  if (e.target === browseBtn) return;
  fileInput.value = '';
  fileInput.click();
});

// Drag & drop
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
});
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    selectFile(e.dataTransfer.files[0]);
  }
});

function selectFile(file) {
  hideError();
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showError('Only PDF files are supported. Please upload a .pdf file.');
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showError('File is too large. Maximum size is 10MB.');
    return;
  }
  selectedFile = file;
  fileName.textContent = '📎 ' + file.name;
  fileName.style.color = '#4ade80';
  convertBtn.disabled = false;
}

// Convert
convertBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  hideError();
  setLoading(true);
  showView('processing');
  stepAnimationActive = true;
  animateSteps();

  const formData = new FormData();
  formData.append('resume', selectedFile);

  try {
    const response = await fetch('/convert', {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();
    stepAnimationActive = false;

    if (!response.ok || result.error) {
      setLoading(false);
      showView('steps');
      showError(result.error || 'Something went wrong. Please try again.');
      return;
    }

    procSteps.forEach(s => { s.classList.remove('dim'); s.classList.add('done'); });
    await delay(700);

    setLoading(false);
    successName.textContent = result.name ? `✅ Converted: ${result.name}` : '✅ Conversion complete!';
    downloadBtn.href = `/download/${result.download_id}`;
    showView('success');

  } catch (err) {
    stepAnimationActive = false;
    setLoading(false);
    showView('steps');
    showError('Network error. Make sure the server is running and try again.');
  }
});

// Convert Another
convertAnotherBtn.addEventListener('click', () => {
  selectedFile = null;
  fileInput.value = '';
  fileName.textContent = 'No file selected';
  fileName.style.color = '#6c63ff';
  convertBtn.disabled = true;
  hideError();
  showView('steps');
});

function setLoading(on) {
  convertBtn.disabled = on;
  btnSpinner.classList.toggle('hidden', !on);
  btnText.textContent = on ? 'Converting...' : 'Convert Resume';
}

function showView(view) {
  stepsView.classList.add('hidden');
  processingView.classList.add('hidden');
  successView.classList.add('hidden');
  if (view === 'steps')      stepsView.classList.remove('hidden');
  if (view === 'processing') processingView.classList.remove('hidden');
  if (view === 'success')    successView.classList.remove('hidden');
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorBox.classList.remove('hidden');
}

function hideError() {
  errorBox.classList.add('hidden');
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function animateSteps() {
  procSteps.forEach(s => { s.classList.add('dim'); s.classList.remove('done'); });
  procSteps[0].classList.remove('dim');

  const timings = [1500, 4000, 7000, 10000];
  for (let i = 0; i < procSteps.length; i++) {
    if (!stepAnimationActive) break;
    await delay(timings[i]);
    if (!stepAnimationActive) break;
    procSteps[i].classList.add('done');
    if (i + 1 < procSteps.length) procSteps[i + 1].classList.remove('dim');
  }
}
