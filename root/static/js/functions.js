
function digify(n, decimal=false) {
  let a = Number(n)
  if(decimal) {
    return a.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})
  }
  else{
    return a.toLocaleString()
  }
  
}

function truncateWord(str, n) {
  trunc_str = str.substring(0, n);
  if(str.length > n) {
    trunc_str += "...";
  }
  return trunc_str
}

function shortify(n, decimal=false) {
  let a = Number(n);
  if(a >= 1000000) {
    return `${(a/1000000).toFixed(1)}M`
  }
  else if(a >= 1000) {
    return `${(a/1000).toFixed(1)}K`
  }
  else {
    return digify(n, decimal)
  }
}

function copyText(message) {
  const textArea = document.createElement('textarea');
  textArea.value = message;
  document.body.appendChild(textArea);
  textArea.select();
  document.execCommand('copy');
  document.body.removeChild(textArea)
  pushNotification('success', 'text copied!', 3000)
}

function deslugify(str) {
  var splitted_str = str.split('_');
  var joined_str = splitted_str.join(' ')
  return joined_str
}



function datify(date=null, time=false) {
  if(!date) {date = new Date()}
  let is_date = date instanceof Date

  let date_obj = is_date ? date : new Date(date)
  if(time) {
    return `${date_obj.toDateString()} ${date_obj.toLocaleTimeString()}`
  }
  else {
    return `${date_obj.toDateString()}`;
  }
}

function timify(time) {
  if(time) {
    let [hours, mins] = time.split(':')
    hours = Number(hours);
    let position = (hours >= 12) ? 'PM' : 'AM';
    hours = (hours > 12) ? hours - 12 : hours;
    hours = hours.toString().padStart(2, '0')
    mins = mins.padStart(2, '0')
    return `${hours}:${mins}${position}`
  }
}

function monthify(date) {
  let months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December'
  ]
  
  let dt = new Date(date);
  return `${months[dt.getMonth()]} ${dt.getFullYear()}`
}

function dateDiff(date) {
  let givenDate = new Date(date);
  let today = new Date();

  let diff_years = today.getFullYear() - givenDate.getFullYear();

  if(
    today.getMonth() < givenDate.getMonth() ||
    (today.getMonth() === givenDate.getMonth() && today.getDate() < givenDate.getDate())
  ) {
    diff_years--;
  }
  return diff_years;
}

function extractVariables(str) {
  return [...str.matchAll(/{{\s*(.*?)\s*}}/g)].map(match => match[1])
}



function pushNotification(type, message, time) {
            const colors = { success: 'bg-emerald-500', error: 'bg-red-500', warning: 'bg-amber-500', info: 'bg-blue-500' };
            const toast = $(`
                <div class="toast ${colors[type]} text-white px-6 py-4 rounded-3xl shadow-2xl flex items-center gap-3 max-w-xs">
                    <span class="fa fa-${type === 'success' ? 'check-circle text-green' : type === 'error' ? 'times-circle text-red' : type === 'warning' ? 'warning text-orange' : 'info-circle text-blue'}"></span>
                    <p class="text-sm font-medium">${message}</p>
                </div>
            `);
            $('#toastContainer').append(toast);
            setTimeout(() => toast.fadeOut(time, () => toast.remove()), 4000);
}

function downloadFile(url, filename="") {
  let link = document.createElement('a');
  link.href = url;
  link.target = "_blank";
  link.dowload = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  pushNotification("success", "File downloaded successfully", 4000);
}

function getQueryParams() {
  let params = new URLSearchParams(window.location.search);
  let query = Object.fromEntries(params.entries());
  return query
}

function buildQueryParams(obj, hash=null) {
  if(hash == null) hash = window.location.hash;
  let params = new URLSearchParams(obj);
  let url = `${window.location.protocol}//${window.location.host}/?${params.toString()}${hash}`;
  return url
}



function showLoader(text="Loading...") {
  const overlay = document.getElementById('loading-overlay');
  const progressBar = document.getElementById('progress-bar');
  const loadingText = document.getElementById('loading-text');
  
  overlay.classList.remove('hidden');
  loadingText.textContent = text;
  progressBar.style.width = '0%';

  let progress = 0;
  setInterval(() => {
    progress += Math.random() * 10;
    if (progress > 100) progress = 10;
    progressBar.style.width = progress + '%';
  }, 120);

}

function hideLoader() {
  const overlay = document.getElementById('loading-overlay');
  const progressBar = document.getElementById('progress-bar');
  const loadingText = document.getElementById('loading-text');
  
  loadingText.textContent = "";
  progressBar.style.width = '0%';
  overlay.classList.add('hidden');
}



function showOwl(containerClass, dotsClass) {
    $(containerClass).owlCarousel({
      items: 1,
      loop: false,
      autoplay: false,
      nav: false,   // no arrows
      dots: true,   // show dots
      dotsContainer: dotsClass
    });
}
