let cityChanger = document.getElementById('cityChanger');
cityChanger.value = 'Все';


let currentCity = document.getElementById('currentCityTextValue');

if (currentCity.innerText) {
  localStorage.setItem('currentCity', currentCity.innerText)
} else {
  currentCity.innerText = localStorage.getItem('currentCity')
}

let currentCityValue = localStorage.getItem('currentCity')

cityChanger.value = currentCityValue;


function setCurCity() {
  let cityChangerValue = document.getElementById('cityChanger').value;
  if (cityChangerValue !== localStorage.getItem('currentCity')) {
    currentCity.innerText = cityChangerValue;
    localStorage.setItem('currentCity', cityChangerValue)
  }
}