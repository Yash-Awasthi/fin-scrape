// Manual data input functions

async function updateICEDetention(event) {
    event.preventDefault();
    
    const detained = parseInt(document.getElementById('ice-detained').value);
    const capacity = parseInt(document.getElementById('ice-capacity').value);
    const fillRate = (detained / capacity) * 100;
    
    const data = {
        indicator: 'ICEDetention',
        value: fillRate,
        metadata: {
            detained_count: detained,
            total_capacity: capacity,
            source: 'manual_input',
            updated_by: 'user',
            timestamp: new Date().toISOString()
        }
    };
    
    const success = await submitManualData(data);
    if (success) {
        showSuccess('ice-success', `ICE detention updated: ${fillRate.toFixed(1)}% fill rate`);
    }
}

async function updateDoDAutonomy(event) {
    event.preventDefault();
    
    const status = document.getElementById('dod-status').value;
    const count = parseInt(document.getElementById('dod-count').value);
    
    const data = {
        indicator: 'DoDAutonomy',
        value: count,
        metadata: {
            policy_status: status,
            system_count: count,
            source: 'manual_input',
            updated_by: 'user',
            timestamp: new Date().toISOString()
        }
    };
    
    const success = await submitManualData(data);
    if (success) {
        showSuccess('dod-success', `DoD autonomy updated: ${count} systems, ${status} policy`);
    }
}

async function updateMBridge(event) {
    event.preventDefault();
    
    const volume = parseFloat(document.getElementById('mbridge-volume').value);
    const participants = document.getElementById('mbridge-participants').value;
    
    const data = {
        indicator: 'MBridge',
        value: volume,
        metadata: {
            volume_billions: volume,
            participants: participants.split(',').map(p => p.trim()),
            source: 'manual_input',
            updated_by: 'user',
            timestamp: new Date().toISOString()
        }
    };
    
    const success = await submitManualData(data);
    if (success) {
        showSuccess('mbridge-success', `mBridge updated: $${volume}B monthly volume`);
    }
}

async function updateSchoolClosures(event) {
    event.preventDefault();
    
    const closures = parseInt(document.getElementById('school-closures').value);
    const reason = document.getElementById('school-reason').value;
    
    const data = {
        indicator: 'SchoolClosures',
        value: closures,
        metadata: {
            district_days_closed: closures,
            primary_reason: reason,
            source: 'manual_input',
            updated_by: 'user',
            timestamp: new Date().toISOString()
        }
    };
    
    const success = await submitManualData(data);
    if (success) {
        showSuccess('school-success', `School closures updated: ${closures} district-days`);
    }
}

async function updatePharmacyShortages(event) {
    event.preventDefault();
    
    const mental = parseInt(document.getElementById('pharma-mental').value);
    const adhd = parseInt(document.getElementById('pharma-adhd').value);
    const antibiotics = parseInt(document.getElementById('pharma-antibiotics').value);
    
    const total = mental + adhd + antibiotics;
    
    const data = {
        indicator: 'PharmacyShortage',
        value: total,
        metadata: {
            mental_health: mental,
            adhd: adhd,
            antibiotics: antibiotics,
            source: 'manual_input',
            updated_by: 'user',
            timestamp: new Date().toISOString()
        }
    };
    
    const success = await submitManualData(data);
    if (success) {
        showSuccess('pharma-success', `Pharmacy shortages updated: ${total} total drugs`);
    }
}

async function updateAGIMilestones(event) {
    event.preventDefault();
    
    const autonomous = document.getElementById('agi-autonomous').checked;
    const selfImprove = document.getElementById('agi-self-improve').checked;
    const general = document.getElementById('agi-general').checked;
    const economic = document.getElementById('agi-economic').checked;
    
    // Calculate milestone score
    let score = 0;
    if (autonomous) score += 25;
    if (selfImprove) score += 20;
    if (general) score += 30;
    if (economic) score += 25;
    
    const data = {
        indicator: 'AGIMilestones',
        value: score,
        metadata: {
            autonomous_operation: autonomous,
            self_improvement: selfImprove,
            general_reasoning: general,
            economic_replacement: economic,
            source: 'manual_input',
            updated_by: 'user',
            timestamp: new Date().toISOString()
        }
    };
    
    const success = await submitManualData(data);
    if (success) {
        showSuccess('agi-success', `AGI milestones updated: ${score}/100 score`);
    }
}

async function submitManualData(data) {
    try {
        const response = await fetch('/api/manual-update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        return response.ok;
    } catch (error) {
        console.error('Failed to submit manual data:', error);
        return false;
    }
}

function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    element.textContent = `✅ ${message}`;
    element.style.display = 'block';
    
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}

// FDA Scraper
async function scrapeFDAData() {
    const statusDiv = document.getElementById('fda-scraper-status');
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '⏳ Fetching FDA shortage data...';
    
    try {
        const response = await fetch('/api/scrape-fda');
        const data = await response.json();
        
        if (data.success) {
            statusDiv.innerHTML = `✅ Found ${data.total_shortages} drug shortages`;
            
            // Auto-fill the form
            document.getElementById('pharma-mental').value = data.mental_health || 0;
            document.getElementById('pharma-adhd').value = data.adhd || 0;
            document.getElementById('pharma-antibiotics').value = data.antibiotics || 0;
            
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        } else {
            statusDiv.innerHTML = '❌ Failed to fetch FDA data. Please enter manually.';
        }
    } catch (error) {
        statusDiv.innerHTML = '❌ Error fetching data. Please enter manually.';
        console.error('FDA scraper error:', error);
    }
}