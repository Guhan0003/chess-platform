/**
 * Chess Platform - Friends Page
 * Handles friend management, requests, and real-time status updates
 */

// Initialize globals
let currentUser = null;
let friends = [];
let pendingRequests = [];
let sentRequests = [];
let currentFilter = 'all';
let searchTimeout = null;
let websocket = null;

// API instance is provided by api.js (global 'api' variable)

// =================================
// Initialization
// =================================

document.addEventListener('DOMContentLoaded', async () => {
  // Check authentication
  if (!api.isAuthenticated()) {
    window.location.href = '/login/';
    return;
  }
  
  // Initialize UI
  initializeEventListeners();
  
  // Load user data
  await loadUserProfile();
  
  // Load friends data
  await loadFriendsData();
  
  // Connect to WebSocket for real-time updates
  connectWebSocket();
});

// =================================
// User Profile
// =================================

async function loadUserProfile() {
  try {
    const response = await api.getUserProfile();
    if (response.ok) {
      currentUser = response.data;
      updateUserDisplay();
    }
  } catch (error) {
    console.error('Failed to load user profile:', error);
    showToast('Failed to load profile', 'error');
  }
}

function updateUserDisplay() {
  if (!currentUser) return;
  
  // Update sidebar user info
  const userAvatar = document.getElementById('userAvatar');
  const userName = document.getElementById('userName');
  const userRating = document.getElementById('userRating');
  
  if (userAvatar) {
    if (currentUser.avatar_url) {
      userAvatar.innerHTML = `<img src="${currentUser.avatar_url}" alt="${currentUser.username}">`;
    } else {
      userAvatar.textContent = currentUser.username.charAt(0).toUpperCase();
    }
  }
  
  if (userName) userName.textContent = currentUser.username;
  if (userRating) userRating.textContent = currentUser.rapid_rating || 1200;
  
  // Update unique ID display
  const uniqueId = currentUser.unique_id || generateLocalId(currentUser.id);
  document.getElementById('uniqueIdValue').textContent = uniqueId;
  document.getElementById('qrIdDisplay').textContent = uniqueId;
  
  // Generate QR code
  generateQRCode(uniqueId);
}

function generateLocalId(userId) {
  // Generate a readable unique ID from user ID
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let id = '';
  let num = userId * 1000 + Math.floor(Date.now() / 1000) % 1000;
  
  for (let i = 0; i < 8; i++) {
    id += chars[num % chars.length];
    num = Math.floor(num / chars.length);
  }
  
  return id.substring(0, 4) + '-' + id.substring(4);
}

// =================================
// Friends Data Loading
// =================================

async function loadFriendsData() {
  try {
    // Load all friend-related data in parallel
    const [friendsRes, pendingRes, sentRes] = await Promise.all([
      api.request('/auth/friends/'),
      api.request('/auth/friends/requests/pending/'),
      api.request('/auth/friends/requests/sent/')
    ]);
    
    if (friendsRes.ok) {
      friends = friendsRes.data || [];
    }
    
    if (pendingRes.ok) {
      pendingRequests = pendingRes.data || [];
    }
    
    if (sentRes.ok) {
      sentRequests = sentRes.data || [];
    }
    
    // Update displays
    updateFriendsDisplay();
    updatePendingRequestsDisplay();
    updateSentRequestsDisplay();
    updateFilterCounts();
    updateOnlineFriendsQuick();
    
  } catch (error) {
    console.error('Failed to load friends data:', error);
    // Show empty state instead of error for graceful degradation
    showEmptyFriendsState();
  }
}

// =================================
// Friends Display
// =================================

function updateFriendsDisplay() {
  const container = document.getElementById('friendsList');
  
  // Filter friends based on current filter
  let filteredFriends = friends;
  const searchTerm = document.getElementById('friendsFilterInput')?.value.toLowerCase() || '';
  
  if (searchTerm) {
    filteredFriends = filteredFriends.filter(f => 
      f.username.toLowerCase().includes(searchTerm) ||
      (f.unique_id && f.unique_id.toLowerCase().includes(searchTerm))
    );
  }
  
  if (currentFilter !== 'all') {
    filteredFriends = filteredFriends.filter(f => f.status === currentFilter);
  }
  
  if (filteredFriends.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">👥</div>
        <div class="empty-title">${searchTerm ? 'No friends found' : 'No friends yet'}</div>
        <div class="empty-description">
          ${searchTerm 
            ? 'Try a different search term' 
            : 'Add friends to start playing together!'}
        </div>
      </div>
    `;
    return;
  }
  
  // Sort friends: online first, then playing, then offline
  const statusOrder = { 'online': 0, 'playing': 1, 'offline': 2 };
  filteredFriends.sort((a, b) => (statusOrder[a.status] || 2) - (statusOrder[b.status] || 2));
  
  // Group friends by status
  const grouped = {
    online: filteredFriends.filter(f => f.status === 'online'),
    playing: filteredFriends.filter(f => f.status === 'playing'),
    offline: filteredFriends.filter(f => f.status === 'offline')
  };
  
  let html = '';
  
  if (currentFilter === 'all') {
    // Show categorized view
    if (grouped.online.length > 0) {
      html += renderFriendCategory('🟢', 'Online', grouped.online);
    }
    if (grouped.playing.length > 0) {
      html += renderFriendCategory('🎮', 'In Game', grouped.playing);
    }
    if (grouped.offline.length > 0) {
      html += renderFriendCategory('⚪', 'Offline', grouped.offline);
    }
  } else {
    // Show flat list for filtered view
    html = filteredFriends.map(f => renderFriendCard(f)).join('');
  }
  
  container.innerHTML = html;
  
  // Attach event listeners
  attachFriendCardListeners();
}

function renderFriendCategory(icon, title, friendsList) {
  return `
    <div class="friends-category">
      <div class="category-header">
        <span class="category-icon">${icon}</span>
        ${title}
        <span class="category-count">${friendsList.length}</span>
      </div>
      ${friendsList.map(f => renderFriendCard(f)).join('')}
    </div>
  `;
}

function renderFriendCard(friend) {
  const statusClass = friend.status || 'offline';
  const isPlaying = friend.status === 'playing';
  const lastSeen = friend.last_seen ? formatLastSeen(friend.last_seen) : '';
  
  return `
    <div class="friend-card ${statusClass}" data-user-id="${friend.id}">
      <div class="friend-avatar">
        ${friend.avatar_url 
          ? `<img src="${friend.avatar_url}" alt="${friend.username}">` 
          : friend.username.charAt(0).toUpperCase()}
        <div class="friend-status-indicator ${statusClass}"></div>
      </div>
      <div class="friend-info">
        <div class="friend-name">${escapeHtml(friend.username)}</div>
        <div class="friend-details">
          <span class="friend-rating">⭐ ${friend.rating || 1200}</span>
          ${isPlaying 
            ? `<span class="playing-badge">🎮 Playing</span>` 
            : friend.status === 'offline' && lastSeen 
              ? `<span class="friend-status-text">${lastSeen}</span>`
              : `<span class="friend-status-text">${statusClass === 'online' ? '🟢 Online' : ''}</span>`
          }
        </div>
      </div>
      <div class="friend-actions">
        ${isPlaying && friend.game_id && friend.game_public 
          ? `<button class="watch-btn" data-game-id="${friend.game_id}">👁 Watch</button>` 
          : ''
        }
        ${friend.status === 'online' 
          ? `<button class="challenge-btn" data-user-id="${friend.id}">⚔️ Challenge</button>` 
          : ''
        }
        <button class="more-btn" data-user-id="${friend.id}" title="More options">⋮</button>
      </div>
    </div>
  `;
}

function showEmptyFriendsState() {
  const container = document.getElementById('friendsList');
  container.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">👥</div>
      <div class="empty-title">No friends yet</div>
      <div class="empty-description">
        Search for players and send friend requests to start building your network!
      </div>
      <button class="empty-action" onclick="document.getElementById('usernameInput').focus()">
        Find Friends
      </button>
    </div>
  `;
}

// =================================
// Pending Requests Display
// =================================

function updatePendingRequestsDisplay() {
  const section = document.getElementById('pendingRequestsSection');
  const container = document.getElementById('pendingRequestsList');
  const countEl = document.getElementById('requestCount');
  
  if (pendingRequests.length === 0) {
    section.style.display = 'none';
    return;
  }
  
  section.style.display = 'block';
  countEl.textContent = pendingRequests.length;
  
  container.innerHTML = pendingRequests.map(req => `
    <div class="request-item" data-request-id="${req.id}">
      <div class="request-avatar">
        ${req.from_user.avatar_url 
          ? `<img src="${req.from_user.avatar_url}" alt="${req.from_user.username}">` 
          : req.from_user.username.charAt(0).toUpperCase()}
      </div>
      <div class="request-info">
        <div class="request-name">${escapeHtml(req.from_user.username)}</div>
        <div class="request-time">${formatTimeAgo(req.created_at)}</div>
      </div>
      <div class="request-actions">
        <button class="accept-btn" data-request-id="${req.id}">Accept</button>
        <button class="decline-btn" data-request-id="${req.id}">Decline</button>
      </div>
    </div>
  `).join('');
  
  // Attach event listeners
  container.querySelectorAll('.accept-btn').forEach(btn => {
    btn.addEventListener('click', () => handleAcceptRequest(btn.dataset.requestId));
  });
  
  container.querySelectorAll('.decline-btn').forEach(btn => {
    btn.addEventListener('click', () => handleDeclineRequest(btn.dataset.requestId));
  });
}

// =================================
// Sent Requests Display
// =================================

function updateSentRequestsDisplay() {
  const section = document.getElementById('sentRequestsSection');
  const container = document.getElementById('sentRequestsList');
  const countEl = document.getElementById('sentCount');
  
  if (sentRequests.length === 0) {
    section.style.display = 'none';
    return;
  }
  
  section.style.display = 'block';
  countEl.textContent = sentRequests.length;
  
  container.innerHTML = sentRequests.map(req => `
    <div class="request-item" data-request-id="${req.id}">
      <div class="request-avatar">
        ${req.to_user.avatar_url 
          ? `<img src="${req.to_user.avatar_url}" alt="${req.to_user.username}">` 
          : req.to_user.username.charAt(0).toUpperCase()}
      </div>
      <div class="request-info">
        <div class="request-name">${escapeHtml(req.to_user.username)}</div>
        <div class="request-time">Sent ${formatTimeAgo(req.created_at)}</div>
      </div>
      <button class="decline-btn" data-request-id="${req.id}">Cancel</button>
    </div>
  `).join('');
  
  // Attach event listeners
  container.querySelectorAll('.decline-btn').forEach(btn => {
    btn.addEventListener('click', () => handleCancelRequest(btn.dataset.requestId));
  });
}

// =================================
// Filter & Count Updates
// =================================

function updateFilterCounts() {
  const counts = {
    all: friends.length,
    online: friends.filter(f => f.status === 'online').length,
    playing: friends.filter(f => f.status === 'playing').length,
    offline: friends.filter(f => f.status === 'offline').length
  };
  
  document.getElementById('allCount').textContent = counts.all;
  document.getElementById('onlineCount').textContent = counts.online;
  document.getElementById('playingCount').textContent = counts.playing;
  document.getElementById('offlineCount').textContent = counts.offline;
}

function updateOnlineFriendsQuick() {
  const container = document.getElementById('onlineFriendsQuick');
  const onlineFriends = friends.filter(f => f.status === 'online' || f.status === 'playing').slice(0, 5);
  
  if (onlineFriends.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="padding: var(--space-lg);">
        <div class="empty-icon" style="font-size: 2rem;">👥</div>
        <div class="empty-description">No friends online</div>
      </div>
    `;
    return;
  }
  
  container.innerHTML = onlineFriends.map(f => `
    <div class="friend-card ${f.status}" data-user-id="${f.id}" style="margin-bottom: var(--space-xs);">
      <div class="friend-avatar" style="width: 36px; height: 36px; font-size: var(--font-size-base);">
        ${f.avatar_url 
          ? `<img src="${f.avatar_url}" alt="${f.username}">` 
          : f.username.charAt(0).toUpperCase()}
        <div class="friend-status-indicator ${f.status}" style="width: 10px; height: 10px;"></div>
      </div>
      <div class="friend-info">
        <div class="friend-name" style="font-size: var(--font-size-sm);">${escapeHtml(f.username)}</div>
        <div class="friend-details" style="font-size: var(--font-size-xs);">
          ${f.status === 'playing' ? '🎮 Playing' : '🟢 Online'}
        </div>
      </div>
    </div>
  `).join('');
}

// =================================
// Event Listeners
// =================================

function initializeEventListeners() {
  // Mobile menu toggle
  document.getElementById('mobileMenuBtn')?.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
  
  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      
      // Update active tab button
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      // Show corresponding content
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      document.getElementById(`tab-${tabId}`).classList.add('active');
    });
  });
  
  // Filter buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      currentFilter = btn.dataset.filter;
      
      // Update active state
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      // Update display
      updateFriendsDisplay();
    });
  });
  
  // Username search form
  document.getElementById('usernameSearchForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await searchByUsername();
  });
  
  // Unique ID search form
  document.getElementById('idSearchForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await searchByUniqueId();
  });
  
  // Friends search filter (real-time)
  document.getElementById('friendsFilterInput')?.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      updateFriendsDisplay();
    }, 300);
  });
  
  // Copy ID button
  document.getElementById('copyIdBtn')?.addEventListener('click', copyUniqueId);
  
  // QR modal buttons
  document.getElementById('showQrBtn')?.addEventListener('click', () => {
    document.getElementById('qrModal').classList.add('active');
  });
  
  document.getElementById('closeQrModal')?.addEventListener('click', () => {
    document.getElementById('qrModal').classList.remove('active');
  });
  
  document.getElementById('qrModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'qrModal') {
      document.getElementById('qrModal').classList.remove('active');
    }
  });
  
  // Header Add Friend button
  document.getElementById('headerAddFriend')?.addEventListener('click', () => {
    document.getElementById('usernameInput')?.focus();
    document.getElementById('addFriendSection')?.scrollIntoView({ behavior: 'smooth' });
  });
  
  // Logout button
  document.getElementById('logout-btn')?.addEventListener('click', async () => {
    if (confirm('Are you sure you want to logout?')) {
      await api.logout();
    }
  });
  
  // User profile click
  document.getElementById('userProfile')?.addEventListener('click', () => {
    window.location.href = '/profile/';
  });
}

function attachFriendCardListeners() {
  // Challenge buttons
  document.querySelectorAll('.challenge-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const userId = btn.dataset.userId;
      handleChallengeFriend(userId);
    });
  });
  
  // Watch buttons
  document.querySelectorAll('.watch-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const gameId = btn.dataset.gameId;
      window.location.href = `/game/${gameId}/?spectate=true`;
    });
  });
  
  // More buttons (placeholder for dropdown menu)
  document.querySelectorAll('.more-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      // TODO: Show dropdown menu with options like Remove Friend, View Profile, etc.
      showToast('More options coming soon!', 'info');
    });
  });
  
  // Friend card click - view profile
  document.querySelectorAll('.friend-card').forEach(card => {
    card.addEventListener('click', () => {
      const userId = card.dataset.userId;
      window.location.href = `/profile/?id=${userId}`;
    });
  });
}

// =================================
// Search Functions
// =================================

async function searchByUsername() {
  const input = document.getElementById('usernameInput');
  const resultsContainer = document.getElementById('usernameSearchResults');
  const query = input.value.trim();
  
  if (!query) {
    showToast('Please enter a username', 'error');
    return;
  }
  
  const btn = document.getElementById('usernameSearchBtn');
  btn.disabled = true;
  btn.textContent = 'Searching...';
  
  try {
    const response = await api.request(`/auth/search/?q=${encodeURIComponent(query)}&limit=10`);
    
    if (response.ok && response.data && response.data.results) {
      displaySearchResults(response.data.results, resultsContainer);
    } else {
      resultsContainer.innerHTML = `
        <div class="empty-state" style="padding: var(--space-lg);">
          <div class="empty-icon" style="font-size: 2rem;">🔍</div>
          <div class="empty-description">No users found</div>
        </div>
      `;
    }
  } catch (error) {
    console.error('Search failed:', error);
    showToast('Search failed. Please try again.', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Search';
  }
}

async function searchByUniqueId() {
  const input = document.getElementById('uniqueIdInput');
  const resultsContainer = document.getElementById('idSearchResults');
  const uniqueId = input.value.trim().toUpperCase();
  
  if (!uniqueId) {
    showToast('Please enter a unique ID', 'error');
    return;
  }
  
  const btn = document.getElementById('idSearchBtn');
  btn.disabled = true;
  btn.textContent = 'Searching...';
  
  try {
    const response = await api.request(`/auth/friends/find-by-id/?unique_id=${encodeURIComponent(uniqueId)}`);
    
    if (response.ok && response.data) {
      displaySearchResults([response.data], resultsContainer);
    } else {
      resultsContainer.innerHTML = `
        <div class="empty-state" style="padding: var(--space-lg);">
          <div class="empty-icon" style="font-size: 2rem;">🔍</div>
          <div class="empty-description">No user found with this ID</div>
        </div>
      `;
    }
  } catch (error) {
    console.error('Search failed:', error);
    resultsContainer.innerHTML = `
      <div class="empty-state" style="padding: var(--space-lg);">
        <div class="empty-icon" style="font-size: 2rem;">🔍</div>
        <div class="empty-description">No user found with this ID</div>
      </div>
    `;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Find User';
  }
}

function displaySearchResults(users, container) {
  if (!users || users.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="padding: var(--space-lg);">
        <div class="empty-icon" style="font-size: 2rem;">🔍</div>
        <div class="empty-description">No users found</div>
      </div>
    `;
    return;
  }
  
  container.innerHTML = users.map(user => {
    // Check relationship status
    const isSelf = currentUser && user.id === currentUser.id;
    const isFriend = friends.some(f => f.id === user.id);
    const hasPendingRequest = sentRequests.some(r => r.to_user.id === user.id);
    const hasIncomingRequest = pendingRequests.some(r => r.from_user.id === user.id);
    
    let buttonHtml = '';
    if (isSelf) {
      buttonHtml = `<span class="add-friend-btn self">You</span>`;
    } else if (isFriend) {
      buttonHtml = `<span class="add-friend-btn friends">Friends ✓</span>`;
    } else if (hasPendingRequest) {
      buttonHtml = `<span class="add-friend-btn pending">Pending...</span>`;
    } else if (hasIncomingRequest) {
      buttonHtml = `<button class="accept-btn" data-user-id="${user.id}">Accept Request</button>`;
    } else {
      buttonHtml = `<button class="add-friend-btn" data-user-id="${user.id}">Add Friend</button>`;
    }
    
    return `
      <div class="search-result-item" data-user-id="${user.id}">
        <div class="result-avatar">
          ${user.avatar_url 
            ? `<img src="${user.avatar_url}" alt="${user.username}">` 
            : user.username.charAt(0).toUpperCase()}
        </div>
        <div class="result-info">
          <div class="result-name">${escapeHtml(user.username)}</div>
          <div class="result-details">
            <span class="result-rating">⭐ ${user.rapid_rating || user.rating || 1200}</span>
            <span class="result-status">
              <span class="status-dot ${user.is_online ? 'online' : 'offline'}"></span>
              ${user.is_online ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
        ${buttonHtml}
      </div>
    `;
  }).join('');
  
  // Attach event listeners
  container.querySelectorAll('.add-friend-btn[data-user-id]').forEach(btn => {
    btn.addEventListener('click', () => handleSendFriendRequest(btn.dataset.userId));
  });
  
  container.querySelectorAll('.accept-btn[data-user-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      const request = pendingRequests.find(r => r.from_user.id === parseInt(btn.dataset.userId));
      if (request) {
        handleAcceptRequest(request.id);
      }
    });
  });
}

// =================================
// Friend Request Handlers
// =================================

async function handleSendFriendRequest(userId) {
  try {
    const response = await api.request('/auth/friends/request/', {
      method: 'POST',
      body: JSON.stringify({ to_user_id: userId })
    });
    
    if (response.ok) {
      showToast('Friend request sent!', 'success');
      
      // Add to sent requests for immediate UI update
      if (response.data) {
        sentRequests.push(response.data);
      }
      
      // Refresh data
      await loadFriendsData();
    } else {
      showToast(response.message || 'Failed to send request', 'error');
    }
  } catch (error) {
    console.error('Failed to send friend request:', error);
    showToast('Failed to send request', 'error');
  }
}

async function handleAcceptRequest(requestId) {
  try {
    const response = await api.request(`/auth/friends/request/${requestId}/accept/`, {
      method: 'POST'
    });
    
    if (response.ok) {
      showToast('Friend request accepted!', 'success');
      
      // Remove from pending requests
      pendingRequests = pendingRequests.filter(r => r.id !== parseInt(requestId));
      
      // Refresh friends list
      await loadFriendsData();
    } else {
      showToast(response.message || 'Failed to accept request', 'error');
    }
  } catch (error) {
    console.error('Failed to accept request:', error);
    showToast('Failed to accept request', 'error');
  }
}

async function handleDeclineRequest(requestId) {
  try {
    const response = await api.request(`/auth/friends/request/${requestId}/reject/`, {
      method: 'POST'
    });
    
    if (response.ok) {
      showToast('Friend request declined', 'info');
      
      // Remove from pending requests
      pendingRequests = pendingRequests.filter(r => r.id !== parseInt(requestId));
      
      // Update display
      updatePendingRequestsDisplay();
    } else {
      showToast(response.message || 'Failed to decline request', 'error');
    }
  } catch (error) {
    console.error('Failed to decline request:', error);
    showToast('Failed to decline request', 'error');
  }
}

async function handleCancelRequest(requestId) {
  try {
    const response = await api.request(`/auth/friends/request/${requestId}/cancel/`, {
      method: 'POST'
    });
    
    if (response.ok) {
      showToast('Friend request cancelled', 'info');
      
      // Remove from sent requests
      sentRequests = sentRequests.filter(r => r.id !== parseInt(requestId));
      
      // Update display
      updateSentRequestsDisplay();
    } else {
      showToast(response.message || 'Failed to cancel request', 'error');
    }
  } catch (error) {
    console.error('Failed to cancel request:', error);
    showToast('Failed to cancel request', 'error');
  }
}

async function handleChallengeFriend(userId) {
  showToast('Challenge feature coming soon!', 'info');
  // TODO: Implement challenge modal/flow
}

// =================================
// Utility Functions
// =================================

function copyUniqueId() {
  const uniqueId = document.getElementById('uniqueIdValue').textContent;
  
  navigator.clipboard.writeText(uniqueId).then(() => {
    const btn = document.getElementById('copyIdBtn');
    btn.innerHTML = '<span>✓</span> Copied!';
    btn.classList.add('copied');
    
    showToast('ID copied to clipboard!', 'success');
    
    setTimeout(() => {
      btn.innerHTML = '<span>📋</span> Copy ID';
      btn.classList.remove('copied');
    }, 2000);
  }).catch(() => {
    showToast('Failed to copy ID', 'error');
  });
}

function generateQRCode(uniqueId) {
  const container = document.getElementById('qrContainer');
  
  // Create a simple QR code placeholder or use a library
  // For now, we'll create a stylized display
  container.innerHTML = `
    <div style="
      width: 200px;
      height: 200px;
      background: white;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      margin: 0 auto;
      border-radius: 8px;
    ">
      <div style="
        font-family: monospace;
        font-size: 24px;
        font-weight: bold;
        color: #333;
        text-align: center;
        word-break: break-all;
      ">${uniqueId}</div>
    </div>
    <p style="margin-top: 12px; font-size: 12px; color: #666;">
      QR code generation requires additional library
    </p>
  `;
  
  // If you want to use a QR code library, you can add it here
  // Example with qrcode.js:
  // new QRCode(container, {
  //   text: `chess-friend:${uniqueId}`,
  //   width: 200,
  //   height: 200
  // });
}

function formatTimeAgo(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  
  if (diffSec < 60) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return date.toLocaleDateString();
}

function formatLastSeen(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  
  if (diffMin < 5) return 'Last seen just now';
  if (diffMin < 60) return `Last seen ${diffMin}m ago`;
  if (diffHour < 24) return `Last seen ${diffHour}h ago`;
  if (diffDay < 7) return `Last seen ${diffDay}d ago`;
  return `Last seen ${date.toLocaleDateString()}`;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  
  const icons = {
    success: '✓',
    error: '✕',
    info: 'ℹ',
    warning: '⚠'
  };
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-message">${escapeHtml(message)}</span>
  `;
  
  container.appendChild(toast);
  
  // Auto remove after 4 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// =================================
// WebSocket Connection
// =================================

function connectWebSocket() {
  // Determine WebSocket URL
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = window.location.hostname;
  const wsPort = window.location.port || (window.location.protocol === 'https:' ? '443' : '8000');
  const wsUrl = `${wsProtocol}//${wsHost}:${wsPort}/ws/friends/`;
  
  try {
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('Friends WebSocket connected');
      
      // Send authentication
      const token = localStorage.getItem('access');
      if (token) {
        websocket.send(JSON.stringify({
          type: 'authenticate',
          token: token
        }));
      }
    };
    
    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };
    
    websocket.onclose = () => {
      console.log('Friends WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(connectWebSocket, 5000);
    };
    
    websocket.onerror = (error) => {
      console.error('Friends WebSocket error:', error);
    };
  } catch (error) {
    console.error('Failed to connect WebSocket:', error);
    // Fallback to polling
    startPolling();
  }
}

function handleWebSocketMessage(data) {
  switch (data.type) {
    case 'friend_status_update':
      // Update friend status
      const friend = friends.find(f => f.id === data.user_id);
      if (friend) {
        friend.status = data.status;
        friend.game_id = data.game_id;
        friend.game_public = data.game_public;
        updateFriendsDisplay();
        updateFilterCounts();
        updateOnlineFriendsQuick();
      }
      break;
      
    case 'friend_request_received':
      showToast(`${data.from_username} sent you a friend request!`, 'info');
      loadFriendsData();
      break;
      
    case 'friend_request_accepted':
      showToast(`${data.username} accepted your friend request!`, 'success');
      loadFriendsData();
      break;
      
    case 'friend_removed':
      friends = friends.filter(f => f.id !== data.user_id);
      updateFriendsDisplay();
      updateFilterCounts();
      break;
  }
}

function startPolling() {
  // Fallback polling for friend status updates
  setInterval(async () => {
    try {
      const response = await api.request('/auth/friends/status/');
      if (response.ok && response.data) {
        // Update friend statuses
        response.data.forEach(update => {
          const friend = friends.find(f => f.id === update.user_id);
          if (friend) {
            friend.status = update.status;
            friend.game_id = update.game_id;
            friend.game_public = update.game_public;
          }
        });
        updateFriendsDisplay();
        updateFilterCounts();
        updateOnlineFriendsQuick();
      }
    } catch (error) {
      console.error('Polling failed:', error);
    }
  }, 30000); // Poll every 30 seconds
}
