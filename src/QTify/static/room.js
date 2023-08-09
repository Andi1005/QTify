const pin = window.location.pathname.match(/[0-9]+/);
const url = `${window.location.protocol}//${window.location.hostname}:${window.location.port}`;

const updateInterval = 10000

let spotifyIsActitiv;

let recommendations = [];
let recomsIdx = 0;

let trackEndsIn;
let isPlaying = false;
let progress = 0;

let current_track;

function buildQueryString(endpoint, query) {
  const params = new URLSearchParams(query);
  return url + endpoint + "?" + params.toString();
}

function flashMessage(msg) {
  messageBox = document.getElementsByClassName("message-flash")[0];
  messageBox.innerHTML = msg;
  messageBox.classList.add("activ");
  setTimeout(function() {
    messageBox.classList.remove("activ")
  }, 3000)
}

// ---- Request current-track ----
const trackInfoReq = new XMLHttpRequest();

//send request
function requestTrackInfo() {
  trackInfoReq.open("GET", buildQueryString("/current-track", {pin: pin}));
  trackInfoReq.send();
}

//recive response
trackInfoReq.onreadystatechange = function(){
  if (this.readyState == 4) {
    if (this.status == 200) {
      if (!spotifyIsActitiv) {
        onSpotifyActiv()
      }
      
      let trackInfo = JSON.parse(trackInfoReq.responseText);
      updateTrackInfo(trackInfo);

      updateQueueView(trackInfo.queue);

      if (trackInfo.name != current_track){
        recommendations = trackInfo.similar_tracks;
        recomsIdx = 0;
      }
      current_track = trackInfo.name
    }
    
    else if (this.status == 204 && spotifyIsActitiv) { //Spotify isn't activ
      onSpotifyInactiv()
    }
  }
}

requestTrackInfo();
window.setInterval(requestTrackInfo, updateInterval);


function onSpotifyInactiv() {
  spotifyIsActitiv = false;
  document.querySelector("#current-track").style.display = "none";
  document.querySelector("#search").style.display = "none";
  document.querySelector("#queue").style.display = "none";
  document.querySelector("#not-activ-error").style.display = "block";
}

function onSpotifyActiv() {
  spotifyIsActitiv = true;
  document.querySelector("#current-track").style.display = "block";
  document.querySelector("#not-activ-error").style.display = "none";
}

function updateTrackInfo(trackInfo) {
  document.querySelector("#current-track-image").src = trackInfo.image;
  
  if (!(trackInfo.color === undefined)){
    c = trackInfo.color;
    document.querySelector("#current-track-image").style.boxShadow = "0px 0px 200px 15px" + c;
  }
  else {
    document.querySelector("#current-track-image").style.boxShadow = "none";
  }
    
  document.querySelector("#current-track-name").innerHTML = trackInfo.name;
  document.querySelector("#current-track-artists").innerHTML = trackInfo.artists;
  document.querySelector("#track-progress").max = trackInfo.duration_ms/1000;
  document.querySelector("#track-progress").value = trackInfo.progress_ms/1000;

  if (trackInfo.is_playing) {
    document.querySelector("#is-paused").style.display = "none"
  } else {
    document.querySelector("#is-paused").style.display = "block"
  }

  isPlaying = trackInfo.is_playing;
  progress = trackInfo.progress_ms/1000;

  // request the new track after the current ends
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


function updateQueueView(queue) {
  queueView = document.getElementById("queue-view");
  trackContainers = queueView.getElementsByClassName("track-preview");

  if (queue.length == 0) {
    document.getElementById("no-queue").style.display = "block";
  } 
  else {
    document.getElementById("no-queue").style.display = "none";
  }

  while (trackContainers.length > 0) {
    trackContainers[0].remove();
  }

  for (let j=0; j<queue.length; j++) {
    track = queue[j];
    queueView = document.querySelector("#queue-view");

    newQueueNode = buildTrackContainer(track);

    queueView.appendChild(newQueueNode); 
  }
}


// ---- Skipping a track ----
const skipTrackReq = new XMLHttpRequest();

function skipTrack() {
  skipTrackReq.open("POST", buildQueryString("/skip", {pin: pin}));
  skipTrackReq.send();
}

skipTrackReq.onreadystatechange = function(){
  if (this.readyState == 4) {
    if (this.status == 204) {
      flashMessage("Skiped");
      requestTrackInfo()
    }
    else {
      flashMessage("Something went wrong");
    }
    document.getElementById("skip-btn").blur();
  }
}


// ---- Search ----
const searchRequest = new XMLHttpRequest();

// Send request on every input change of the search field.
document.getElementById("search-field").addEventListener('input', function (evt) {
  if (this.value == "") {
    closeSearchBar()
  } else {
    const queryString = buildQueryString("/search", {q: this.value, pin: pin});
    searchRequest.open("GET", queryString);
    searchRequest.send(); 
  }
});

//Recive request response
searchRequest.onreadystatechange = function(){
  if (this.readyState == 4) {
    if (this.status == 200) {
      document.querySelector("#search-results-container").style.visibility = "visible";
      document.querySelector("#search-back-btn").style.display = "block";

      const tracks = JSON.parse(searchRequest.responseText).tracks;

      const searchResultContainer = document.getElementById("search-results");
      const searchResultElements = searchResultContainer.getElementsByClassName("track-preview");
      let elem = null;

      // Update every search result element
      for (let i = 0; i<tracks.length; i++){
        track = tracks[i];

        elem = searchResultElements[i];
        if (elem == null) {
            elem = buildTrackContainer(track);
            searchResultContainer.appendChild(elem);
        }
        else {
          elem.querySelector(".track-image").src = track.image;
          elem.querySelector(".track-name").innerHTML = track.name;
          elem.querySelector(".track-artists").innerHTML = track.artists;
  
        }
  
        elem.onclick = generateOnClick(track.uri);
      } 
    }
    else {
      closeSearchBar()
    }
  }
};


function buildTrackContainer(track) {
  const newTrackContainer = document.createElement("div");
  newTrackContainer.classList.add("track-preview");
  newTrackContainer.classList.add("search-result-track");

  const trackImage = document.createElement("img");
  trackImage.classList.add("track-image");
  trackImage.src = track.image_url;
  newTrackContainer.appendChild(trackImage);

  const container = document.createElement("span");
  newTrackContainer.appendChild(container);

  const trackName = document.createElement("p");
  trackName.classList.add("track-name");
  trackName.innerHTML = track.name;
  container.appendChild(trackName);

  const trackArtists = document.createElement("p");
  trackArtists.classList.add("track-artists");
  trackArtists.innerHTML = track.artist;
  container.appendChild(trackArtists);

  return newTrackContainer;
}


// Send a request to add the track to queue, if the button is pressed
function generateOnClick(track_uri) {
  const addToQueueReq = new XMLHttpRequest();

  function addToQueue() {
    const queryString = buildQueryString("/queue", {uri: track_uri, pin: pin});
    addToQueueReq.open("POST", queryString);
    addToQueueReq.send();
  }

  addToQueueReq.onreadystatechange = function(){
    if (this.readyState == 4) {
      if (this.status == 204) {
        flashMessage("Added to playback queue")
      }
    }
  }

  return addToQueue
}


// ---- Dynamic search bar ----
const searchField = document.querySelector("#search-field");
const defaultPlaceholder = searchField.placeholder;
let current_recom;
let charIdx = searchField.placeholder.length - 1;
const speed = 60;
const cycleSpeed = 15000
const recomPhrases = [
  "Versuchs mal mit",
  "Wie währe es mit",
  "Magst du",
  "Krasser Banger:",
  "Was hält`s du von",
  "Suche doch mal nach",
]

function cycleTrackRecommendations() {
  if (searchField.value == "" && recommendations != null) {
    removePlaceholder();  
  }
  else {
    setTimeout(cycleTrackRecommendations, cycleSpeed);
  }
}

setTimeout(cycleTrackRecommendations, cycleSpeed);

function removePlaceholder() {
  if (charIdx >= 0) {
    searchField.placeholder = searchField.placeholder.slice(0, charIdx);
    charIdx--;
    setTimeout(function (){removePlaceholder()}, speed);
  }
  else {

    if (recommendations.length === 0) {
      newPlaceholder = defaultPlaceholder
    } else {
      recomPhrase = recomPhrases[Math.floor(Math.random() * recomPhrases.length)]
      current_recom = recommendations[recomsIdx]
      newPlaceholder = recomPhrase + " \"" + current_recom + "\" ?"
    }
    addPlaceholder(newPlaceholder);
  }
}

function addPlaceholder(newPlaceholder) {
  if (charIdx < newPlaceholder.length) {
    searchField.placeholder += newPlaceholder.charAt(charIdx);
    charIdx++;
    setTimeout(function (){addPlaceholder(newPlaceholder)}, speed);
  }
  else {
    recomsIdx ++;
    if (recomsIdx >= recommendations.length) {
      recomsIdx = 0;
    }
    setTimeout(cycleTrackRecommendations, cycleSpeed);
  }
}

// Clear the sehrch bar, if the X button is pressed
function closeSearchBar() {
  searchField.value = ""
  document.querySelector("#search-results-container").style.visibility = "hidden";
  document.querySelector("#search-back-btn").style.display = "none";
}


// Search for the current recomendation, if the search button is pressed while a recomendation is shown
function searchRecommendation() {
  if (searchField.value == "" && searchField.placeholder != defaultPlaceholder) {
    searchField.value = current_recom
    document.getElementById("search-field").dispatchEvent(new Event('input'));
  }
}


// ---- Change between tabs ----
function openTab(newTab, container) {
  if (spotifyIsActitiv) {
    // Deaktivae all tabs
    tabs = document.getElementsByClassName(container);
    for (let i = 0; i<tabs.length; i++) {
      tabs[i].style.display = "none";
    }

    // Only show the selected tab
    document.getElementById(newTab).style.display = "block";
  }
}


// ---- QR Code ----
function showQROverlay(pin) {
  qrOverlay = document.getElementById("qrcode-overlay")
  if (!qrOverlay.querySelector("#qrcode").innerHTML) {
      generateQRCode(pin)
  }
  qrOverlay.style.display = "block";
}


function hideQROverlay() {
  document.getElementById("qrcode-overlay").style.display = "none";
}

QRCode = new QRCode(document.getElementById("qrcode"), url + "/room/" + pin);
document.getElementById("room-pin").innerHTML = pin;