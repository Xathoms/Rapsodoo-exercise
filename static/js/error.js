/**
 * ErrorPageManager - Minimal error page functionality
 *
 * Provides basic retry functionality for error pages
 *
 * @class ErrorPageManager
 */
class ErrorPageManager {
  static CONSTANTS = {
    SELECTORS: {
      BTN_RETRY: '.btn-retry',
      BTN_RETRY_TEXT: '.btn-retry-text',
    },

    CLASSES: {
      LOADING: ['opacity-50', 'pointer-events-none'],
    },
  };

  constructor() {
    this.init();
  }

  /**
   * Initialize the error page manager
   */
  init() {
    try {
      this.setupEventListeners();
    } catch (error) {
      console.error('❌ ErrorPageManager initialization failed:', error);
    }
  }

  /**
   * Setup event listeners for interactive elements
   */
  setupEventListeners() {
    const retryBtn = document.querySelector(
      ErrorPageManager.CONSTANTS.SELECTORS.BTN_RETRY
    );
    if (retryBtn) {
      retryBtn.addEventListener('click', () => this.handleRetry());
    }
  }

  /**
   * Handle manual retry button click
   */
  handleRetry() {
    this.executeRetry();
  }

  /**
   * Execute retry operation
   */
  async executeRetry() {
    const retryBtn = document.querySelector(
      ErrorPageManager.CONSTANTS.SELECTORS.BTN_RETRY
    );
    const retryText = document.querySelector(
      ErrorPageManager.CONSTANTS.SELECTORS.BTN_RETRY_TEXT
    );

    if (retryBtn) {
      retryBtn.classList.add(...ErrorPageManager.CONSTANTS.CLASSES.LOADING);
      retryBtn.disabled = true;
    }

    if (retryText) {
      retryText.textContent = 'Retrying...';
    }

    try {
      const isAccessible = await this.checkPageAccessibility();

      if (isAccessible) {
        window.location.reload();
      } else {
        setTimeout(() => {
          this.resetRetryButton();
        }, 1500);
      }
    } catch (error) {
      console.warn('Retry attempt failed:', error);
      setTimeout(() => {
        this.resetRetryButton();
      }, 1500);
    }
  }

  /**
   * Reset retry button to original state
   */
  resetRetryButton() {
    const retryBtn = document.querySelector(
      ErrorPageManager.CONSTANTS.SELECTORS.BTN_RETRY
    );
    const retryText = document.querySelector(
      ErrorPageManager.CONSTANTS.SELECTORS.BTN_RETRY_TEXT
    );

    if (retryBtn) {
      retryBtn.classList.remove(...ErrorPageManager.CONSTANTS.CLASSES.LOADING);
      retryBtn.disabled = false;
    }

    if (retryText) {
      retryText.textContent = 'Try Again';
    }
  }

  /**
   * Check if the original page is now accessible
   * @returns {Promise<boolean>} Whether page is accessible
   */
  async checkPageAccessibility() {
    try {
      const response = await fetch(window.location.pathname, {
        method: 'HEAD',
        cache: 'no-cache',
      });

      return response.ok;
    } catch (error) {
      return false;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  try {
    window.errorPageManager = new ErrorPageManager();
    console.log('✅ Error page minimal functionality loaded');
  } catch (error) {
    console.error('❌ Failed to initialize error page manager:', error);
  }
});
