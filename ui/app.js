/**
 * Nexus Spatial Intelligence - Browser UI
 * 
 * Handles video upload, analysis execution, and results visualization.
 */

const API_BASE = window.location.origin;
let selectedFile = null;
let currentRunId = null;

// Upload zone drag-and-drop
const uploadZone = document.getElementById('uploadZone');
const videoInput = document.getElementById('videoInput');

uploadZone.addEventListener('click', () => videoInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

videoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    selectedFile = file;
    uploadZone.querySelector('p').textContent = `✓ ${file.name}`;
    uploadZone.querySelector('.hint').textContent = `Size: ${(file.size / (1024 * 1024)).toFixed(2)} MB`;
    document.getElementById('analyzeBtn').disabled = false;
}

// Analyze button
document.getElementById('analyzeBtn').addEventListener('click', analyzeVideo);

async function analyzeVideo() {
    if (!selectedFile) {
        showError('Please select a video file');
        return;
    }
    
    // Reset UI
    hideError();
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('progressContainer').style.display = 'block';
    document.getElementById('analyzeBtn').disabled = true;
    updateProgress(0, 'Uploading video...');
    
    try {
        // Upload and analyze
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        updateProgress(20, 'Sending to server...');
        
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            body: formData,
        });
        
        updateProgress(70, 'Processing...');
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }
        
        const result = await response.json();
        updateProgress(95, 'Rendering results...');
        
        currentRunId = result.run_id;
        displayResults(result);
        
        updateProgress(100, 'Complete!');
        setTimeout(() => {
            document.getElementById('progressContainer').style.display = 'none';
        }, 500);
        
    } catch (error) {
        document.getElementById('progressContainer').style.display = 'none';
        document.getElementById('analyzeBtn').disabled = false;
        showError(error.message);
        console.error('Analysis error:', error);
    }
}

function updateProgress(percent, text) {
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressText').textContent = text;
}

function showError(message) {
    const errorBox = document.getElementById('errorBox');
    document.getElementById('errorMessage').textContent = message;
    errorBox.classList.add('show');
}

function hideError() {
    document.getElementById('errorBox').classList.remove('show');
}

function displayResults(result) {
    document.getElementById('resultsSection').style.display = 'block';
    
    // Metrics
    const video = result.video;
    const processing = result.processing;
    const analysis = result.analysis;
    const adaptive = result.adaptive_analysis || {};
    const recommendation = result.agent_recommendation || {};
    
    document.getElementById('videoDuration').textContent = 
        `${(video.total_frames / video.fps).toFixed(2)}s`;
    document.getElementById('processingTime').textContent = 
        `${processing.duration_seconds.toFixed(2)}s`;
    document.getElementById('throughput').textContent = 
        `${processing.fps_processed.toFixed(1)}`;
    document.getElementById('avgMotion').textContent = 
        `${analysis.metrics.avg_foreground_percentage.toFixed(2)}%`;
    
    // Decision
    const decisionTitle = adaptive.decision_made === 'follow_up_triggered' 
        ? '🔍 Follow-up Refinement Triggered' 
        : '✓ Baseline Analysis Sufficient';
    const decisionClass = adaptive.decision_made === 'follow_up_triggered' ? 'triggered' : '';
    
    document.getElementById('decisionBox').className = `decision-box ${decisionClass}`;
    document.getElementById('decisionTitle').textContent = decisionTitle;
    document.getElementById('decisionReason').textContent = adaptive.reason || 'N/A';
    
    // Heatmaps
    displayHeatmap(result.run_id, result.artifacts);
    
    // Recommendation
    displayRecommendation(recommendation);
    
    // Trace
    displayTrace(adaptive, result.agent_recommendation);
    
    // S3 Status
    displayS3Status(result.s3_storage);
}

function displayHeatmap(runId, artifacts) {
    const baselineHeatmap = document.getElementById('baselineHeatmap');
    baselineHeatmap.src = `${API_BASE}/artifacts/${runId}/heatmap.png`;
    
    const followupContainer = document.getElementById('followupContainer');
    if (artifacts.heatmap_followup) {
        followupContainer.style.display = 'block';
        document.getElementById('followupHeatmap').src = 
            `${API_BASE}/artifacts/${runId}/heatmap_followup_16x16.png`;
    } else {
        followupContainer.style.display = 'none';
    }
}

function displayRecommendation(recommendation) {
    if (!recommendation || !recommendation.category) {
        document.getElementById('recommendationBox').innerHTML = '<p>No recommendation available</p>';
        return;
    }
    
    const categoryEmoji = {
        'low_activity_with_refinement': '🔍',
        'low_activity_refinement_failed': '⚠️',
        'sufficient_activity': '✓',
        'insufficient_data': '❓',
    };
    
    const emoji = categoryEmoji[recommendation.category] || '•';
    
    document.getElementById('recCategory').textContent = 
        `${emoji} ${recommendation.category.replace(/_/g, ' ')}`;
    
    // Evidence
    const evidenceHtml = recommendation.evidence
        .map(e => `<div class="evidence-item">${escapeHtml(e)}</div>`)
        .join('');
    document.getElementById('recEvidence').innerHTML = evidenceHtml;
    
    // Next Steps
    const stepsHtml = recommendation.next_steps
        .map(s => `<p>${escapeHtml(s)}</p>`)
        .join('');
    document.getElementById('recNextSteps').innerHTML = stepsHtml;
    
    // Notes
    document.getElementById('recNotes').textContent = recommendation.notes || '-';
}

function displayTrace(adaptive, agentRec) {
    const traceData = {
        adaptive_analysis: adaptive,
        agent_recommendation: agentRec,
    };
    
    const prettyJson = JSON.stringify(traceData, null, 2);
    document.getElementById('traceJson').textContent = prettyJson;
}

function displayS3Status(s3Storage) {
    const s3Status = document.getElementById('s3Status');
    const s3Label = document.getElementById('s3Label');
    const s3Details = document.getElementById('s3Details');
    
    if (s3Storage.enabled) {
        s3Status.classList.remove('disabled');
        s3Label.textContent = `☁️ S3 Storage: Enabled`;
        
        const artifacts = s3Storage.uploaded_artifacts || {};
        const artifactLinks = Object.entries(artifacts)
            .map(([key, uri]) => `<strong>${key}:</strong> ${escapeHtml(uri)}`)
            .join('<br>');
        
        s3Details.innerHTML = `
            <strong>Bucket:</strong> ${escapeHtml(s3Storage.bucket)}<br>
            <strong>Artifacts:</strong><br>
            ${artifactLinks}
        `;
    } else {
        s3Status.classList.add('disabled');
        s3Label.textContent = `💾 S3 Storage: Disabled`;
        s3Details.innerHTML = '<em>Artifacts stored locally only.</em>';
    }
}

function toggleTrace() {
    const content = document.getElementById('traceContent');
    const icon = document.getElementById('traceIcon');
    
    content.classList.toggle('show');
    icon.textContent = content.classList.contains('show') ? '▲' : '▼';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize on page load
window.addEventListener('load', () => {
    console.log('Nexus Spatial Intelligence UI loaded');
    updateProgress(0, 'Ready');
});
