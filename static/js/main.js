const socket = io();
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileName = document.getElementById('file-name');
const controls = document.getElementById('scrape-controls');
const colSelector = document.getElementById('column-selector');
const startBtn = document.getElementById('start-btn');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const logList = document.getElementById('log-list');
const resultsBody = document.getElementById('results-body');

let currentTempPath = "";

// Drag and Drop
['dragover', 'dragleave', 'drop'].forEach(evt => {
    dropZone.addEventListener(evt, e => {
        e.preventDefault();
        if(evt === 'dragover') dropZone.classList.add('active');
        else dropZone.classList.remove('active');
    });
});

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
    if(fileInput.files.length > 0) handleUpload(fileInput.files[0]);
});

dropZone.addEventListener('drop', e => {
    if(e.dataTransfer.files.length > 0) handleUpload(e.dataTransfer.files[0]);
});

function handleUpload(file) {
    fileName.innerText = file.name;
    addLog(`File uploaded: ${file.name}`, 'system');
    
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/upload-csv', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if(data.headers) {
                currentTempPath = data.temp_path;
                colSelector.innerHTML = data.headers.map(h => `<option value="${h}">${h}</option>`).join('');
                controls.style.display = 'block';
                addLog(`Found ${data.headers.length} columns. Please select the Business Name column.`, 'system');
            }
        });
}

// Start Scraper
startBtn.addEventListener('click', () => {
    const column = colSelector.value;
    const threads = document.getElementById('thread-count').value;
    
    startBtn.disabled = true;
    startBtn.innerText = "Engines Running...";
    resultsBody.innerHTML = ""; // Clear table
    
    socket.emit('start_scrape', {
        path: currentTempPath,
        column: column,
        threads: threads
    });
});

// Socket Events
socket.on('scrape_started', data => {
    addLog(`Scraping started for ${data.total} companies...`, 'success');
    document.getElementById('stat-total').innerText = data.total;
    updateProgress(0);
});

socket.on('row_finished', data => {
    const row = data.data;
    addDataRow(row);
    updateProgress(data.progress);
    
    const count = parseInt(document.getElementById('stat-processed').innerText) + 1;
    document.getElementById('stat-processed').innerText = count;
    
    const total = parseInt(document.getElementById('stat-total').innerText);
    document.getElementById('stat-success').innerText = Math.round((count / total) * 100) + "%";
    
    addLog(`[${count}/${total}] Scraped ${row.company_name}`, row.status === 'Success' ? 'success' : 'error');
});

socket.on('scrape_complete', data => {
    addLog(data.message, 'success');
    startBtn.disabled = false;
    startBtn.innerText = "Start Engines";
    document.getElementById('export-btn').disabled = false;
});

// Helper Functions
function addLog(msg, type) {
    const div = document.createElement('div');
    div.className = `log-entry ${type}`;
    div.innerText = `> ${new Date().toLocaleTimeString()}: ${msg}`;
    logList.prepend(div);
}

function updateProgress(percent) {
    const p = Math.round(percent);
    progressFill.style.width = p + "%";
    progressText.innerText = p + "%";
}

function addDataRow(row) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td class="text-bold">${row.company_name}</td>
        <td><a href="${row.website_link}" target="_blank" class="link">${row.website_link.replace('https://www.', '').replace('https://', '')}</a></td>
        <td>${row.email}</td>
        <td>${row.phone}</td>
        <td>${row.location}</td>
        <td>
            ${row.socials.LinkedIn !== 'Not Found' ? 'L ' : ''}
            ${row.socials.Facebook !== 'Not Found' ? 'F ' : ''}
            ${row.socials.Instagram !== 'Not Found' ? 'I ' : ''}
        </td>
    `;
    resultsBody.prepend(tr);
}
