// Executive Dashboard JavaScript

let executiveData = null;
let refreshTimer = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadExecutiveData();
    // Refresh every 30 seconds
    refreshTimer = setInterval(loadExecutiveData, 30000);
});

// Load data from API
async function loadExecutiveData() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        executiveData = data;
        updateExecutiveDashboard(data);
    } catch (error) {
        console.error('Failed to load data:', error);
    }
}

// Update all dashboard components
function updateExecutiveDashboard(data) {
    // Update timestamp
    const lastUpdate = new Date(data.timestamp);
    document.getElementById('last-update-exec').textContent = 
        `Last update: ${lastUpdate.toLocaleTimeString()}`;
    
    // Update phase and actions
    updatePhaseAndActions(data);
    
    // Update alert summary
    updateAlertSummary(data);
    
    // Update heat map
    updateHeatMap(data);
    
    // Update critical indicators
    updateCriticalIndicators(data);
    
    // Update trends (simplified for now)
    updateTrends(data);
}

// Update phase and immediate actions
function updatePhaseAndActions(data) {
    const phaseElement = document.getElementById('exec-phase');
    const phaseNameElement = document.getElementById('exec-phase-name');
    const actionList = document.getElementById('action-list');
    
    // Set phase
    const currentPhase = data.current_phase || 0;
    phaseElement.textContent = currentPhase;
    phaseElement.className = currentPhase >= 5 ? 'phase-value high-phase' : 'phase-value';
    
    // Set phase name and headline
    const phaseInfo = data.phase_info || {};
    phaseNameElement.textContent = phaseInfo.headline || phaseInfo.name || `Phase ${currentPhase}`;
    
    // Update HOPI information
    if (data.hopi) {
        document.getElementById('exec-hopi').textContent = data.hopi.score.toFixed(1);
        document.getElementById('exec-confidence').textContent = data.hopi.confidence.toFixed(0) + '%';
        
        // Color HOPI score
        const hopiEl = document.getElementById('exec-hopi');
        if (data.hopi.score >= 70) {
            hopiEl.className = 'hopi-value red';
        } else if (data.hopi.score >= 35) {
            hopiEl.className = 'hopi-value amber';
        } else {
            hopiEl.className = 'hopi-value green';
        }
    }
    
    // Set immediate actions
    actionList.innerHTML = '';
    
    if (data.tighten_up) {
        // TIGHTEN-UP actions take priority
        const tightenActions = [
            'TOP OFF: Gas tank, get cash from ATM',
            'CHARGE: All devices, power banks, batteries',
            'CHECK: Food, water, medications, first aid',
            'REVIEW: Emergency contacts and rally points',
            'MONITOR: News and this dashboard closely'
        ];
        
        tightenActions.forEach(action => {
            const li = document.createElement('li');
            li.textContent = action;
            li.style.color = '#ffa726';
            actionList.appendChild(li);
        });
    } else if (phaseInfo.actions && phaseInfo.actions.length > 0) {
        // Show top 3 phase actions
        phaseInfo.actions.slice(0, 3).forEach(action => {
            const li = document.createElement('li');
            li.textContent = action;
            actionList.appendChild(li);
        });
    } else {
        // Default actions
        const li = document.createElement('li');
        li.textContent = 'Continue normal monitoring';
        actionList.appendChild(li);
    }
}

// Update alert summary counts
function updateAlertSummary(data) {
    let redCount = 0;
    let amberCount = 0;
    let greenCount = 0;
    
    data.indicators.forEach(indicator => {
        switch(indicator.level.toLowerCase()) {
            case 'red':
                redCount++;
                break;
            case 'amber':
                amberCount++;
                break;
            case 'green':
                greenCount++;
                break;
        }
    });
    
    document.getElementById('red-indicators').textContent = redCount;
    document.getElementById('amber-indicators').textContent = amberCount;
    document.getElementById('green-indicators').textContent = greenCount;
}

// Update heat map
function updateHeatMap(data) {
    const heatMap = document.getElementById('heat-map');
    heatMap.innerHTML = '';
    
    // Organize indicators by category
    const categories = {
        'Economy & Jobs': ['Treasury', 'GroceryCPI', 'JoblessClaims', 'StrikeTracker', 'GDPGrowth'],
        'Rights & Security': ['LegiScan', 'ACLEDProtests', 'CISACyber', 'GridOutages'],
        'Oil Axis': ['CREAOil', 'MBridgeSettlements', 'OFACDesignations', 'JODIOil'],
        'AI Window': ['AILayoffs', 'AIRansomware', 'DeepfakeShocks', 'MarketVolatility', 'WHODisease'],
        'Cult Signals': ['TwitterCult', 'EtherscanTokens', 'ACLEDCult', 'GoogleTrendsAI']
    };
    
    Object.entries(categories).forEach(([category, indicators]) => {
        const row = document.createElement('div');
        row.className = 'category-row';
        
        // Category label
        const label = document.createElement('div');
        label.className = 'category-label';
        label.textContent = category;
        row.appendChild(label);
        
        // Indicator tiles
        indicators.forEach(indicatorName => {
            const indicator = data.indicators.find(i => i.name === indicatorName);
            const tile = document.createElement('div');
            tile.className = `indicator-tile ${indicator ? indicator.level.toLowerCase() : 'unknown'}`;
            tile.textContent = indicatorName.replace(/([A-Z])/g, ' $1').trim().split(' ')[0];
            
            // Add tooltip
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = indicator ? `${indicatorName}: ${indicator.value}` : `${indicatorName}: No Data`;
            tile.appendChild(tooltip);
            
            tile.onclick = () => showIndicatorDetail(indicatorName);
            row.appendChild(tile);
        });
        
        heatMap.appendChild(row);
    });
}

// Update critical indicators
function updateCriticalIndicators(data) {
    const criticalGrid = document.getElementById('critical-grid');
    criticalGrid.innerHTML = '';
    
    // Define critical indicators
    const criticalNames = ['MarketVolatility', 'DeepfakeShocks', 'AIRansomware', 'WHODisease'];
    
    criticalNames.forEach(name => {
        const indicator = data.indicators.find(i => i.name === name);
        if (!indicator) return;
        
        const div = document.createElement('div');
        div.className = 'critical-indicator';
        
        const info = document.createElement('div');
        info.className = 'critical-info';
        
        const title = document.createElement('h4');
        title.textContent = getIndicatorTitle(name);
        info.appendChild(title);
        
        const desc = document.createElement('p');
        desc.textContent = getIndicatorShortDesc(name);
        info.appendChild(desc);
        
        const value = document.createElement('div');
        value.className = 'critical-value';
        value.textContent = indicator.value;
        value.style.color = indicator.level === 'red' ? '#ef4444' : 
                           indicator.level === 'amber' ? '#f59e0b' : '#10b981';
        
        div.appendChild(info);
        div.appendChild(value);
        criticalGrid.appendChild(div);
    });
}

// Update trend charts (simplified)
function updateTrends(data) {
    const trendsGrid = document.getElementById('trends-grid');
    trendsGrid.innerHTML = '';
    
    // Show top changing indicators
    const trendIndicators = ['Treasury', 'MarketVolatility', 'CREAOil', 'AILayoffs'];
    
    trendIndicators.forEach(name => {
        const indicator = data.indicators.find(i => i.name === name);
        if (!indicator) return;
        
        const card = document.createElement('div');
        card.className = 'trend-card';
        
        const header = document.createElement('div');
        header.className = 'trend-header';
        
        const nameSpan = document.createElement('span');
        nameSpan.className = 'trend-name';
        nameSpan.textContent = name;
        
        const changeSpan = document.createElement('span');
        changeSpan.className = 'trend-change positive';
        changeSpan.textContent = '↑ 5%'; // Would calculate real change
        
        header.appendChild(nameSpan);
        header.appendChild(changeSpan);
        card.appendChild(header);
        
        // Placeholder for mini chart
        const chart = document.createElement('div');
        chart.className = 'trend-chart';
        chart.style.background = 'linear-gradient(to right, #10b981, #f59e0b, #ef4444)';
        chart.style.opacity = '0.3';
        card.appendChild(chart);
        
        trendsGrid.appendChild(card);
    });
}

// Helper functions
function getIndicatorTitle(name) {
    const titles = {
        'MarketVolatility': '📊 Bond Market Shock',
        'DeepfakeShocks': '🎭 Deepfake Events',
        'AIRansomware': '🔓 AI Ransomware',
        'WHODisease': '🦠 Disease Outbreak'
    };
    return titles[name] || name;
}

function getIndicatorShortDesc(name) {
    const descriptions = {
        'MarketVolatility': '10Y Treasury intraday volatility',
        'DeepfakeShocks': 'Market shocks from deepfakes',
        'AIRansomware': 'AI-assisted ransomware attacks',
        'WHODisease': 'Countries with H2H transmission'
    };
    return descriptions[name] || '';
}

function showIndicatorDetail(indicatorName) {
    // In production, would show modal with details
    console.log('Show details for:', indicatorName);
    // Could redirect to main dashboard with indicator highlighted
    window.location.href = `/?highlight=${indicatorName}`;
}