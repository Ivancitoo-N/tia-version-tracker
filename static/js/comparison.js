// TIA Version Tracker - Comparison Page JavaScript

const API_BASE = '/api';
let comparisonData = null;
let snapshotIds = null;
let projectId = null;

// Initialize comparison page
document.addEventListener('DOMContentLoaded', () => {
    loadComparisonData();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('downloadPdfBtn').addEventListener('click', downloadPdf);
}

function loadComparisonData() {
    // Load data from sessionStorage
    const dataStr = sessionStorage.getItem('comparisonData');
    const idsStr = sessionStorage.getItem('snapshotIds');
    const projIdStr = sessionStorage.getItem('projectId');

    if (!dataStr || !idsStr) {
        alert('No comparison data found. Redirecting to home...');
        window.location.href = '/';
        return;
    }

    comparisonData = JSON.parse(dataStr);
    snapshotIds = JSON.parse(idsStr);
    projectId = projIdStr;

    displayComparisonResults();
}

function displayComparisonResults() {
    // Update summary cards
    document.getElementById('newTagsCount').textContent = comparisonData.new_tags.length;
    document.getElementById('modifiedTagsCount').textContent = comparisonData.modified_tags.length;
    document.getElementById('deletedTagsCount').textContent = comparisonData.deleted_tags.length;

    // Display new tags
    displayNewTags(comparisonData.new_tags);

    // Display modified tags
    displayModifiedTags(comparisonData.modified_tags);

    // Display deleted tags
    displayDeletedTags(comparisonData.deleted_tags);
}

function displayNewTags(tags) {
    const tbody = document.querySelector('#newTagsTable tbody');
    const section = document.getElementById('newTagsSection');

    if (tags.length === 0) {
        section.style.display = 'none';
        return;
    }

    tbody.innerHTML = '';

    tags.forEach(tag => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${tag.tag_name}</strong></td>
            <td>${tag.tag_type || '-'}</td>
            <td>${tag.tag_address || '-'}</td>
            <td>${tag.tag_description || '-'}</td>
        `;
        tbody.appendChild(row);
    });
}

function displayModifiedTags(modifiedTags) {
    const container = document.getElementById('modifiedTagsList');
    const section = document.getElementById('modifiedTagsSection');

    if (modifiedTags.length === 0) {
        section.style.display = 'none';
        return;
    }

    container.innerHTML = '';

    modifiedTags.forEach(mod => {
        const tagDiv = document.createElement('div');
        tagDiv.className = 'tag-change';

        let changesHtml = '';
        mod.changes.forEach(change => {
            changesHtml += `
                <div class="change-detail">
                    <div class="change-field">${change.field}:</div>
                    <div class="change-old">Old: ${change.old || '(empty)'}</div>
                    <div class="change-new">New: ${change.new || '(empty)'}</div>
                </div>
            `;
        });

        tagDiv.innerHTML = `
            <div class="tag-change-header">⚠️ ${mod.tag_name}</div>
            ${changesHtml}
        `;

        container.appendChild(tagDiv);
    });
}

function displayDeletedTags(tags) {
    const tbody = document.querySelector('#deletedTagsTable tbody');
    const section = document.getElementById('deletedTagsSection');

    if (tags.length === 0) {
        section.style.display = 'none';
        return;
    }

    tbody.innerHTML = '';

    tags.forEach(tag => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${tag.tag_name}</strong></td>
            <td>${tag.tag_type || '-'}</td>
            <td>${tag.tag_address || '-'}</td>
            <td>${tag.tag_description || '-'}</td>
        `;
        tbody.appendChild(row);
    });
}

async function downloadPdf() {
    if (!snapshotIds) {
        alert('No comparison data available');
        return;
    }

    try {
        // Get project name
        const projectSelect = sessionStorage.getItem('projectName') || 'TIA Project';

        const response = await fetch(`${API_BASE}/compare/pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                snapshot_a_id: snapshotIds.a,
                snapshot_b_id: snapshotIds.b,
                project_name: projectSelect
            })
        });

        if (response.ok) {
            // Download the PDF
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `comparison_${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const data = await response.json();
            alert(`Error generating PDF: ${data.error}`);
        }
    } catch (error) {
        console.error('Error downloading PDF:', error);
        alert('Failed to download PDF report');
    }
}
