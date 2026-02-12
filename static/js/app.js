// TIA Version Tracker - Main Application JavaScript

const API_BASE = '/api';
let currentProjectId = null;
let selectedSnapshots = new Set();

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    loadProjects();
    setupEventListeners();
});

function setupEventListeners() {
    // New project button
    document.getElementById('newProjectBtn').addEventListener('click', showNewProjectForm);
    document.getElementById('createProjectBtn').addEventListener('click', createProject);
    document.getElementById('cancelProjectBtn').addEventListener('click', hideNewProjectForm);

    // Project selection
    document.getElementById('projectSelect').addEventListener('change', onProjectChange);

    // File upload
    document.getElementById('fileInput').addEventListener('change', onFileSelect);
    document.getElementById('uploadForm').addEventListener('submit', uploadSnapshot);

    // Comparison
    document.getElementById('compareBtn').addEventListener('click', compareSnapshots);
}

// Project Management
async function loadProjects() {
    try {
        const response = await fetch(`${API_BASE}/projects`);
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('projectSelect');
            select.innerHTML = '<option value="">Select a project...</option>';

            data.projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.id;
                option.textContent = `${project.name} (${project.snapshot_count} snapshots)`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading projects:', error);
        showStatus('error', 'Failed to load projects');
    }
}

function showNewProjectForm() {
    document.getElementById('newProjectForm').classList.remove('hidden');
    document.getElementById('newProjectName').focus();
}

function hideNewProjectForm() {
    document.getElementById('newProjectForm').classList.add('hidden');
    document.getElementById('newProjectName').value = '';
}

async function createProject() {
    const name = document.getElementById('newProjectName').value.trim();

    if (!name) {
        alert('Please enter a project name');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/projects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });

        const data = await response.json();

        if (data.success) {
            hideNewProjectForm();
            await loadProjects();
            document.getElementById('projectSelect').value = data.project_id;
            onProjectChange();
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Error creating project:', error);
        alert('Failed to create project');
    }
}

function onProjectChange() {
    const select = document.getElementById('projectSelect');
    currentProjectId = select.value;

    if (currentProjectId) {
        document.getElementById('uploadSection').style.display = 'block';
        document.getElementById('snapshotsSection').style.display = 'block';
        loadSnapshots();
    } else {
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('snapshotsSection').style.display = 'none';
    }
}

// Snapshot Management
function onFileSelect(event) {
    const file = event.target.files[0];
    const fileInfo = document.getElementById('fileInfo');

    if (file) {
        fileInfo.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    } else {
        fileInfo.textContent = 'No file selected';
    }
}

async function uploadSnapshot(event) {
    event.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const operatorInput = document.getElementById('operatorInput');
    const projectSelect = document.getElementById('projectSelect');

    const file = fileInput.files[0];
    const operator = operatorInput.value.trim();
    const projectName = projectSelect.options[projectSelect.selectedIndex].text.split(' (')[0];

    if (!file || !operator) {
        showStatus('error', 'Please fill in all fields');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_name', projectName);
    formData.append('operator', operator);

    try {
        showStatus('info', 'Uploading and processing file...');

        const response = await fetch(`${API_BASE}/snapshots`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showStatus('success', 'Snapshot uploaded successfully!');
            fileInput.value = '';
            operatorInput.value = '';
            document.getElementById('fileInfo').textContent = 'No file selected';
            await loadSnapshots();
            await loadProjects(); // Refresh project counts
        } else {
            showStatus('error', `Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Error uploading snapshot:', error);
        showStatus('error', 'Failed to upload snapshot');
    }
}

async function loadSnapshots() {
    if (!currentProjectId) return;

    try {
        const response = await fetch(`${API_BASE}/projects/${currentProjectId}/snapshots`);
        const data = await response.json();

        if (data.success) {
            displaySnapshots(data.snapshots);
        }
    } catch (error) {
        console.error('Error loading snapshots:', error);
    }
}

function displaySnapshots(snapshots) {
    const container = document.getElementById('snapshotsList');
    selectedSnapshots.clear();

    if (snapshots.length === 0) {
        container.innerHTML = '<p class="hint">No snapshots yet. Upload your first .zap15 file above.</p>';
        document.getElementById('compareControls').classList.add('hidden');
        return;
    }

    container.innerHTML = '';

    snapshots.forEach(snapshot => {
        const item = document.createElement('div');
        item.className = 'snapshot-item';
        item.innerHTML = `
            <input type="checkbox" class="snapshot-checkbox" data-id="${snapshot.id}">
            <div class="snapshot-info">
                <strong>${snapshot.file_name || 'Snapshot #' + snapshot.id}</strong>
                <div class="snapshot-meta">
                    📅 ${new Date(snapshot.snapshot_date).toLocaleString()} 
                    | 👤 ${snapshot.operator}
                </div>
            </div>
        `;

        const checkbox = item.querySelector('.snapshot-checkbox');
        checkbox.addEventListener('change', () => onSnapshotSelect(snapshot.id, checkbox.checked));
        item.addEventListener('click', (e) => {
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change'));
            }
        });

        container.appendChild(item);
    });

    updateCompareButton();
}

function onSnapshotSelect(snapshotId, checked) {
    if (checked) {
        if (selectedSnapshots.size < 2) {
            selectedSnapshots.add(snapshotId);
        } else {
            event.target.checked = false;
            return;
        }
    } else {
        selectedSnapshots.delete(snapshotId);
    }

    updateCompareButton();
    updateSelectedStyles();
}

function updateSelectedStyles() {
    document.querySelectorAll('.snapshot-item').forEach(item => {
        const checkbox = item.querySelector('.snapshot-checkbox');
        if (checkbox.checked) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
}

function updateCompareButton() {
    const controls = document.getElementById('compareControls');
    const button = document.getElementById('compareBtn');

    if (selectedSnapshots.size === 2) {
        controls.classList.remove('hidden');
        button.disabled = false;
    } else if (selectedSnapshots.size > 0) {
        controls.classList.remove('hidden');
        button.disabled = true;
    } else {
        controls.classList.add('hidden');
    }
}

async function compareSnapshots() {
    const ids = Array.from(selectedSnapshots);

    if (ids.length !== 2) {
        alert('Please select exactly 2 snapshots');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                snapshot_a_id: ids[0],
                snapshot_b_id: ids[1]
            })
        });

        const data = await response.json();

        if (data.success) {
            // Store comparison data and navigate to results page
            sessionStorage.setItem('comparisonData', JSON.stringify(data.comparison));
            sessionStorage.setItem('snapshotIds', JSON.stringify({ a: ids[0], b: ids[1] }));
            sessionStorage.setItem('projectId', currentProjectId);
            window.location.href = '/comparison';
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Error comparing snapshots:', error);
        alert('Failed to compare snapshots');
    }
}

function showStatus(type, message) {
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.className = `status-message ${type}`;
    statusDiv.textContent = message;
    statusDiv.classList.remove('hidden');

    setTimeout(() => {
        statusDiv.classList.add('hidden');
    }, 5000);
}
