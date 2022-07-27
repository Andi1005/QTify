const href = window.location.pathname;
const pin = href.match(/[0-9]{4}/);
const url = "http://localhost:5000"

const trackInfoReq = new XMLHttpRequest();

const updateInterval = 60000 // debug, normal is about 1-5s

function requestTrackInfo() {
  trackInfoReq.open("GET", url + "/current-track?pin=" + pin);
  trackInfoReq.send();
}

//recive response
trackInfoReq.onreadystatechange = function(){
  if (this.readyState == 4) {
    if (this.status == 200) {
      document.querySelector(".current-track").style.display = "flex"
      document.querySelector("#no-track-error").style.display = "none"

      trackInfo = JSON.parse(trackInfoReq.responseText);
      updateTrackInfo(trackInfo);
    }
    else if ( this.status == 204) { //There is no song playing
      document.querySelector(".current-track").style.display = "none"
      document.querySelector("#no-track-error").style.display = "block"
    }
  }
}

requestTrackInfo();
window.setInterval(requestTrackInfo, updateInterval);


let trackEndsIn;
let isPlaying = false;
let progress = 0;

function updateTrackInfo(trackInfo) {
  document.querySelector("#current-track-image").src = trackInfo.image;
  document.querySelector("#current-track-name").innerHTML = trackInfo.name;
  document.querySelector("#current-track-artists").innerHTML = trackInfo.artists;
  document.querySelector("#track-progress").max = trackInfo.duration_ms/1000;
  document.querySelector("#track-progress").value = trackInfo.progress_ms/1000;

  isPlaying = trackInfo.is_playing;
  progress = trackInfo.progress_ms/1000;

  trackEndsIn = trackInfo.duration_ms - trackInfo.progress_ms;
  setTimeout(function(){
    requestTrackInfo();
    document.getElementById("track-progress").value = 0
  }, trackEndsIn);
}

const progressUpdateInterval = 200;

window.setInterval(function(){
  // Update progress bar
  progressBar = document.getElementById("track-progress")
  if (isPlaying) {
    progressBar.value += progressUpdateInterval/1000
  }
  else {
    // Ensures that the progress bar stops at the right time
    document.getElementById("track-progress").value = progress
  }
  
}, progressUpdateInterval);


//Send a request on search bar input to /search endpoint
const searchRequest = new XMLHttpRequest();
document.getElementById("search-field").addEventListener('input', function (evt) {
  searchRequest.open("GET", url + "/search?q=" + this.value + "&pin=" + pin);
  searchRequest.send(); 
});

function buildSearchResultElem() {
  const newSearchResult = document.createElement("div");
  newSearchResult.classList.add("track-preview");

  const trackImage = document.createElement("img");
  trackImage.classList.add("track-image");
  newSearchResult.appendChild(trackImage);

  const container = document.createElement("span");
  newSearchResult.appendChild(container);

  const trackName = document.createElement("p");
  trackName.classList.add("track-name");
  container.appendChild(trackName);

  const trackArtists = document.createElement("p");
  trackArtists.classList.add("track-artists");
  container.appendChild(trackArtists);

  return newSearchResult
}


function generateOnClick(track_uri) {
  function addToQueue() {
    const addToQueueReq = new XMLHttpRequest();
    addToQueueReq.open("POST", url + "/queue?pin=" + pin + "&uri=" + track_uri);
    addToQueueReq.send();
  }
  return addToQueue
}

//Recive request response
searchRequest.onreadystatechange = function(){
  if (this.readyState == 4 && this.status == 200) {
    document.querySelector("#no-search-result-error").style.display = "none"

    tracks = JSON.parse(searchRequest.responseText).tracks;

    searchResultContainer = document.getElementById("search-results")
    searchResultElements = searchResultContainer.getElementsByClassName("track-preview")
    let elem = null

    // Update every search result element
    for (let i = 0; i<tracks.length; i++){
      track = tracks[i];

      elem = searchResultElements[i];
      if (elem == null) {
          elem = buildSearchResultElem();
          searchResultContainer.appendChild(elem);
      }
 
      elem.onclick = generateOnClick(track.uri)
      elem.querySelector(".track-image").src = track.image;
      elem.querySelector(".track-name").innerHTML = track.name;
      elem.querySelector(".track-artists").innerHTML = track.artists;
    }
  }
};