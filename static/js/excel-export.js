function exportToExcel() {
  const searchDate = document.getElementById('search-date')?.value || 'latest';

  const exportUrl = `/api/export/excel?date=${encodeURIComponent(searchDate)}`;

  const exportButton = event.target.closest('button');
  const originalText = exportButton.innerHTML;

  exportButton.innerHTML = `
      <svg class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
        </path>
      </svg>
      Exporting...
    `;
  exportButton.disabled = true;

  fetch(exportUrl)
    .then((response) => {
      if (!response.ok) {
        if (
          response.headers.get('content-type')?.includes('application/json')
        ) {
          return response.json().then((data) => {
            throw new Error(data.error || 'Export failed');
          });
        }
        throw new Error(`Export failed: HTTP ${response.status}`);
      }

      const contentDisposition = response.headers.get('content-disposition');
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/['"]/g, '')
        : `covid19_export_${searchDate}.xlsx`;

      return response.blob().then((blob) => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';

      document.body.appendChild(link);
      link.click();

      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);

      console.log('✅ Excel file downloaded successfully!');
    })
    .catch((error) => {
      console.error('Export error:', error);
      console.log('❌ Export failed:', error.message);
    })
    .finally(() => {
      setTimeout(() => {
        exportButton.innerHTML = originalText;
        exportButton.disabled = false;
      }, 1000);
    });
}
