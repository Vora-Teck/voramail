async function make_request() {
    console.log("hi")
    let url = $("#sand_url").val();
    let method = $("#sand_method").val();
    let api_key = $("#sand_api").val();
    let secret = $("#sand_secret").val();

    let headers = {
        'Accept': 'application/json',
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
        "X-SECRET-KEY": secret
    }

    $("#sand_request").val('')
    $("#sand_response").val('')

    var formData = {}

    try {
        $(".e-breakdown-key").each(function() {
            var value = $(this).val();
            if(value.trim() !== "") {
                let typ = $(this).siblings(".e-breakdown-type").val();
                if(typ == "") {
                    pushNotification("warning", "Invalid value. Kindly select a value type", 5000);
                    return;
                }
                else if(typ == "json") {
                    formData[value] = JSON.parse($(this).siblings(".breakdown-value").children(".e-breakdown-value").val());
                }
                else {
                    formData[value] = $(this).siblings(".breakdown-value").children(".e-breakdown-value").val();
                }
            }
        })
    }
    catch(e) {
        $('.sand_response').html(e);
        return
    }

    let options = {
        method: method,
        headers: headers
    }
    let opts = {
        method: method,
        headers: headers
    }
    if(method !== "GET") {
        options.body = JSON.stringify(formData)
        opts.body = formData
    }
    

    let request_text = `
    const url = "${url}";

    const options =  ${JSON.stringify(opts, null, 4)};

    let response = await fetch(url, options);
    let data = await response.json();

    console.log(data)
    `;
    $("#sand_request").val(request_text)

    showLoader("Making request...")
    try {
        let response = await fetch(url, options)
        let data = await response.json()
        let parsed = JSON.stringify(data, null, 4)
        $("#sand_response").val(parsed)
    }
    catch(err) {
        $("#sand_response").val(err)
    }
    finally {hideLoader()}
}

function updateValueField(elem) {
    var typ = elem.val();
    let con = elem.siblings(".breakdown-value");
    con.empty();
    var temp = ``;
    switch(typ) {
        case "":
            temp = ``;
            break;
        case "text":
            temp = `<input type="text" class="e-breakdown-value" placeholder="enter value">`;
            break;
        case "number":
            temp = `<input type="number" class="e-breakdown-value" placeholder="enter value">`;
            break;
        case "email":
            temp = `<input type="email" class="e-breakdown-value" placeholder="enter value">`;
            break;
        case "url":
            temp = `<input type="url" class="e-breakdown-value" placeholder="enter value">`;
            break;
        case "password":
            temp = `<input type="password" class="e-breakdown-value" placeholder="enter value">`;
            break;
        case "textarea":
            temp = `<textarea rows="5" class="e-breakdown-value" placeholder="enter value"></textarea>`;
            break;
        case "date":
            temp = `<input type="date" class="e-breakdown-value">`;
            break;
        case "json":
            temp = `<textarea rows="5" class="e-breakdown-value" placeholder="enter JSON data (array, objects)"></textarea>`;
            break;
        default:
            temp = ``;
            break;
    }
    con.html(temp);
}

$('#add-breakdown-btn').click(function(e) {
        e.preventDefault();
        var temp = `
        <div class="input-con w-flex w-flex-start mb-2 w-align-center" style="gap:15px">
                      <input type="text" class="e-breakdown-key" style="max-width:200px;" placeholder="key e.g account_id">
                      <div>:</div>
                      <select class="e-breakdown-type" style="max-width:200px;">
                        <option value="" selected>Select Value Type</option>
                        <option value="text">Text</option>
                        <option value="number">Number</option>
                        <option value="email">Email</option>
                        <option value="url">URL</option>
                        <option value="password">Password</option>
                        <option value="textarea">Textarea</option>
                        <option value="json">JSON Data</option>
                      </select>
                      <div>:</div>
                      <div class="breakdown-value" style="max-width:350px;">
                        
                      </div>
                      <div class="text-red-300 h3 rem-breakdown-btn">X</div>
                    </div>`;
        $(".breakdown-con").append(temp)
        $(".rem-breakdown-btn").click(function() {
          $(this).parent(".w-flex").remove();
        })
        $(".e-breakdown-type").on('change', function() {
        updateValueField($(this))
      })
});



$("#make-req-btn").on('click', make_request)