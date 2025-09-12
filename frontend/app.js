/**
 * Chess Platform - Main Application Controller
 * Configures routing and initializes the single-page application
 */

class ChessApp {
  constructor() {
    this.router = new ChessRouter();
    this.api = new ChessAPI();
    this.initialized = false;
  }

  // Initialize the application
  async init() {
    if (this.initialized) return;
    
    console.log('Initializing Chess Platform...');
    
    // Configure routes
    this.configureRoutes();
    
    // Initialize router
    await this.router.init();
    
    // Set up global event listeners
    this.setupGlobalEventListeners();
    
    this.initialized = true;
    console.log('Chess Platform initialized successfully');
  }

  // Configure application routes
  configureRoutes() {
    // Public routes (no authentication required)
    this.router.addRoute('/login', {
      title: 'Login - Chess Platform',
      template: 'src/pages/auth/login.html',
      public: true
    });

    this.router.addRoute('/register', {
      title: 'Register - Chess Platform',
      template: 'src/pages/auth/register.html',
      public: true
    });

    // Protected routes (authentication required)
    this.router.addRoute('/lobby', {
      title: 'Lobby - Chess Platform',
      template: 'src/pages/dashboard/lobby.html',
      requiresAuth: true
    });

    this.router.addRoute('/game/:id', {
      title: 'Game - Chess Platform',
      template: 'src/pages/game/play.html',
      requiresAuth: true,
      controller: (params) => {
        console.log('Loading game:', params.id);
      }
    });

    this.router.addRoute('/puzzles', {
      title: 'Puzzles - Chess Platform',
      template: 'src/pages/puzzles/puzzles.html',
      requiresAuth: true
    });

    this.router.addRoute('/profile', {
      title: 'Profile - Chess Platform',
      template: 'src/pages/profile/profile.html',
      requiresAuth: true
    });

    // Default route
    this.router.addRoute('/', {
      title: 'Chess Platform',
      public: true,
      controller: () => {
        // Redirect to appropriate page
        if (this.api.isAuthenticated()) {
          this.router.navigate('/lobby');
        } else {
          this.router.navigate('/login');
        }
      }
    });
  }

  // Set up global event listeners
  setupGlobalEventListeners() {
    // Handle route navigation clicks
    document.addEventListener('click', (e) => {
      const routeLink = e.target.closest('[data-route]');
      if (routeLink) {
        e.preventDefault();
        const route = routeLink.dataset.route;
        this.router.navigate(route);
      }
    });

    // Handle authentication state changes
    window.addEventListener('storage', (e) => {
      if (e.key === 'access') {
        // Token changed - refresh current route to check auth
        this.router.refresh();
      }
    });

    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.api.isAuthenticated()) {
        // Page became visible - refresh data
        this.refreshPageData();
      }
    });
  }

  // Refresh current page data
  refreshPageData() {
    const currentRoute = this.router.getCurrentRoute();
    
    // Trigger refresh based on current page
    if (currentRoute === '/lobby') {
      // Trigger lobby refresh if we're on lobby page
      const event = new CustomEvent('refreshLobby');
      window.dispatchEvent(event);
    }
  }

  // Get application instance
  static getInstance() {
    if (!window.chessApp) {
      window.chessApp = new ChessApp();
    }
    return window.chessApp;
  }
}

// Initialize application when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    ChessApp.getInstance().init();
  });
} else {
  ChessApp.getInstance().init();
}

// Make globally available
window.ChessApp = ChessApp;
