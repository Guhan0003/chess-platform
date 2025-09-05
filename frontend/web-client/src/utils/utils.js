/**
 * Chess Platform - Client-Side Router
 * Handles navigation between pages without full page reloads
 */

class ChessRouter {
  constructor() {
    this.routes = {};
    this.currentRoute = null;
    this.isAuthenticated = false;
    
    // Initialize router
    this.init();
  }

  /**
   * Initialize the router
   */
  init() {
    // Check authentication status
    this.checkAuth();
    
    // Handle browser back/forward buttons
    window.addEventListener('popstate', (e) => {
      this.handleRoute(window.location.pathname, false);
    });

    // Handle initial page load
    this.handleRoute(window.location.pathname);
    
    // Set up link click handlers
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-route]')) {
        e.preventDefault();
        const route = e.target.getAttribute('data-route');
        this.navigate(route);
      }
    });
  }

  /**
   * Register a route
   * @param {string} path - Route path
   * @param {Object} config - Route configuration
   */
  addRoute(path, config) {
    this.routes[path] = {
      title: config.title || 'Chess Platform',
      template: config.template,
      controller: config.controller,
      requiresAuth: config.requiresAuth || false,
      public: config.public || false
    };
  }

  /**
   * Navigate to a route
   * @param {string} path - Route path
   * @param {boolean} pushState - Whether to push to history
   */
  navigate(path, pushState = true) {
    if (pushState) {
      history.pushState(null, null, path);
    }
    this.handleRoute(path);
  }

  /**
   * Handle route navigation
   * @param {string} path - Route path  
   * @param {boolean} pushState - Whether to push to history
   */
  async handleRoute(path, pushState = true) {
    // Remove query params and hash for route matching
    const cleanPath = path.split('?')[0].split('#')[0];
    
    // Find matching route
    let route = this.routes[cleanPath];
    
    // Default routes
    if (!route) {
      if (cleanPath === '/' || cleanPath === '/index.html' || cleanPath === '') {
        if (this.isAuthenticated) {
          return this.navigate('/lobby', pushState);
        } else {
          return this.navigate('/login', pushState);
        }
      }
      
      // 404 - redirect to appropriate page
      if (this.isAuthenticated) {
        return this.navigate('/lobby', pushState);
      } else {
        return this.navigate('/login', pushState);
      }
    }

    // Check authentication requirements
    if (route.requiresAuth && !this.isAuthenticated) {
      return this.navigate('/login', pushState);
    }
    
    if (route.public && this.isAuthenticated && (cleanPath === '/login' || cleanPath === '/register')) {
      return this.navigate('/lobby', pushState);
    }

    // Update current route
    this.currentRoute = cleanPath;
    
    // Update page title
    document.title = route.title;
    
    try {
      // Load and display the page
      await this.loadPage(route);
    } catch (error) {
      console.error('Error loading page:', error);
      this.showError('Failed to load page');
    }
  }

  /**
   * Load page content
   * @param {Object} route - Route configuration
   */
  async loadPage(route) {
    try {
      // Show loading state
      this.showLoading();
      
      // Load template
      let html;
      if (typeof route.template === 'string') {
        // Load from URL
        const response = await fetch(route.template);
        if (!response.ok) throw new Error(`Failed to load template: ${response.status}`);
        html = await response.text();
      } else if (typeof route.template === 'function') {
        // Generate from function
        html = route.template();
      } else {
        throw new Error('Invalid template configuration');
      }
      
      // Update page content
      const appContainer = document.getElementById('app');
      if (!appContainer) {
        throw new Error('App container not found');
      }
      
      appContainer.innerHTML = html;
      
      // Run controller if provided
      if (route.controller && typeof route.controller === 'function') {
        await route.controller();
      }
      
      // Hide loading state
      this.hideLoading();
      
      // Add fade-in animation
      appContainer.classList.add('fade-in');
      
    } catch (error) {
      this.hideLoading();
      throw error;
    }
  }

  /**
   * Check authentication status
   */
  checkAuth() {
    const token = localStorage.getItem('access');
    this.isAuthenticated = !!token;
    return this.isAuthenticated;
  }

  /**
   * Update authentication status
   * @param {boolean} status - Authentication status
   */
  setAuth(status) {
    this.isAuthenticated = status;
  }

  /**
   * Show loading state
   */
  showLoading() {
    const loader = document.getElementById('page-loader');
    if (loader) {
      loader.classList.remove('hidden');
    }
  }

  /**
   * Hide loading state  
   */
  hideLoading() {
    const loader = document.getElementById('page-loader');
    if (loader) {
      loader.classList.add('hidden');
    }
  }

  /**
   * Show error message
   * @param {string} message - Error message
   */
  showError(message) {
    // Create or update error element
    let errorEl = document.getElementById('router-error');
    if (!errorEl) {
      errorEl = document.createElement('div');
      errorEl.id = 'router-error';
      errorEl.className = 'error-message';
      document.body.appendChild(errorEl);
    }
    
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      errorEl.classList.add('hidden');
    }, 5000);
  }

  /**
   * Get current route
   */
  getCurrentRoute() {
    return this.currentRoute;
  }

  /**
   * Get route parameters from URL
   * @param {string} pattern - Route pattern with parameters
   */
  getParams(pattern = null) {
    const url = new URL(window.location.href);
    const params = {};
    
    // Get query parameters
    url.searchParams.forEach((value, key) => {
      params[key] = value;
    });
    
    // If pattern provided, extract path parameters
    if (pattern) {
      const pathParts = window.location.pathname.split('/');
      const patternParts = pattern.split('/');
      
      patternParts.forEach((part, index) => {
        if (part.startsWith(':')) {
          const paramName = part.substring(1);
          params[paramName] = pathParts[index];
        }
      });
    }
    
    return params;
  }

  /**
   * Redirect to a route
   * @param {string} path - Route path
   */
  redirect(path) {
    this.navigate(path);
  }

  /**
   * Go back in history
   */
  back() {
    history.back();
  }

  /**
   * Refresh current route
   */
  refresh() {
    this.handleRoute(window.location.pathname, false);
  }
}

// Create global router instance
const router = new ChessRouter();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ChessRouter;
}

// Make available globally
window.router = router;