// Fetch data from stats.json
async function fetchMarathonData() {
    try {
        const response = await fetch('data/stats.json');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        // Return fallback data if fetch fails
        return {
            currentDay: 1,
            stats: {
                marathonSubs: 0,
                totalFollowers: 0,
                marathonFollowers: 0,
                totalChats: 0
            },
            dailySubs: { day1: 0 },
            topGifters: [],
            topChatters: []
        };
    }
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Update all stats on the page
async function updateStats() {
    const data = await fetchMarathonData();
    
    // Update current day
    document.getElementById('current-day').textContent = data.currentDay || 1;
    
    // Update main stats
    document.getElementById('marathon-subs').textContent = formatNumber(data.stats.marathonSubs || 0);
    document.getElementById('total-followers').textContent = formatNumber(data.stats.totalFollowers || 0);
    document.getElementById('marathon-followers').textContent = formatNumber(data.stats.marathonFollowers || 0);
    document.getElementById('total-chats').textContent = formatNumber(data.stats.totalChats || 0);
    
    // Update daily subs
    const currentDayKey = `day${data.currentDay || 1}`;
    const dailySubsCount = data.dailySubs?.[currentDayKey] || 0;
    document.getElementById('daily-subs-count').textContent = dailySubsCount;
    document.getElementById('current-day-number').textContent = data.currentDay || 1;
    
    // Update top gifters leaderboard
    const giftersContainer = document.getElementById('top-gifters-list');
    if (giftersContainer) {
        giftersContainer.innerHTML = '';
        const gifters = data.topGifters || [];
        gifters.slice(0, 10).forEach((gifter, index) => {
            const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
            const item = document.createElement('div');
            item.className = 'leaderboard-item';
            item.innerHTML = `
                <span>${medal} ${gifter.username}</span>
                <span>${gifter.amount} subs</span>
            `;
            giftersContainer.appendChild(item);
        });
    }
    
    // Update top chatters leaderboard
    const chattersContainer = document.getElementById('top-chatters-list');
    if (chattersContainer) {
        chattersContainer.innerHTML = '';
        const chatters = data.topChatters || [];
        chatters.slice(0, 10).forEach((chatter, index) => {
            const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
            const item = document.createElement('div');
            item.className = 'leaderboard-item';
            item.innerHTML = `
                <span>${medal} ${chatter.username}</span>
                <span>${formatNumber(chatter.messages)} messages</span>
            `;
            chattersContainer.appendChild(item);
        });
    }
    
    // Update marathon top gifters (same as regular, but featured)
    const marathonGiftersContainer = document.getElementById('marathon-gifters-list');
    if (marathonGiftersContainer) {
        marathonGiftersContainer.innerHTML = '';
        const gifters = data.topGifters || [];
        gifters.slice(0, 10).forEach((gifter, index) => {
            const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
            const item = document.createElement('div');
            item.className = 'leaderboard-item';
            item.innerHTML = `
                <span>${medal} ${gifter.username}</span>
                <span>${gifter.amount} total gifts</span>
            `;
            marathonGiftersContainer.appendChild(item);
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    updateStats();
    
    // Refresh data every 2 minutes
    setInterval(updateStats, 120000);
});
