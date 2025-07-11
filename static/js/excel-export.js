/**
 * Excel Export functionality for COVID-19 regional data
 *
 * This module handles the client-side Excel export functionality,
 * providing user feedback and error handling during the export process.
 */

/**
 * Export regional COVID-19 data to Excel format
 *
 * @param {Event} event - The click event from the export button
 */
function exportToExcel(event) {
  const searchDate = getSearchDate();
  const exportUrl = buildExportUrl(searchDate);

  const exportButton = getExportButton(event);
  if (!exportButton) {
    console.error('Export button not found');
    return;
  }

  setButtonLoadingState(exportButton);
  performExport(exportUrl, exportButton, searchDate);
}

/**
 * Get the search date value from the form input
 *
 * @returns {string} The search date value or 'latest' as default
 */
function getSearchDate() {
  const searchDateInput = document.getElementById('search-date');
  return searchDateInput?.value || 'latest';
}

/**
 * Build the export API URL with proper encoding
 *
 * @param {string} searchDate - The date to export data for
 * @returns {string} The complete API URL
 */
function buildExportUrl(searchDate) {
  return `/api/export/excel?date=${encodeURIComponent(searchDate)}`;
}

/**
 * Get the export button element from the event
 *
 * @param {Event} event - The click event
 * @returns {HTMLElement|null} The export button element
 */
function getExportButton(event) {
  return event?.target?.closest('button') || null;
}

/**
 * Set the button to loading state with spinner and disabled status
 *
 * @param {HTMLElement} exportButton - The export button element
 */
function setButtonLoadingState(exportButton) {
  exportButton.dataset.originalText = exportButton.innerHTML;

  exportButton.innerHTML = `
    <svg class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
      </path>
    </svg>
    Exporting...
  `;
  exportButton.disabled = true;
}

/**
 * Restore the button to its original state
 *
 * @param {HTMLElement} exportButton - The export button element
 */
function restoreButtonState(exportButton) {
  if (exportButton && exportButton.dataset.originalText) {
    exportButton.innerHTML = exportButton.dataset.originalText;
    exportButton.disabled = false;
    delete exportButton.dataset.originalText;
  }
}

/**
 * Perform the actual export operation
 *
 * @param {string} exportUrl - The API endpoint URL
 * @param {HTMLElement} exportButton - The export button element
 * @param {string} searchDate - The search date for filename generation
 */
function performExport(exportUrl, exportButton, searchDate) {
  fetch(exportUrl)
    .then((response) => handleExportResponse(response))
    .then(({ blob, filename }) => downloadFile(blob, filename))
    .catch((error) => {
      console.error('Export error:', error);
      console.log('❌ Export failed:', error.message);
    })
    .finally(() => {
      setTimeout(() => {
        restoreButtonState(exportButton);
      }, 1000);
    });
}

/**
 * Handle the export API response
 *
 * @param {Response} response - The fetch response object
 * @returns {Promise<{blob: Blob, filename: string}>} Promise resolving to blob and filename
 * @throws {Error} If response is not ok or processing fails
 */
async function handleExportResponse(response) {
  if (!response.ok) {
    if (response.headers.get('content-type')?.includes('application/json')) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Export failed');
    }
    throw new Error(`Export failed: HTTP ${response.status}`);
  }

  const filename = extractFilenameFromResponse(response);
  const blob = await response.blob();

  return { blob, filename };
}

/**
 * Extract filename from response headers
 *
 * @param {Response} response - The fetch response object
 * @returns {string} The extracted filename or a default name
 */
function extractFilenameFromResponse(response) {
  const contentDisposition = response.headers.get('content-disposition');

  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename=([^;]+)/);
    if (filenameMatch) {
      return filenameMatch[1].replace(/['"]/g, '');
    }
  }

  const timestamp = new Date().toISOString().split('T')[0];
  return `covid19_export_${timestamp}.xlsx`;
}

/**
 * Download the file blob to the user's device
 *
 * @param {Blob} blob - The file blob data
 * @param {string} filename - The filename for the download
 */
function downloadFile(blob, filename) {
  const url = window.URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';

  document.body.appendChild(link);
  link.click();

  cleanupDownload(url, link);
}

/**
 * Clean up temporary download resources
 *
 * @param {string} url - The object URL to revoke
 * @param {HTMLElement} link - The temporary link element to remove
 */
function cleanupDownload(url, link) {
  window.URL.revokeObjectURL(url);
  document.body.removeChild(link);
}
