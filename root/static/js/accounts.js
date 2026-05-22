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
            let temp = `
            <a href="/email-accounts?account_id=${data[i].account_id}">
              <div class="stat-card">
                <div class="stat-card-header">
                  <div class="stat-card-title">${data[i].account_id}</div>
                  <div class="stat-card-icon primary">
                    <span class="fa fa-ellipsis-v"></span>
                    
                  </div>
                </div>
                <div class="stat-card-value">${data[i].name}</div>
                <div class="stat-card-change positive">
                  <span class="fa fa-check-circle"></span>
                  <span>${data[i].smtp_username}</span>
                </div>
              </div>
            </a>`;
            $(".account-list").append(temp)
          }
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
  let username = $("#ac_username").val().trim();
  let host = $("#ac_host").val().trim();
  let password = $("#ac_pass").val();
  let callback = $("#ac_callback").val();
  let ips = $("#ac_ip").val().trim();
  ips = ips?.split(',') || [];

  let formData = {
    name, username, host, password, callback, ips
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




// ===================== Event Listeners =======================
$(".add-account-btn").click(function(e) {e.preventDefault();$(".add-account-con").addClass("active")})


$(".add-account-form").submit(async function(e) {e.preventDefault();await createAccount()})
$(".account-info-form").submit(async function(e) {e.preventDefault();await updateAccount()})
$(".account-api-form").submit(async function(e) {e.preventDefault();await updateAccount()})
