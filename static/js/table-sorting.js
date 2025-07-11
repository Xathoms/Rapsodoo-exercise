/**
 * TableSorter - table sorting functionality
 *
 */
class TableSorter {
  static CONSTANTS = {
    ANIMATION_DELAY_MS: 30,
    SORT_TRANSITION_MS: 200,
    CLEANUP_DELAY_MS: 300,
    DEFAULT_SORT: { column: 'cases', direction: 'desc' },
    SELECTORS: {
      TABLE_BODY: '#data-table-body',
      DATA_ROWS: '#data-table-body tr[data-region]',
      SORT_HEADERS: '[data-sort]',
      SORT_INDICATORS: '[data-sort] svg',
      SORT_STATUS: '#sort-status',
      SORT_LABEL: '#sort-label',
    },
    CLASSES: {
      SORTING: 'sorting',
      SLIDE_IN: 'slide-in',
      OPACITY_FULL: 'opacity-100',
      OPACITY_DIM: 'opacity-30',
      ROTATE_180: 'rotate-180',
    },
  };

  constructor() {
    this.currentSort = { ...TableSorter.CONSTANTS.DEFAULT_SORT };
    this.originalData = [];
    this.currentData = [];
    this.totalCases = 0;
    this.domCache = new Map();

    this.init();
  }

  /**
   * Initialize the table sorter
   */
  init() {
    try {
      this.cacheDOM();
      this.extractAndCacheData();
      this.attachEventListeners();
      this.updateUI();
    } catch (error) {
      console.error('❌ TableSorter initialization failed:', error);
    }
  }

  /**
   * Cache frequently used DOM elements for performance
   */
  cacheDOM() {
    const selectors = TableSorter.CONSTANTS.SELECTORS;

    this.domCache.set(
      'tableBody',
      document.querySelector(selectors.TABLE_BODY)
    );
    this.domCache.set(
      'sortStatus',
      document.querySelector(selectors.SORT_STATUS)
    );
    this.domCache.set(
      'sortLabel',
      document.querySelector(selectors.SORT_LABEL)
    );
    this.domCache.set(
      'sortHeaders',
      document.querySelectorAll(selectors.SORT_HEADERS)
    );
    this.domCache.set(
      'sortIndicators',
      document.querySelectorAll(selectors.SORT_INDICATORS)
    );

    if (!this.domCache.get('tableBody')) {
      throw new Error('Required table body element not found');
    }
  }

  /**
   * Extract and cache table data from DOM
   */
  extractAndCacheData() {
    const dataRows = document.querySelectorAll(
      TableSorter.CONSTANTS.SELECTORS.DATA_ROWS
    );

    if (!dataRows.length) {
      console.warn('⚠️ No data rows found in table');
      return;
    }

    this.originalData = Array.from(dataRows)
      .map((row, index) => {
        return this.extractRowData(row, index + 1);
      })
      .filter((data) => data !== null);

    this.currentData = [...this.originalData];
    this.totalCases = this.calculateTotalCases();
  }

  /**
   * Extract data from a single table row
   * @param {HTMLElement} row - Table row element
   * @param {number} originalRank - Original ranking
   * @returns {Object|null} Extracted row data or null if invalid
   */
  extractRowData(row, originalRank) {
    try {
      const dataset = row.dataset;

      return {
        regionName: dataset.region?.trim() || '',
        totalCases: this.parseIntSafe(dataset.cases, 0),
        provincesCount: this.parseIntSafe(dataset.provinces, 0),
        lastUpdated: dataset.updated || '',
        originalRank,
      };
    } catch (error) {
      console.warn('⚠️ Failed to extract data from row:', error);
      return null;
    }
  }

  /**
   * Safely parse integer with fallback
   * @param {string} value - Value to parse
   * @param {number} fallback - Fallback value
   * @returns {number} Parsed integer or fallback
   */
  parseIntSafe(value, fallback = 0) {
    const parsed = parseInt(value, 10);
    return isNaN(parsed) ? fallback : parsed;
  }

  /**
   * Calculate total cases from original data
   * @returns {number} Total cases
   */
  calculateTotalCases() {
    return this.originalData.reduce((sum, item) => sum + item.totalCases, 0);
  }

  /**
   * Attach event listeners to sort headers
   */
  attachEventListeners() {
    const sortHeaders = this.domCache.get('sortHeaders');

    sortHeaders.forEach((header) => {
      const column = header.dataset.sort;

      header.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleSort(column);
      });

      header.setAttribute('role', 'button');
      header.setAttribute('tabindex', '0');
      header.title = `Sort by ${this.getColumnDisplayName(column)}`;

      header.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.handleSort(column);
        }
      });
    });
  }

  /**
   * Handle sorting when header is clicked
   * @param {string} column - Column to sort by
   */
  handleSort(column) {
    if (!this.isValidColumn(column)) {
      console.warn(`⚠️ Invalid sort column: ${column}`);
      return;
    }

    try {
      this.addSortingAnimation();

      const newDirection = this.calculateNewDirection(column);
      this.currentSort = { column, direction: newDirection };

      this.performSort();

      setTimeout(() => {
        this.renderSortedTable();
        this.updateUI();
        this.removeSortingAnimation();
      }, TableSorter.CONSTANTS.SORT_TRANSITION_MS);
    } catch (error) {
      console.error('❌ Sort operation failed:', error);
      this.removeSortingAnimation();
    }
  }

  /**
   * Validate if column is sortable
   * @param {string} column - Column name
   * @returns {boolean} Is valid column
   */
  isValidColumn(column) {
    return ['cases', 'name', 'provinces'].includes(column);
  }

  /**
   * Calculate new sort direction based on current state
   * @param {string} column - Column being sorted
   * @returns {string} New direction ('asc' or 'desc')
   */
  calculateNewDirection(column) {
    if (this.currentSort.column === column) {
      return this.currentSort.direction === 'asc' ? 'desc' : 'asc';
    }

    const defaultDirections = {
      cases: 'desc',
      provinces: 'desc',
      name: 'asc',
    };

    return defaultDirections[column] || 'asc';
  }

  /**
   * Perform the actual sorting operation
   */
  performSort() {
    this.currentData = [...this.originalData].sort((a, b) => {
      return this.compareItems(
        a,
        b,
        this.currentSort.column,
        this.currentSort.direction
      );
    });
  }

  /**
   * Compare two items for sorting
   * @param {Object} a - First item
   * @param {Object} b - Second item
   * @param {string} column - Column to compare
   * @param {string} direction - Sort direction
   * @returns {number} Comparison result
   */
  compareItems(a, b, column, direction) {
    let valueA, valueB;

    switch (column) {
      case 'cases':
        valueA = a.totalCases;
        valueB = b.totalCases;
        break;
      case 'name':
        valueA = a.regionName.toLowerCase();
        valueB = b.regionName.toLowerCase();
        break;
      case 'provinces':
        valueA = a.provincesCount;
        valueB = b.provincesCount;
        break;
      default:
        return 0;
    }

    const comparison = valueA > valueB ? 1 : valueA < valueB ? -1 : 0;
    return direction === 'asc' ? comparison : -comparison;
  }

  /**
   * Add sorting animation classes
   */
  addSortingAnimation() {
    const tableBody = this.domCache.get('tableBody');
    const rows = tableBody.querySelectorAll('tr');

    rows.forEach((row) => {
      row.classList.add(TableSorter.CONSTANTS.CLASSES.SORTING);
    });
  }

  /**
   * Remove sorting animation classes
   */
  removeSortingAnimation() {
    setTimeout(() => {
      const tableBody = this.domCache.get('tableBody');
      const rows = tableBody.querySelectorAll('tr');

      rows.forEach((row) => {
        row.classList.remove(TableSorter.CONSTANTS.CLASSES.SORTING);
      });
    }, TableSorter.CONSTANTS.CLEANUP_DELAY_MS);
  }

  /**
   * Render the sorted table
   */
  renderSortedTable() {
    const tableBody = this.domCache.get('tableBody');

    if (!tableBody) {
      console.error('❌ Table body element not found');
      return;
    }

    const html = this.currentData
      .map((item, index) => {
        return this.generateRowHTML(item, index);
      })
      .join('');

    tableBody.innerHTML = html;
  }

  /**
   * Generate HTML for a single table row
   * @param {Object} item - Data item
   * @param {number} index - Row index
   * @returns {string} HTML string
   */
  generateRowHTML(item, index) {
    const percentage =
      this.totalCases > 0 ? (item.totalCases / this.totalCases) * 100 : 0;
    const isEven = index % 2 === 0;
    const animationDelay = index * TableSorter.CONSTANTS.ANIMATION_DELAY_MS;

    return `
      <tr class="${
        TableSorter.CONSTANTS.CLASSES.SLIDE_IN
      } transition-all duration-300 hover:bg-gray-50 ${
      isEven ? 'bg-white' : 'bg-gray-50'
    }" 
          style="animation-delay: ${animationDelay}ms"
          data-region="${this.escapeHtml(item.regionName)}" 
          data-cases="${item.totalCases}" 
          data-provinces="${item.provincesCount}"
          data-updated="${this.escapeHtml(item.lastUpdated)}"
          data-rank="${index + 1}">
        ${this.generateCellHTML('region', item.regionName)}
        ${this.generateCellHTML('cases', item.totalCases)}
        ${this.generateCellHTML('provinces', item.provincesCount)}
        ${this.generateCellHTML('percentage', percentage)}
      </tr>
    `;
  }

  /**
   * Generate HTML for individual cells
   * @param {string} type - Cell type
   * @param {*} value - Cell value
   * @returns {string} HTML string
   */
  generateCellHTML(type, value) {
    switch (type) {
      case 'region':
        return `
          <td class="region-cell px-6 py-4 whitespace-nowrap">
            <div class="text-sm font-semibold text-gray-900">${this.escapeHtml(
              value
            )}</div>
          </td>
        `;

      case 'cases':
        return `
          <td class="cases-cell px-6 py-4 whitespace-nowrap">
            <div class="text-sm font-bold text-gray-900">${value.toLocaleString()}</div>
          </td>
        `;

      case 'provinces':
        return `
          <td class="provinces-cell px-6 py-4 whitespace-nowrap">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              ${value}
            </span>
          </td>
        `;

      case 'percentage':
        return `
          <td class="percentage-cell px-6 py-4 whitespace-nowrap">
            <div class="flex items-center">
              <div class="percentage-text text-sm font-medium text-gray-900">
                ${value.toFixed(2)}%
              </div>
              <div class="ml-2 w-16 bg-gray-200 rounded-full h-2">
                <div class="percentage-bar bg-blue-500 h-2 rounded-full transition-all duration-300" 
                    style="width: ${Math.min(value, 100).toFixed(1)}%"></div>
              </div>
            </div>
          </td>
        `;

      default:
        return '<td></td>';
    }
  }

  /**
   * Escape HTML to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Update all UI elements
   */
  updateUI() {
    this.updateSortIndicators();
    this.updateSortStatus();
  }

  /**
   * Update visual sort indicators on column headers
   */
  updateSortIndicators() {
    const sortIndicators = this.domCache.get('sortIndicators');
    const { OPACITY_FULL, OPACITY_DIM, ROTATE_180 } =
      TableSorter.CONSTANTS.CLASSES;

    sortIndicators.forEach((indicator) => {
      indicator.classList.remove(OPACITY_FULL, ROTATE_180);
      indicator.classList.add(OPACITY_DIM);
    });

    const activeHeader = document.querySelector(
      `[data-sort="${this.currentSort.column}"]`
    );
    if (activeHeader) {
      const indicator = activeHeader.querySelector('svg');
      if (indicator) {
        indicator.classList.remove(OPACITY_DIM);
        indicator.classList.add(OPACITY_FULL);

        if (this.currentSort.direction === 'asc') {
          indicator.classList.add(ROTATE_180);
        }
      }
    }
  }

  /**
   * Update sort status display
   */
  updateSortStatus() {
    const sortStatus = this.domCache.get('sortStatus');
    const sortLabel = this.domCache.get('sortLabel');

    if (!sortStatus || !sortLabel) {
      return;
    }

    const columnName = this.getColumnDisplayName(this.currentSort.column);
    const directionSymbol = this.currentSort.direction === 'desc' ? '↓' : '↑';

    sortStatus.textContent = `${columnName} ${directionSymbol}`;
    sortLabel.textContent = 'Sort Order';
  }

  /**
   * Get display name for column
   * @param {string} column - Column key
   * @returns {string} Display name
   */
  getColumnDisplayName(column) {
    const displayNames = {
      cases: 'Cases',
      name: 'Region',
      provinces: 'Provinces',
    };

    return displayNames[column] || 'Data';
  }

  /**
   * Public method to refresh data
   */
  refresh() {
    this.extractAndCacheData();
    this.renderSortedTable();
    this.updateUI();
  }

  /**
   * Public method to get current sort state
   * @returns {Object} Current sort state
   */
  getCurrentSort() {
    return { ...this.currentSort };
  }

  /**
   * Public method to set sort programmatically
   * @param {string} column - Column to sort
   * @param {string} direction - Sort direction
   */
  setSortState(column, direction) {
    if (this.isValidColumn(column) && ['asc', 'desc'].includes(direction)) {
      this.currentSort = { column, direction };
      this.performSort();
      this.renderSortedTable();
      this.updateUI();
    }
  }
}

document.addEventListener('DOMContentLoaded', function () {
  setTimeout(() => {
    const tableBody = document.querySelector('#data-table-body');

    if (tableBody && tableBody.children.length > 0) {
      try {
        window.tableSorter = new TableSorter();
      } catch (error) {
        console.error('❌ TableSorter initialization failed:', error);
      }
    } else {
      console.warn('⚠️ Table not found or empty, sorting not initialized');
    }
  }, 100);
});
