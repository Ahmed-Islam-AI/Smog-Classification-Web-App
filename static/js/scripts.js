document.addEventListener('DOMContentLoaded', () => {
    console.log('Scripts loaded and DOM is ready');

    // Example: Form submission handling
   document.getElementById('weather-form').onsubmit = function (e) {
    e.preventDefault();  // Prevent the form from reloading the page

    const city = document.getElementById('city').value;

    // Fetch weather for the entered city
    fetch('/weather', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `city=${encodeURIComponent(city)}`  // Send the city as form data
    })
    .then(response => response.json())
    .then(data => {
        if (data.weather && data.weather.current) {
            document.getElementById('weather-result').textContent = `Weather: ${data.weather.current.condition.text}, Temperature: ${data.weather.current.temperature}°C`;
        } else {
            document.getElementById('weather-result').textContent = "Weather data not available.";
        }
    })
    .catch(error => console.error('Error:', error));
};
