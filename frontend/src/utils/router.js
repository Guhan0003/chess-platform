// Advanced Router for Chess Platform
class ChessRouter {
  constructor() {
    this.routes = {};
    this.currentRoute = null;
    this.initialized = false;
    
    // Listen to popstate events for browser back/forward
    window.addEventListener('popstate', (event) => {
      this.handleRoute(window.location.pathname, false);
    });
  }

  // Add a route with configuration
  addRoute(path, config) {
    this.routes[path] = {
      path: path,
      title: config.title || 'Chess Platform',
      template: config.template,
      controller: config.controller,
      public: config.public || false,
      requiresAuth: config.requiresAuth || false,
      ...config
    };
  }

  // Register a route with a callback (backward compatibility)
  register(path, callback) {
    this.routes[path] = { callback };
  }

  // Navigate to a route
  navigate(path, pushState = true) {
    if (pushState) {
      window.history.pushState(null, '', path);
    }
    this.handleRoute(path, pushState);
  }

  // Handle route changes
  async handleRoute(path, pushState = true) {
    this.currentRoute = path;
    
    // Find matching route (exact match first, then pattern matching)
    let route = this.routes[path];
    
    if (!route) {
      // Try pattern matching for routes like /game/:id
      for (const routePath in this.routes) {
        if (this.matchRoute(routePath, path)) {
          route = this.routes[routePath];
          break;
        }
      }
    }
    
    if (route) {
      // Set page title
      if (route.title) {
        document.title = route.title;
      }
      
      // Handle authentication requirements
      if (route.requiresAuth && !this.checkAuth()) {
        this.navigate('/login');
        return;
      }
      
      // Load template if specified
      if (route.template) {
        await this.loadTemplate(route.template);
      }
      
      // Execute controller
      if (route.controller) {
        route.controller(this.extractParams(route.path, path));
      } else if (route.callback) {
        route.callback();
      }
    } else {
      console.warn(`No route handler found for: ${path}`);
      // Default fallback - show error instead of redirecting to prevent loops
      this.showError(`Page not found: ${path}`);
    }
  }

  // Match route patterns like /game/:id
  matchRoute(pattern, path) {
    const patternParts = pattern.split('/');
    const pathParts = path.split('/');
    
    if (patternParts.length !== pathParts.length) {
      return false;
    }
    
    return patternParts.every((part, i) => {
      return part.startsWith(':') || part === pathParts[i];
    });
  }

  // Extract parameters from route like /game/:id
  extractParams(pattern, path) {
    const patternParts = pattern.split('/');
    const pathParts = path.split('/');
    const params = {};
    
    patternParts.forEach((part, i) => {
      if (part.startsWith(':')) {
        params[part.substring(1)] = pathParts[i];
      }
    });
    
    return params;
  }

  // Load template content
  async loadTemplate(templatePath) {
    try {
      const response = await fetch(templatePath);
      if (response.ok) {
        const html = await response.text();
        const app = document.getElementById('app');
        if (app) {
          app.innerHTML = html;
        }
      } else {
        console.error(`Failed to load template: ${templatePath}`);
        this.showError('Page not found');
      }
    } catch (error) {
      console.error(`Error loading template: ${templatePath}`, error);
      this.showError('Failed to load page');
    }
  }

  // Check if user is authenticated
  checkAuth() {
    // Simple check - you might want to implement more sophisticated auth
    return localStorage.getItem('access') !== null;
  }

  // Show error page
  showError(message) {
    const app = document.getElementById('app');
    if (app) {
      app.innerHTML = `
        <div class="error-page" style="text-align: center; padding: 50px;">
          <div class="error-icon" style="font-size: 48px;">⚠️</div>
          <h1 class="error-title">Oops! Something went wrong</h1>
          <p class="error-message">${message}</p>
          <button onclick="location.reload()" style="padding: 10px 20px; margin-top: 20px; background: #60a5fa; color: white; border: none; border-radius: 5px; cursor: pointer;">
            Refresh Page
          </button>
        </div>
      `;
    }
  }

  // Set authentication state
  setAuth(isAuthenticated) {
    // This method is called by API when auth state changes
    console.log('Auth state changed:', isAuthenticated);
  }

  // Initialize router
  async init() {
    this.initialized = true;
    
    // Start with current path or default to login
    const currentPath = window.location.pathname;
    if (currentPath === '/') {
      this.navigate('/login');
    } else {
      await this.handleRoute(currentPath, false);
    }
  }

  // Get current route
  getCurrentRoute() {
    return this.currentRoute;
  }

  // Refresh current route
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
