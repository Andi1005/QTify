const href = window.location.pathname;
const pin = href.match(/[0-9]{4}/);
const url = "http://localhost:5000"

const trackInfoReq = new XMLHttpRequest();

const updateInterval = 60000 // debug, normal is about 1-5s

function requestTrackInfo() {
  trackInfoReq.open("GET", url + "/current-track?pin=" + pin);
  trackInfoReq.send();
}

trackInfoReq.onreadystatechange = function(){
  if (this.readyState == 4 && this.status == 200) {
    trackInfo = JSON.parse(trackInfoReq.responseText);
    updateTrackInfo(trackInfo);
  }
}

requestTrackInfo();
window.setInterval(requestTrackInfo, updateInterval);


let trackEndsIn;
let isPlaying = false;
let progress = 0;

function updateTrackInfo(trackInfo) {
  document.getElementById("current-track-image").src = trackInfo.image;
  document.getElementById("current-track-name").innerHTML = trackInfo.name;
  document.getElementById("current-track-artists").innerHTML = trackInfo.artists;
  document.getElementById("track-progress").max = trackInfo.duration_ms/1000;
  document.getElementById("track-progress").value = trackInfo.progress_ms/1000;

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
  progressBar = document.getElementById("track-progress")
  if (isPlaying) {
    progressBar.value += progressUpdateInterval/1000
  }
  else {
    //ensures that the progress bar stops at the right time
    document.getElementById("track-progress").value = progress
  }
  
}, progressUpdateInterval);


const searchRequest = new XMLHttpRequest();

document.getElementById("search-field").addEventListener('input', function (evt) {
  searchRequest.open("GET", url + "/search?q=" + this.value + "&pin=" + pin);
  searchRequest.send(); 
});

searchRequest.onreadystatechange = function(){
  if (this.readyState == 4 && this.status == 200) {
    tracks = JSON.parse(searchRequest.responseText);

    searchResultContainer = document.getElementById("search-results")
    searchResultElements = searchResultContainer.getElementsByClassName("search-result")

    for (let track of tracks.tracks) {
      console.log(track.name);
    }
  }
};