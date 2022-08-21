const pin = window.location.pathname.match(/[0-9]+/);
const url = `${window.location.protocol}//${window.location.hostname}:${window.location.port}`;

const updateInterval = 6000

let spotifyIsActitiv;

let recommendations = [];
let recomsIdx = 0;

let trackEndsIn;
let isPlaying = false;
let progress = 0;

let current_track;


function flashMessage(msg) {
  messageBox = document.getElementsByClassName("message-flash")[0];
  messageBox.innerHTML = msg;
  messageBox.classList.add("activ");
  setTimeout(function() {
    messageBox.classList.remove("activ")
  }, 3000)
}


function buildQueryString(endpoint, query) {
  const params = new URLSearchParams(query);
  return url + endpoint + "?" + params.toString();
}


const trackInfoReq = new XMLHttpRequest();
function requestTrackInfo() {
  trackInfoReq.open("GET", buildQueryString("/current-track", {pin: pin}));
  trackInfoReq.send();
}


//recive response
trackInfoReq.onreadystatechange = function(){
  if (this.readyState == 4) {
    if (this.status == 200) {
      spotifyIsActitiv = true;
      document.querySelector("#current-track-container").style.display = "block";
      document.querySelector("#search-bar").style.display = "flex";
      document.querySelector("#search-results-container").style.display = "block";
      document.querySelector("#not-activ-error").style.display = "none";

      trackInfo = JSON.parse(trackInfoReq.responseText);
      updateTrackInfo(trackInfo);

      if (trackInfo.name != current_track){
        recommendations = trackInfo.similar_tracks;
        recomsIdx = 0;
      }
      current_track = trackInfo.name
    }
    
    else if ( this.status == 204) { //Spotify isn't activ
      spotifyIsActitiv = false;
      document.querySelector("#current-track-container").style.display = "none";
      document.querySelector("#search-bar").style.display = "none";
      document.querySelector("#search-results-container").style.display = "none";
      document.querySelector("#not-activ-error").style.display = "block";
    }
  }
}


requestTrackInfo(); //Call once at start
window.setInterval(requestTrackInfo, updateInterval);


function updateTrackInfo(trackInfo) {
  document.querySelector("#current-track-image").src = trackInfo.image;
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
      console.log(this.responseText);
    }
    document.getElementById("skip-btn").blur();
  }
}

//Send a request on search bar input to /search endpoint
const searchRequest = new XMLHttpRequest();
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
            elem = buildSearchResultElem();
            searchResultContainer.appendChild(elem);
        }
  
        elem.onclick = generateOnClick(track.uri);
        elem.querySelector(".track-image").src = track.image;
        elem.querySelector(".track-name").innerHTML = track.name;
        elem.querySelector(".track-artists").innerHTML = track.artists;
      } 
    }
    else {
      closeSearchBar()
    }
  }
};


function buildSearchResultElem() {
  const newSearchResult = document.createElement("div");
  newSearchResult.classList.add("track-preview");
  newSearchResult.classList.add("search-result-track");

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

  return newSearchResult;
}


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


function closeSearchBar() {
  searchField.value = ""
  document.querySelector("#search-results-container").style.visibility = "hidden";
  document.querySelector("#search-back-btn").style.display = "none";
}


function searchRecommendation() {
  if (searchField.value == "" && searchField.placeholder != defaultPlaceholder) {
    searchField.value = current_recom
    document.getElementById("search-field").dispatchEvent(new Event('input'));
  }
}


const searchResultsNumber = 10
for (let i = 0; i<searchResultsNumber; i++){
    buildSearchResultElem()
}


setTimeout(cycleTrackRecommendations, cycleSpeed);


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