/* provided code starts */
function answerBoxTemplate(title, titleDesc) {
  return `<div class=''>
      <h3 class='episode-title'>${title}</h3>
  </div>`
}

function sendFocusTitleIn() {
  document.getElementById("title-in").focus()
}
// function sendFocusYearIn() {
//   document.getElementById("year-in").focus()
// }

function sendFocusDirectorIn() {
  document.getElementById("director-in").focus()
}

function filterText() {
  document.getElementById("answer-box").innerHTML = ""
  console.log(document.getElementById("title-in").value)
  fetch("/episodes?" + new URLSearchParams({ title: document.getElementById("title-in").value }).toString())
    .then((response) => response.json())
    .then((data) => data.forEach(row => {

      let tempDiv = document.createElement("div")
      tempDiv.innerHTML = answerBoxTemplate(row.title, row.desc)
      document.getElementById("answer-box").appendChild(tempDiv)
    }));

}

function showOtherInput() {
  const selectElement = document.getElementById('genre-options');
  const otherInputElement = document.getElementById('other-genre-input');

  if (selectElement.value === 'other') {
    otherInputElement.style.display = 'block';
  } else {
    otherInputElement.style.display = 'none';
  }
}
/* provided code ends */

var songKeywords = [];
var wordCloudShown = [];
initializeWordCloudShown();

function initializeWordCloudShown() {
  for (var i = 0; i < 25; i++) {
    wordCloudShown.push(false);
  }
}

function resetWordCloudShown() {
  for (var i = 0; i < 25; i++) {
    wordCloudShown[i] = false;
  }
}

function submit(e) {
  e.preventDefault();
  console.log('submittt')
  const loadingMessage = document.getElementById('loading');
  loadingMessage.style.display = 'block';
  document.getElementById("output").innerHTML = "";
  var title = document.getElementById("title-in").value;
  var director = document.getElementById("director-in").value;
  var genre = document.getElementById("genre-in").value;
  //var artist = document.getElementById("artist-in").value;
  var emptyTitleError = document.getElementById('empty-input-title-error');
  var emptyGenreError = document.getElementById('empty-input-genre-error');

  var songPopularityFilter = document.getElementById("popularity-range").value;
  var songLengthFilter = document.getElementById("length-range").value;
  var songGenreFilter = new Set();

  var allSongGenresIds = []
  var allSongGenres = []
  for (var songGenreId of document.getElementsByClassName("music-genre")) {
    allSongGenresIds.push(songGenreId.id)
    allSongGenres.push(songGenreId.id.slice(0, -6))

  }
  if (document.getElementById('all').checked) {
    songGenreFilter = allSongGenres
  }
  else {
    for (let i = 0; i < allSongGenres.length; i++) {
      if (document.getElementById(allSongGenresIds[i]).checked) {
        songGenreFilter.add(allSongGenres[i])
      }
    }
  }


  if (genre == "Other") {
    genre = document.getElementById("other-movie-genre").value;
  }

  if (genre == 'Select a genre' || genre == "" || title == "") {
    if (genre == 'Select a genre' || genre == "") {
      emptyGenreError.style.display = 'block';
    }
    else {
      emptyGenreError.style.display = 'none';
    }
    if (title == "") {
      emptyTitleError.style.display = 'block';
    }
    else {
      emptyTitleError.style.display = 'none';
    }
    reset()
    return
  }
  else {
    emptyGenreError.style.display = 'none';
    emptyTitleError.style.display = 'none';
  }
  outDict = { "Title": title, "Director": director, "Genre": genre, "songPopularity": songPopularityFilter, "songLength": songLengthFilter, "songGenres": songGenreFilter };
  //send outDict somewhere... where?
  console.log(outDict);

  if (title == "") {
    title = "a";
  }
  if (director == "") {
    director = "a"
  }
  if (genre == "") {
    genre = "a"
  }
  fetch(
    "/get_output/" + title +
    "/" + director +
    "/" + genre +
    "/" + songPopularityFilter +
    "/" + songLengthFilter
  )
    .then((response) => response.json())
    .then((data) => {
      reset();
      displayOutput(data.song, songPopularityFilter);
      songKeywords = data.keywords;
      resetWordCloudShown();
    })

}

function displayOutput(songList, songPopularityFilter) {

  var output = document.getElementById("output");
  console.log('!!!!!!!!!!')
  console.log(songList)
  if (songList.length == 0) {
    var noOutput = document.createElement("div");
    noOutput.innerHTML = "Sorry, we cannot find any relevant result.";
    output.appendChild(noOutput);
    return;
  }

  if (songPopularityFilter == 1) {
    songList.sort((a, b) => a.popularity - b.popularity);
  } else if (songPopularityFilter == 3) {
    songList.sort((a, b) => b.popularity - a.popularity);
  }

  var rowElements = [];
  var cardElements = [];
  var id = 0;

  for (var song of songList) {
    var c = document.createElement("div");
    c.className = "col-sm-4";
    c.innerHTML = createSongCard(song.title, song.genre, song.duration, song.lyrics, song.features, song.popularity, song.artist, song.link, id);
    cardElements.push(c);
    id++;
  }

  var i = 0;
  while (i < cardElements.length) {
    var row = document.createElement("div");
    row.className = "row";
    row.appendChild(cardElements[i]);
    i++;
    if (i < cardElements.length) {
      row.appendChild(cardElements[i]);
      i++;
    }
    if (i < cardElements.length) {
      row.appendChild(cardElements[i]);
      i++;
    }
    rowElements.push(row);
  }

  for (var row of rowElements) {
    output.appendChild(row);
  }
  const loadingMessage = document.getElementById('loading');
  loadingMessage.style.display = 'none';
}


function generateWordCloud(id) {
  if (wordCloudShown[id]) {
    return;
  }
  wordCloudShown[id] = true;
  var width = window.innerWidth / 5;
  var height = window.innerHeight / 3;

  var svg = d3.select("#song-cloud-" + id).append("svg")
    .attr("width", width)
    .attr("height", height)
    .append("g");

  var layout = d3.layout.cloud()
    .size([width, height])
    .words(songKeywords[id].map(function (d) { return { text: d }; }))
    .padding(5)
    .rotate(0)
    .fontSize(20)
    .on("end", draw);
  layout.start();

  function draw(words) {
    svg
      .append("g")
      .attr("transform", "translate(" + layout.size()[0] / 2 + "," + layout.size()[1] / 2 + ")")
      .selectAll("text")
      .data(words)
      .enter().append("text")
      .style("font-size", 20)
      .style("fill", "#69b3a2")
      .attr("text-anchor", "middle")
      .style("font-family", "cursive")
      .attr("transform", function (d) {
        return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
      })
      .text(function (d) { return d.text; });
  }

}


function createSongCard(title, genre, duration, lyrics, features, popularity, artist, link, id) {
  var minute = Math.floor(duration / 1000 / 60);
  var durationText = minute + " minutes and " + Math.floor((duration - minute * 1000 * 60) / 1000) + " seconds";
  var infoCollapseId = "song-info-collapse-" + id;
  var lyricCollapseId = "song-lyric-collapse-" + id;
  var cloudCollapseId = "song-cloud-collapse-" + id;
  var songCloudId = "song-cloud-" + id;

  var title_split = title.split(" ")
  var artist_split = artist.split(" ")
  var link = 'https://open.spotify.com/search/'
  for (let i = 0; i < title_split.length; i++) {
    link += title_split[i] + '%20'
  }
  for (let i = 0; i < artist_split.length - 1; i++) {
    link += artist_split[i] + '%20'
  }
  link += artist_split[artist_split.length - 1]
  console.log(link)

  const featureText = featureToText(features)

  return `
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">${title}</h5>
        <h5 class="song-info">
          <span class="artist">${artist} | </span>
          <span class="genre">${genre}  </span>
          <br />
          <span class="duration">${durationText}</span>
          <br />
          <span class="popularity">Popularity: ${popularity}</span>
        </h5>
        <button class="btn btn-primary" type="button" onclick="openURL('${link}')">
        Listen on Spotify
      </button>
        <button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#${infoCollapseId}"
          aria-expanded="false" aria-controls=${infoCollapseId}>
          Song Characteristics
        </button>
        <div class="collapse song-collapse" id=${infoCollapseId}>
          <div class="card card-body">
            <p> ${featureText.energy}</p>
            <div class="progress">
              <div class="progress-bar" role="progressbar" style="width: ${features.energy * 100}%" aria-valuemin="0" aria-valuemax="1">
                Energy
              </div>
            </div>
            <p> ${featureText.valence}</p>
            <div class="progress">
              <div class="progress-bar" role="progressbar" style="width: ${features.valence * 100}%" aria-valuemin="0" aria-valuemax="1">
                Valence
              </div>
              
            </div>
            <p> ${featureText.instrumentalness}</p>
            <div class="progress">
              <div class="progress-bar" role="progressbar" style="width: ${features.instrumentalness * 100}%" aria-valuemin="0" aria-valuemax="1">
                Instrumentalness
              </div>
            </div>
          </div>
        </div>
        <button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#${lyricCollapseId}"
          aria-expanded="false" aria-controls=${lyricCollapseId}>
          Song Lyrics
        </button>
        <div class="collapse song-collapse" id=${lyricCollapseId}>
          <div class="card card-body song-lyric">${lyrics}</div>
        </div>
        <button class="btn btn-primary" type="button" data-toggle="collapse" data-target="#${cloudCollapseId}"
          aria-expanded="false" aria-controls=${cloudCollapseId} onclick='generateWordCloud(${id})'>
          Song Cloud
        </button>
        <div class="collapse song-collapse" id=${cloudCollapseId}>
          <div class="card card-body song-cloud" id=${songCloudId}></div>
        </div>
      </div>
    </div>
  `
}

function toggleGenreChecks() {
  var checkboxes = document.getElementsByClassName("music-genre");
  var allChecked = document.getElementById("all");
  var checkValue = allChecked.checked ? true : false;

  for (var check of checkboxes) {
    check.checked = checkValue;
  }
}

function toggleAllGenreCheck() {
  var checkboxes = document.getElementsByClassName("music-genre");
  var allChecked = document.getElementById("all");
  var checkValue = true
  for (var check of checkboxes) {
    if (!(check.checked)) {

      checkValue = false
    }
  }
  //console.log(checkValue)
  allChecked.checked = checkValue
  //console.log("allchecked is check: ", allChecked.checked)
  //console.log("elt is check: ", document.getElementById("all").checked)
}

function toggleCollapseText() {
  var toggleButton = document.getElementById("genreToggleButton");
  if (toggleButton.innerHTML == "Show") {
    toggleButton.innerHTML = "Hide";
  } else {
    toggleButton.innerHTML = "Show";
  }
}

function openURL(link) {
  const url = link;
  window.open(url, '_blank');
}

function featureToText(features) {
  let featureText = {}

  if (features.danceability < .5) {
    featureText["danceability"] = "low danceability (score = " + Math.round(features.danceability * 100) + "%)"
  }
  else {
    featureText["danceability"] = "high danceability (score = " + Math.round(features.danceability * 100) + "%)"
  }
  if (features.speechiness < .5) {
    featureText["speechiness"] = "instrumental (score = " + Math.round(features.speechiness * 100) + "%)"
  }
  else {
    featureText["speechiness"] = "lyrical (score = " + Math.round(features.speechiness * 100) + "%)"
  }
  if (features.acousticness < .5) {
    featureText["acousticness"] = "not acoustic (score = " + Math.round(features.acousticness * 100) + "%)"
  }
  else {
    featureText["acousticness"] = "very acoustic (score = " + Math.round(features.acousticness * 100) + "%)"
  }

  if (features.instrumentalness < .5) {
    console.log()
    featureText["instrumentalness"] = "text-heavy (score = " + Math.round(features.instrumentalness * 100) + "%)"
  }
  else {
    featureText["instrumentalness"] = "largely instrumental (score = " + Math.round(features.instrumentalness * 100) + "%)"
  }
  if (features.valence < .5) {
    featureText["valence"] = "sad (score = " + Math.round(features.valence * 100) + "%)"
  }
  else {
    featureText["valence"] = "happy (score = " + Math.round(features.valence * 100) + "%)"
  }
  if (features.energy < .5) {
    featureText["energy"] = "low energy (score = " + Math.round(features.energy * 100) + "%)"
  }
  else {
    featureText["energy"] = "high energy (score = " + Math.round(features.energy * 100) + "%)"
  }
  return featureText

}

function reset() {
  const loadingMessage = document.getElementById('loading');
  loadingMessage.style.display = 'none';
  document.getElementById("output").innerHTML = "";
}

function toggleExplainText() {
  console.log('toggle')
  var toggleButton = document.getElementById("explainToggleButton");
  var explanation = document.getElementById("explanation");
  if (toggleButton.innerHTML == "Show how we get your results") {
    toggleButton.innerHTML = "Hide explanation";
    explanation.style.display = 'block';
  } else {
    toggleButton.innerHTML = "Show how we get your results";
    explanation.style.display = 'none';
  }
}

function initialize() {
  document.getElementById("input-form").addEventListener('submit', submit);
  document.getElementById("input-form").addEventListener('reset', reset);
  document.getElementById("all").addEventListener('click', toggleGenreChecks);
  for (var songGenreId of document.getElementsByClassName("music-genre")) {
    songGenreId.addEventListener('click', toggleAllGenreCheck);
  }
  //document.getElementsByClassName("music-genre").addEventListener('click', toggleAllGenreCheck);
  document.getElementById("all").checked = true;
  document.getElementById("genreToggleButton").innerHTML = "Show";
  document.getElementById("genreToggleButton").addEventListener('click', toggleCollapseText);
  document.getElementById("explainToggleButton").addEventListener('click', toggleExplainText);
}
