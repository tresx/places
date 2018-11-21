let map;
let geocoder;

// Takes an element with postcode, id, name & description attributes
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
						<h3>${element.name}</h3>
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

function initMap(latlng) {
	geocoder = new google.maps.Geocoder();
	map = new google.maps.Map(
		document.getElementById('place-map'), {center: latlng, zoom: 15});
	addElement(element);
}

initMap(latlng);
