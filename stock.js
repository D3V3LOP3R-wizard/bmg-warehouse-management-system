// Frontend script: calls backend `/api/search?q=` and renders results

document.getElementById('stockSearchForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const searchTerm = document.getElementById('stockCode').value.trim();
    if (searchTerm) {
        searchStock(searchTerm);
    }
});

async function searchStock(query) {
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.innerHTML = '<div class="result-card">Searching…</div>';

    try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            resultsContainer.innerHTML = `<div class="result-card"><div class="result-header"><div class="result-title">Error</div></div><p>${body.error || 'Request failed'}</p></div>`;
            return;
        }

        const payload = await res.json();
        const matches = payload.results || [];

        if (matches.length === 0) {
            resultsContainer.innerHTML = `
                <div class="result-card">
                    <div class="result-header">
                        <div class="result-title">No Results Found</div>
                    </div>
                    <p>No stock items found matching "${escapeHtml(query)}". Please check the part number and try again.</p>
                </div>
            `;
            return;
        }

        // Build HTML
        resultsContainer.innerHTML = '';
        matches.forEach(item => {
            const statusClass = item.status === 'correct' ? 'status-correct' : 'status-incorrect';
            const statusText = item.status === 'correct' ? 'Correct Location' : 'Incorrect Location';

            const resultHTML = `
                <div class="result-card">
                    <div class="result-header">
                        <div class="result-title">${escapeHtml(item.partNumber)} - ${escapeHtml(item.description)}</div>
                        <div class="result-status ${statusClass}">${statusText}</div>
                    </div>
                    
                    <div class="result-details">
                        <div class="detail-item">
                            <div class="detail-label">Current Bin Location</div>
                            <div class="detail-value">${escapeHtml(item.currentBin)}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Correct Bin Location</div>
                            <div class="detail-value">${escapeHtml(item.correctBin)}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Quantity in Stock</div>
                            <div class="detail-value">${escapeHtml(String(item.quantity))} units</div>
                        </div>
                    </div>
                    
                    <div class="bin-location">
                        <div class="bin-title">Correct Placement Location:</div>
                        <div class="bin-info">
                            <div class="bin-number">${escapeHtml(item.correctBin)}</div>
                            <div class="bin-zone">Zone ${escapeHtml(String(item.correctBin).charAt(0))}</div>
                        </div>
                        ${item.status === 'incorrect' ? 
                            `<p style="margin-top: 10px; color: var(--danger); font-weight: 600;">
                                <i class="fas fa-exclamation-triangle"></i> This item is in the wrong location. Please move it to bin ${escapeHtml(item.correctBin)}.
                            </p>` : 
                            `<p style="margin-top: 10px; color: var(--success); font-weight: 600;">
                                <i class="fas fa-check-circle"></i> This item is in the correct location.
                            </p>`
                        }
                    </div>
                </div>
            `;

            resultsContainer.innerHTML += resultHTML;
        });
    } catch (err) {
        resultsContainer.innerHTML = `<div class="result-card"><div class="result-header"><div class="result-title">Error</div></div><p>Network error: ${escapeHtml(err.message || String(err))}</p></div>`;
    }
}

function escapeHtml(s) {
    return (s + '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// Initialize with a sample search
window.onload = function () {
    // Optionally run a sample search on load
    // searchStock('BMG-12345');
};