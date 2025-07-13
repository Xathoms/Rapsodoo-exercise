/**
 * RefreshManager class for handling intelligent page refresh functionality.
 *
 * This class implements smart refresh strategies that minimize unnecessary page reloads
 * while ensuring users see updated data when available. It includes user activity
 * tracking, visibility detection, and soft refresh mechanisms.
 *
 *
 * @class RefreshManager
 */
class RefreshManager {
  /**
   * Initialize the refresh manager with configuration.
   *
   * Sets up activity tracking, visibility monitoring, and refresh intervals
   */
  constructor() {
    this.refreshInterval = null;
    this.lastActivity = Date.now();
    this.isVisible = true;

    this.refreshIntervalMinutes =
      window.appConfig?.refreshIntervalMinutes || 60;
    this.maxInactiveMinutes = window.appConfig?.maxInactiveMinutes || 30;

    this.init();
  }

  /**
   * Initialize event listeners and monitoring systems.
   *
   * Sets up page visibility change detection, user activity monitoring,
   * and initializes the smart refresh system based on current page state.
   */
  init() {
    document.addEventListener('visibilitychange', () => {
      this.isVisible = !document.hidden;
      if (this.isVisible) {
        this.updateLastActivity();
        this.checkIfShouldRefresh();
      } else {
        this.stopRefresh();
      }
    });

    ['click', 'keypress', 'scroll', 'mousemove'].forEach((event) => {
      document.addEventListener(event, () => this.updateLastActivity(), {
        passive: true,
      });
    });

    this.setupSmartRefresh();
  }

  /**
   * Update the timestamp of last user activity.
   *
   * Called whenever user interaction is detected to reset the inactivity timer.
   * This helps determine when to stop automatic refresh to save resources.
   */
  updateLastActivity() {
    this.lastActivity = Date.now();
  }

  /**
   * Check if the user is currently active based on recent interactions.
   *
   * @returns {boolean} True if user has been active within the inactivity threshold
   */
  isUserActive() {
    const inactiveMinutes = (Date.now() - this.lastActivity) / (1000 * 60);
    return inactiveMinutes < this.maxInactiveMinutes;
  }

  /**
   * Set up smart refresh based on current page parameters.
   *
   * Analyzes URL parameters to determine if auto-refresh should be enabled.
   * Only enables refresh for 'latest' data views to avoid disrupting specific date views.
   */
  setupSmartRefresh() {
    const urlParams = new URLSearchParams(window.location.search);
    const searchDate = urlParams.get('date');

    if (!searchDate || searchDate === 'latest') {
      this.startSmartRefresh();
    }
  }

  /**
   * Start the intelligent refresh system with activity and visibility checks.
   *
   * Establishes a periodic check that evaluates whether refresh should occur
   * based on user activity, page visibility, and data freshness needs.
   */
  startSmartRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    this.refreshInterval = setInterval(() => {
      if (!this.isVisible) {
        return;
      }

      if (!this.isUserActive()) {
        this.stopRefresh();
        return;
      }

      this.performSoftRefresh();
    }, this.refreshIntervalMinutes * 60 * 1000);
  }

  /**
   * Stop the automatic refresh system.
   *
   * Clears the refresh interval and logs the action for debugging.
   * Called when user becomes inactive or page becomes hidden.
   */
  stopRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  /**
   * Perform a soft refresh using API calls instead of page reload.
   *
   * Checks for data updates via API and notifies user if new data is available,
   * rather than forcefully reloading the page. This provides better UX and
   * allows users to choose when to update.
   *
   * @async
   */
  async performSoftRefresh() {
    try {
      const response = await fetch('/api/regions');

      if (!response.ok) {
        throw new Error('API check failed');
      }

      const data = await response.json();

      const lastUpdateElement = document.querySelector('[data-last-update]');
    } catch (error) {
      console.warn('⚠️ Soft refresh failed:', error.message);
    }
  }

  /**
   * Check connectivity to the server using a lightweight HEAD request.
   *
   * @async
   * @returns {Promise<boolean>} True if server is reachable, false otherwise
   */
  async checkConnectivity() {
    try {
      const response = await fetch('/api/cache', {
        method: 'HEAD',
        cache: 'no-cache',
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Check if a refresh should be performed based on elapsed time since last check.
   *
   * This method can be called when the page becomes visible again to determine
   * if enough time has passed to warrant a data freshness check.
   */
  checkIfShouldRefresh() {
    const timeSinceLastActivity = Date.now() - this.lastActivity;
    const shouldCheck =
      timeSinceLastActivity > this.refreshIntervalMinutes * 60 * 1000;

    if (shouldCheck) {
      this.performSoftRefresh();
    }
  }
}

/**
 * Enhanced form validation for search date inputs.
 *
 * Validates date inputs against business rules including future date prevention
 * and minimum date enforcement. Provides user feedback via toast notifications.
 *
 * @returns {boolean} True if form is valid and can be submitted
 */
function validateSearchForm() {
  const dateInput = document.getElementById('search-date');
  if (dateInput && dateInput.value) {
    const selectedDate = new Date(dateInput.value);
    const today = new Date();

    const historicalStartDate =
      window.appConfig?.historicalStartDate || '2020-02-24';
    const minDate = new Date(historicalStartDate);

    if (selectedDate > today) {
      showToast('Cannot select future dates', 'warning');
      return false;
    }

    if (selectedDate < minDate) {
      showToast(
        `Data only available from ${historicalStartDate} onwards`,
        'warning'
      );
      return false;
    }
  }
  return true;
}

/**
 * Display toast notification with consistent styling and behavior.
 *
 * Creates and displays a temporary notification message with appropriate
 * styling based on message type. Includes automatic dismissal and animation.
 *
 * @param {string} message - The message text to display
 * @param {string} type - The notification type (info, warning, error, success)
 */
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  const bgColors = {
    info: 'bg-blue-600',
    warning: 'bg-yellow-600',
    error: 'bg-red-600',
    success: 'bg-green-600',
  };

  toast.className = `
    fixed bottom-4 right-4 ${bgColors[type]} text-white px-6 py-3 rounded-lg shadow-lg 
    transform translate-y-full transition-transform duration-300 z-50 max-w-sm
  `;
  toast.textContent = message;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.transform = 'translateY(0)';
  }, 100);

  setTimeout(() => {
    toast.style.transform = 'translateY(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/**
 * Show loading state for a specific element.
 *
 * Applies visual loading indicators including opacity reduction,
 * pointer event blocking, and spinner visibility.
 *
 * @param {HTMLElement} element - The element to show loading state for
 */
function showLoading(element) {
  if (element) {
    element.classList.add('opacity-50', 'pointer-events-none');
    const spinner = element.querySelector('.loading-spinner');
    if (spinner) spinner.classList.remove('hidden');

    element.style.cursor = 'wait';
  }
}

/**
 * Hide loading state for a specific element.
 *
 * Removes visual loading indicators and restores normal element functionality.
 *
 * @param {HTMLElement} element - The element to hide loading state for
 */
function hideLoading(element) {
  if (element) {
    element.classList.remove('opacity-50', 'pointer-events-none');
    const spinner = element.querySelector('.loading-spinner');
    if (spinner) spinner.classList.add('hidden');

    element.style.cursor = '';
  }
}

/**
 * Initialize the smart refresh system and enhanced form validation.
 *
 * Sets up all client-side functionality including the refresh manager,
 * date input validation, and user interaction enhancements.
 */
document.addEventListener('DOMContentLoaded', function () {
  window.smartRefresh = new RefreshManager();

  const dateInput = document.getElementById('search-date');
  if (dateInput) {
    dateInput.addEventListener('change', function () {
      if (this.value) {
        const selectedDate = new Date(this.value);
        const today = new Date();

        const historicalStartDate =
          window.appConfig?.historicalStartDate || '2020-02-24';
        const minDate = new Date(historicalStartDate);

        if (selectedDate > today) {
          showToast('Cannot select future dates', 'warning');
          this.value = '';
        } else if (selectedDate < minDate) {
          showToast(
            `Data only available from ${historicalStartDate} onwards`,
            'warning'
          );
          this.value = '';
        }
      }
    });
  }
});

window.validateSearchForm = validateSearchForm;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showToast = showToast;
