import * as API from "../module/api.js";

let accountListView = $("#accounts");
let accountDetailView = $("#account_settings");
let allView = $(".agent-view")

async function showView(view) {
  allView.hide()
  view.show()
}


async function getAccounts() {
  showLoader("Loading data...")
  $(".account-list").empty()
  try {
    let data = await API.getAccounts()
    //console.log(data)
    if(data.error) {
      pushNotification("error", data.error, 5000)
    }
    else {
      if(data.length  === 0) {
          $(".empty-state").removeClass("w-hide")
          $(".account-list").addClass("w-hide")
      }
      else {
          $(".empty-state").addClass("w-hide")
          $(".account-list").removeClass("w-hide");


          for(let i in data) {

            let temp2 = `
            <div class="relative w-full max-w-sm rounded-2xl border border-gray-800 bg-gray-900/80 backdrop-blur shadow-2xl transition hover:border-gray-700 hover:shadow-blue-500/10">
  
              <!-- Top Section -->
              <div class="flex items-start justify-between p-3">
          
                <!-- Project Info -->
                <div class="flex items-center gap-4">
          
                  <!-- Icon -->
                  <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg"
                        class="h-6 w-6 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor">
                      <path stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M3 7l9-4 9 4-9 4-9-4zm0 5l9 4 9-4m-18 5l9 4 9-4"/>
                    </svg>
                  </div>
                  <!-- Text -->
                  <div>
                    <h3 class="text-lg font-semibold text-white">
                    ${data[i].name}
                    </h3>
                    <p class="mt-1 text-sm text-gray-400">
                      ${data[i].smtp_data.provider} • ${data[i].active ? `Active` : 'Inactive'}
                    </p>
                  </div>
                </div>
                
                <!-- Dropdown -->
                <div class="relative">
                  <!-- Button -->
                  <button
                    class="opt-btn flex h-10 w-10 items-center justify-center rounded-lg text-gray-400 transition hover:bg-gray-800 hover:text-white"
                  >
                    <!-- Vertical Ellipsis -->
                    <i class="fa fa-ellipsis-v"></i>
                  </button>
                  <!-- Menu -->
                  <div
                    id="dropdownMenu"
                    class="dropdownMenu absolute right-0 z-50 mt-2 hidden w-48 overflow-hidden rounded-xl border border-gray-800 bg-gray-900 shadow-2xl"
                  >
          
                  <a href="#" onclick="copyText('${data[i].account_id}')"
                    class="flex items-center gap-3 px-4 py-3 text-sm text-gray-300 transition hover:bg-gray-800 hover:text-white">
                    <span class="fa fa-copy"></span>
                    Copy Account ID
                  </a>
          
                    <a href="/email-accounts?account_id=${data[i].account_id}"
                      class="flex items-center gap-3 px-4 py-3 text-sm text-gray-300 transition hover:bg-gray-800 hover:text-white">
                      <span class="fa fa-gear"></span>
                      Settings
                    </a>

                    <a href="/mails?account_id=${data[i].account_id}"
                      class="flex items-center gap-3 px-4 py-3 text-sm text-gray-300 transition hover:bg-gray-800 hover:text-white">
                      <span class="fa fa-envelope"></span>
                      View Mails
                    </a>
          
                    <div class="border-t border-gray-800"></div>
          
                    <a href="#" data-id="${data[i].account_id}" data-name="${data[i].name} - ${data[i].smtp_username}"
                      class="acc-del-btn flex items-center gap-3 px-4 py-3 text-sm text-red-400 transition hover:bg-red-500/10 hover:text-red-300">
                      <span class="fa fa-trash"></span>
                      Delete Account
                    </a>
          
                  </div>
          
                </div>
          
              </div>

              <p class="p-3 text-sm text-gray-500">${data[i].smtp_username}</p>
          
              <!-- Footer -->
              <div class="border-t border-gray-800 px-3 py-3 text-sm text-gray-500">
                Updated ${datify(data[i].updated_at, true)}
              </div>
          
            </div>`;
            $(".account-list").append(temp2)
          }

          $(".opt-btn").on('click', function() {
            $(this).siblings(".dropdownMenu").toggleClass('hidden')
          })

          $(".acc-del-btn").on('click', function() {
            let id = $(this).data('id');
            let name =  $(this).data('name');
            $(".acco_name").text(name)
            $("#acco_id").val(id)
            $(".delete-account-con").addClass('active')
          })
      }
    }
  }
  catch(err) {
    pushNotification("error", err, 5000)
  }
  finally {
    hideLoader()
  }
  
}

async function getAccount(account_id) {
  
  try {
    let data = await API.getAccount(account_id)
    //console.log(data)
    if(data.error) {
      pushNotification("error", data.error, 5000)
      await showView(accountListView)
      await getAccounts()
    }
    else {
      $(".account_full").html(`${data.name} - ${data.account_id}`)
      $("#ac_name").val(data.name);
      $("#ac_id").val(data.account_id);
      $("#ac_username").val(data.smtp_username);
      $("#ac_host").val(data.smtp_host);
      $("#ac_port").val(`${data.encryption.port} - ${data.encryption.encryption}`);
      $("#ac_pass").val(data.smtp_password || '');
      $("#ac_callback").val(data.callback_url);
      $("#ac_ip").val(data.ip_whitelist?.join(', ') || '');
      $("#ac_learn").attr('href', data.smtp_data.password_help_url)
    }
  }
  catch(err) {
    pushNotification("error", err, 5000)
  }
  finally {
    hideLoader()
  }
}

async function setup() {
  let query = getQueryParams();
  if(query.account_id) {
    showLoader("Loading data...")
    await showView(accountDetailView)
    await getAccount(query.account_id)
  }
  else {
    await showView(accountListView)
    await getAccounts()
  }
}

setup()

async function createAccount() {
  let name = $("#account_name").val().trim();
  let username = $("#account_username").val().trim();
  let host = $("#account_host").val().trim();

  if(username == "" || name == "" || host == "") {
    pushNotification("error", "All fields are required", 5000);
    return
  }

  let payload = {name, username, host}
  //console.log(payload)
  showLoader("Creating Account...")
  let data = await API.createAccount(payload)
  //console.log(data)
  if(data.error) {
    pushNotification("error", data.error, 5000)
  }
  else {
    pushNotification("success", data.message, 3000)
    $(".add-account-form")[0].reset();
    $(".add-account-con").removeClass("active");
    getAccounts()
  }
  hideLoader()
}

async function updateAccount() {
  let account_id = $("#ac_id").val();
  let name = $("#ac_name").val().trim();
  let password = $("#ac_pass").val();
  let callback = $("#ac_callback").val();
  let ips = $("#ac_ip").val().trim();
  ips = ips?.split(',') || [];

  let formData = {
    name, password, callback, ips
  }
  
  showLoader("Updating configuration...")
  try {
    let data = await API.updateAccount(account_id, formData)
    //console.log(data)
    if(data.error) {
      pushNotification("error", data.error, 5000)
    }
    else {
      pushNotification("success", data.message, 3000);
      getAccount(account_id)
    }
  }
  catch(err) {
    pushNotification("error", err, 5000)
  }
  finally {hideLoader()}

}

async function deleteAccount() {
  let account_id = $("#acco_id").val().trim();

  if(!account_id || account_id == "") {
    pushNotification("error", "Invalid selected account", 5000);
    return
  }

  //console.log(payload)
  showLoader("Deleting Account...")
  let data = await API.deleteAccount(account_id)
  //console.log(data)
  if(data.error) {
    pushNotification("error", data.error, 5000)
  }
  else {
    pushNotification("success", data.message, 3000)
    $(".delete-account-form")[0].reset();
    $(".delete-account-con").removeClass("active");
    getAccounts()
  }
  hideLoader()
}



// Optional: close when clicking outside
$(document).on("click", function (e) {
  const menu = $(".dropdownMenu");

  if (
    !e.target.closest(".dropdownMenu") &&
    !e.target.closest("button")
  ) {
    menu.addClass("hidden");
  }
});



// ===================== Event Listeners =======================
$(".add-account-btn").click(function(e) {e.preventDefault();$(".add-account-con").addClass("active")})


$(".add-account-form").submit(async function(e) {e.preventDefault();await createAccount()})
$(".delete-account-form").submit(async function(e) {e.preventDefault();await deleteAccount()})
$(".account-info-form").submit(async function(e) {e.preventDefault();await updateAccount()})
$(".account-api-form").submit(async function(e) {e.preventDefault();await updateAccount()})
