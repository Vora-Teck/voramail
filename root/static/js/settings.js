import * as API from "../module/api.js";

showLoader("Loading data...")

async function getPublicKey() {
  let data = await API.publicKey()
  //console.log(data)
  if(data.error) {
    pushNotification("n_error", data.error, 5000)
  }
  else {
    $("#api_key").val(data.public_key)
  }
  hideLoader()
}

getPublicKey()

async function generateKey() {
  showLoader("Processing...")
  let data = await API.generateKey()
  //console.log(data)
  if(data.error) {
    pushNotification("error", data.error, 5000)
  }
  else {
    pushNotification("success", data.message, 3000);
    $("#secret_key").val(data.secret_key)
    $(".secret-input").show();
    $(".gen-btn").hide();
  }
  hideLoader()
}


async function updatePassword() {
  let old_password = $("#old_pass").val();
  let new_password = $("#new_pass").val();
  let cnew_password = $("#cnew_pass").val();

  if(!old_password || !new_password) {
    pushNotification("warning", "Password field cannot be empty!", 5000);
    return
  }

  if(cnew_password !== new_password) {
    pushNotification("warning", "Passwords do not match!", 5000);
    return
  }

  let payload = {old_password, new_password}
  //console.log(payload)
  showLoader("Updating...")
  try {
    let data = await API.updatePassword(payload)
    //console.log(data)
    if(data.error) {
      pushNotification("error", data.error, 5000)
    }
    else {
      pushNotification("success", data.message, 3000)
      $(".pass-form")[0].reset();
    }
  }
  catch(err) {
    pushNotification("error", err, 5000)
  }
  finally {hideLoader()}
}

$(".secret-input").hide();


$(".gen-btn").click(async function(e) {
  e.preventDefault();
  await generateKey()
})

$(".logout-btn").click(async function(e) {
  e.preventDefault();
  await API.clearKey("access_token")
  await API.clearKey("refresh_token")
  pushNotification("success", "Logout successful", 3000)
  location.href = "/login"
})



$(".pass-form").submit(async function(e) {
  await e.preventDefault();
  await updatePassword()
})
