let currentSort = {
  column: 'cases',
  direction: 'desc',
};

let originalData = [];
let currentData = [];
let totalCases = 0;

function extractTableData() {
  const rows = document.querySelectorAll('#data-table-body tr[data-region]');
  const data = [];

  rows.forEach((row) => {
    const regionData = {
      region_name: row.dataset.region,
      total_cases: parseInt(row.dataset.cases),
      provinces_count: parseInt(row.dataset.provinces),
      last_updated: row.dataset.updated,
      rank: parseInt(row.dataset.rank),
    };
    data.push(regionData);
  });

  return data;
}

function initializeFrontendSorting() {
  originalData = extractTableData();
  currentData = [...originalData];

  totalCases = originalData.reduce((sum, item) => sum + item.total_cases, 0);

  document.querySelectorAll('[data-sort]').forEach((header) => {
    header.addEventListener('click', function (e) {
      e.preventDefault();
      const column = this.dataset.sort;
      handleFrontendSort(column);
    });

    header.title = `Click to sort by ${header.dataset.sort}`;
  });

  updateSortIndicators();
  updateSortStatus();
}

function handleFrontendSort(column) {
  const rows = document.querySelectorAll('tbody tr');
  rows.forEach((row) => row.classList.add('sorting'));

  let newDirection;
  if (currentSort.column === column) {
    newDirection = currentSort.direction === 'asc' ? 'desc' : 'asc';
  } else {
    if (column === 'cases') {
      newDirection = 'desc';
    } else if (column === 'provinces') {
      newDirection = 'desc';
    } else {
      newDirection = 'asc';
    }
  }

  currentSort = { column, direction: newDirection };

  currentData = sortDataArray([...originalData], column, newDirection);

  setTimeout(() => {
    renderSortedTable(currentData);
    updateSortIndicators();
    updateSortStatus();

    setTimeout(() => {
      document.querySelectorAll('tbody tr').forEach((row) => {
        row.classList.remove('sorting');
      });
    }, 300);
  }, 200);
}

function sortDataArray(data, column, direction) {
  return data.sort((a, b) => {
    let valueA, valueB;

    if (column === 'cases') {
      valueA = a.total_cases;
      valueB = b.total_cases;
    } else if (column === 'name') {
      valueA = a.region_name.toLowerCase();
      valueB = b.region_name.toLowerCase();
    } else if (column === 'provinces') {
      valueA = a.provinces_count;
      valueB = b.provinces_count;
    } else {
      return 0;
    }

    if (direction === 'asc') {
      return valueA > valueB ? 1 : valueA < valueB ? -1 : 0;
    } else {
      return valueA < valueB ? 1 : valueA > valueB ? -1 : 0;
    }
  });
}

function renderSortedTable(data) {
  const tbody = document.getElementById('data-table-body');

  tbody.innerHTML = data
    .map((item, index) => {
      const percentage =
        totalCases > 0 ? (item.total_cases / totalCases) * 100 : 0;
      const isEven = index % 2 === 0;

      return `
        <tr class="slide-in transition-all duration-300 hover:bg-gray-50 ${
          isEven ? 'bg-white' : 'bg-gray-50'
        }" 
            style="animation-delay: ${index * 30}ms"
            data-region="${item.region_name}" 
            data-cases="${item.total_cases}" 
            data-provinces="${item.provinces_count}"
            data-updated="${item.last_updated}"
            data-rank="${index + 1}">
          <td class="region-cell px-6 py-4 whitespace-nowrap">
            <div class="text-sm font-semibold text-gray-900">${
              item.region_name
            }</div>
          </td>
          <td class="cases-cell px-6 py-4 whitespace-nowrap">
            <div class="text-sm font-bold text-gray-900">${item.total_cases.toLocaleString()}</div>
          </td>
          <td class="provinces-cell px-6 py-4 whitespace-nowrap">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              ${item.provinces_count}
            </span>
          </td>
          <td class="percentage-cell px-6 py-4 whitespace-nowrap">
            <div class="flex items-center">
              <div class="percentage-text text-sm font-medium text-gray-900">
                ${percentage.toFixed(2)}%
              </div>
              <div class="ml-2 w-16 bg-gray-200 rounded-full h-2">
                <div class="percentage-bar bg-blue-500 h-2 rounded-full transition-all duration-300" 
                    style="width: ${percentage.toFixed(1)}%"></div>
              </div>
            </div>
          </td>
        </tr>
      `;
    })
    .join('');
}

function updateSortIndicators() {
  document.querySelectorAll('[data-sort] svg').forEach((indicator) => {
    indicator.classList.remove('opacity-100', 'rotate-180');
    indicator.classList.add('opacity-60');
  });

  const activeHeader = document.querySelector(
    `[data-sort="${currentSort.column}"]`
  );
  if (activeHeader) {
    const indicator = activeHeader.querySelector('svg');
    indicator.classList.remove('opacity-60');
    indicator.classList.add('opacity-100');
    if (currentSort.direction === 'desc') {
      indicator.classList.add('rotate-180');
    }
  }
}

function updateSortStatus() {
  const sortStatus = document.getElementById('sort-status');
  const sortLabel = document.getElementById('sort-label');

  if (sortStatus && sortLabel) {
    let columnName;
    if (currentSort.column === 'cases') {
      columnName = 'Cases';
    } else if (currentSort.column === 'name') {
      columnName = 'Region';
    } else if (currentSort.column === 'provinces') {
      columnName = 'Provinces';
    } else {
      columnName = 'Data';
    }

    const directionSymbol = currentSort.direction === 'desc' ? '↓' : '↑';

    sortStatus.textContent = `${columnName} ${directionSymbol}`;
    sortLabel.textContent = 'Sort Order';
  }
}

document.addEventListener('DOMContentLoaded', function () {
  setTimeout(() => {
    const table = document.getElementById('data-table-body');
    if (table && table.children.length > 0) {
      initializeFrontendSorting();
    } else {
      console.warn('⚠️ Table not found or empty, sorting not initialized');
    }
  }, 100);
});
