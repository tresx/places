let geocoder;
let map;

// AJAX request to GET /locations
// returns locations as JSON near a given latlng
function getLocations(latlng) {
    return fetch(`/locations?lat=${latlng.lat}&lng=${latlng.lng}`)
    .then(response => response.json())
    .catch(error => console.error(error));
}

function initMap(latlng) {
    geocoder = new google.maps.Geocoder();
    map = new google.maps.Map(
        document.getElementById('map'), {center: latlng, zoom: 11});
}

function addElement(element) {
    geocoder.geocode(
        {'address': element.postcode},
        function(results, status) {
            if (status == 'OK') {
                let marker = new google.maps.Marker({
                    map: map,
                    position: results[0].geometry.location
                });
                // Add clickable infoWindow for each element
                let href = `/place/${element.id}`
                let infoWindow = new google.maps.InfoWindow({
                    content: `
                        <a href=${href}><h3>${element.name}</h3></a>
                        <span>Average rating: ${element.average_rating}</span>
                        <ul>
                            <li>${element.description}
                            <li>${element.postcode}
                        </ul>`
                });
                marker.addListener('click', function() {
                    infoWindow.open(map, marker);
                });
            } else {
                alert('Geocode was not successful: ' + status);
            }
        }
    );
}

navigator.geolocation.getCurrentPosition(function(position) {
    let latlng = {lat: position.coords.latitude,
                  lng: position.coords.longitude};
    initMap(latlng);
    getLocations(latlng).then(function(result) {
        result.forEach(element => addElement(element));
    });
});
