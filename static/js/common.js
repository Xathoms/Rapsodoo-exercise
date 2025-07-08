function validateSearchForm() {
  const dateInput = document.getElementById('search-date');
  if (dateInput && dateInput.value) {
    const selectedDate = new Date(dateInput.value);
    const today = new Date();
    const minDate = new Date('2020-02-24');

    if (selectedDate > today || selectedDate < minDate) {
      return false;
    }
  }
  return true;
}

function showLoading(element) {
  if (element) {
    element.classList.add('opacity-50', 'pointer-events-none');
    const spinner = element.querySelector('.loading-spinner');
    if (spinner) spinner.classList.remove('hidden');
  }
}

function hideLoading(element) {
  if (element) {
    element.classList.remove('opacity-50', 'pointer-events-none');
    const spinner = element.querySelector('.loading-spinner');
    if (spinner) spinner.classList.add('hidden');
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const urlParams = new URLSearchParams(window.location.search);
  const searchDate = urlParams.get('date');

  if (!searchDate || searchDate === 'latest') {
    setTimeout(function () {
      location.reload();
    }, 30 * 60 * 1000);
  }

  const dateInput = document.getElementById('search-date');
  if (dateInput) {
    dateInput.addEventListener('change', function () {
      if (this.value) {
        const selectedDate = new Date(this.value);
        const today = new Date();
        const minDate = new Date('2020-02-24');

        if (selectedDate > today) {
          alert('Cannot select future dates');
          this.value = '';
        } else if (selectedDate < minDate) {
          alert('Data only available from February 24, 2020 onwards');
          this.value = '';
        }
      }
    });
  }
});

window.validateSearchForm = validateSearchForm;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
