// analytics.js
document.addEventListener('DOMContentLoaded', function() {
    fetch('/analytics/data')
      .then(response => response.json())
      .then(data => {
        const ctx = document.getElementById('apartmentChart').getContext('2d');
        new Chart(ctx, {
          type: 'bar',
          data: {
            labels: data.apartments,
            datasets: [{
              label: 'Number of Visitors',
              data: data.counts,
              backgroundColor: 'rgba(75, 192, 192, 0.6)',
              borderColor: 'rgba(75, 192, 192, 1)',
              borderWidth: 1
            }]
          },
          options: {
            scales: {
              y: {
                beginAtZero: true,
                stepSize: 1
              }
            }
          }
        });
      })
      .catch(error => console.error('Error loading analytics data:', error));
  });
  