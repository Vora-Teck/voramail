import * as API from "../module/api.js";


function switchTab(n) {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const tabLogin = document.getElementById('tab-login');
    const tabSignup = document.getElementById('tab-signup');

    if (n === 0) {
      loginForm.classList.remove('hidden');
      signupForm.classList.add('hidden');
      tabLogin.classList.add('border-b-2', 'border-emerald-500', 'text-white');
      tabSignup.classList.remove('border-b-2', 'border-emerald-500', 'text-white');
    } else {
      loginForm.classList.add('hidden');
      signupForm.classList.remove('hidden');
      tabLogin.classList.remove('border-b-2', 'border-emerald-500', 'text-white');
      tabSignup.classList.add('border-b-2', 'border-emerald-500', 'text-white');
    }
}


function simulateSocial(provider) {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    overlay.classList.remove('hidden');
    loadingText.textContent = `Connecting to ${provider}...`;
    
    setTimeout(() => {
      alert(`✅ Successfully signed in with ${provider}!\n\n(This is a demo simulation)`);
      overlay.classList.add('hidden');
    }, 1600);
}


$("#tab-login").on('click', function() {switchTab(0)})
$("#tab-signup").on('click', function() {switchTab(1)})


async function authenticate() {
    let email = $('#login-email').val();
    let password = $('#login-password').val();

    if(!email || !password) {
        pushNotification("error", "Email or password cannot be empty", 3000);
        return
    }
    const formData = {email, password}
    showLoader("Authenticating...")

    try {
        let data = await API.login(formData);
        //console.log(data);
        if (data.error) {
            pushNotification("error", data.error, 5000)
        }
        else if(data.access_token && data.refresh_token) {
            await API.setKey("access_token", data.access_token);
            await API.setKey("refresh_token", data.refresh_token);
            pushNotification("success", "Login Successful!", 5000);
            location.href = "/dashboard"
        }
        hideLoader()
    }
    catch(err) {
        console.log(err)
        pushNotification("error", err, 3000)
        hideLoader()
    }
}

async function register() {
    let first_name = $("#fname").val();
    let last_name = $("#lname").val();
    let email = $('#signup-email').val();
    let password = $('#signup-password').val();
    let cpassword = $('#confirm-password').val();

    if(!first_name || !last_name) {
        pushNotification("error", "First or Last Name cannot be empty", 3000);
        return
    }
    if(!email || !password) {
        pushNotification("error", "Email or password cannot be empty", 3000);
        return
    }
    if(password !== cpassword) {
        pushNotification("error", "Passwords do not match!", 3000);
        return
    }
    const formData = {email, password, first_name, last_name}
    showLoader("Creating Account...")

    try {
        let data = await API.register(formData);
        //console.log(data);
        if (data.error) {
            pushNotification("error", data.error, 5000)
        }
        else {
            pushNotification("success", data.message, 5000);
            $('#signup-form')[0].reset()
            switchTab(0)
        }
        hideLoader()
    }
    catch(err) {
        pushNotification("error", err, 3000)
        hideLoader()
    }
}


$('#login-form').submit(function(e) {
    e.preventDefault();
    authenticate();
})

$('#signup-form').submit(function(e) {
    e.preventDefault();
    register();
})



