import * as API from "../module/api.js";


let query = getQueryParams();


async function getAccounts() {
    showLoader("Loading data...")
    $(".acc_id").empty()
    try {
      let data = await API.getAccounts()
      //console.log(data)
      //console.log(JSON.stringify(data))
      if(data.error) {
        pushNotification("error", data.error, 5000)
      }
      else {
        for(let i in data) {
            let temp = `
                <option value="${data[i].account_id}">${data[i].name}</option>`;
            $("#acc_id").append(temp)
        }
        $("#acc_id").val(query.account_id)
      }
    }
    catch(err) {
      pushNotification("error", err, 5000)
    }
    finally {
      hideLoader()
    }
    
  }

async function getMails() {
  let id = query.account_id
  let status = $("#status-filter").val()
  let page = $("#emp_page").val()
  let per_page = 20

  let params = {status, page, per_page}

  $(".mess-list").empty();
  try {
    let data = await API.getMails(id, params)
    //console.log(JSON.stringify(data))
    if(data.error) {
      pushNotification("error", data.error, 5000)
    }
    else {
      let d = data.data;
      let pages = data.pages
      let count = data.total_items;
      let current_page = data.page;
      //$(".total_count").html(digify(count))
      //$('.emp-no').html(data['total_items'])
      $('.page_nos').empty();
      if(data.has_prev) {
        $('.page_nos').append(`<a href="#" class="page_no" data-id="${parseInt(current_page) - 1}"><i class="fa fa-angle-left"></i></a>`)
      }
      $('.page_nos').append(`<a href="#" class="page_no active" data-id="${current_page}">${current_page}</a>`)
      if(data.has_next) {
        $('.page_nos').append(`<a href="#" class="page_no" data-id="${parseInt(current_page) + 1}"><i class="fa fa-angle-right"></i></a>`)
      }
      
      $('.page_no').click(function(e) {
        e.preventDefault();
        let page = $(this).data('id');
        $('#emp_page').val(page);
        getMails();
      })

      let stat_icons = {
        queued: "fa-clock-o",
        running: "fa-repeat",
        failed: "fa-times text-red-600",
        completed: "fa-check text-green-600"
      }

      let stat_bg = {
        queued: "fa-clock-o",
        running: "fa-repeat",
        failed: "bg-red-300",
        completed: "fa-check-circle"
      }

      let stat_class = {
        running: "info",
        completed: "success",
        failed: "error",
        queued: "warning"
      }

      if(d.length > 0) {
        for(let i in d) {
          let temp = `
          <tr class="trans-row" data-id="${d[i].id}">
                <td>
                  <div class="project-title-cell">
                    <div class="project-icon ${stat_bg[d[i].status]}">
                      <span class="fa ${stat_icons[d[i].status]}"></span>
                    </div>
                    <div class="project-info">
                      <div class="project-title-text">${d[i].subject}&nbsp;&nbsp;<i class="fa fa-circle text-sm text-white"></i>&nbsp;&nbsp;${d[i].mode.toUpperCase()}</div>
                      <div class="project-meta-text">${d[i].message_id}</div>
                    </div>
                  </div>
                </td>
                <td class="w-center"><span class="status-badge ${stat_class[d[i].status]}">${d[i].status}</span></td>
                <td>${datify(d[i].created_at)}</td>
                <td>${datify(d[i].updated_at)}</td>
              </tr>`;
          $(".mess-list").append(temp);
        }

        $(".trans-row").on('click', function() {
          let ref = $(this).data('id')
          getMail(ref)
        })
      }
      else {
        let temp = `
        <tr>
          <td colspan="4"><i>No mails found.</i></td>
        </tr>`;
        $(".mess-list").append(temp);
      }
    }
  }
  catch(err) {pushNotification("error", `Error occurred: ${err}`, 3000)}
  finally {hideLoader()}
  
}

async function setup() {
    if(query.account_id) {
      await getAccounts()
      await getMails()
    }
    else {
      pushNotification("error", "No email account selected", 5000)
    }
  }
  
setup()

async function getMail(ref) {
  showLoader("Fetching details...")
  try {
    let data = await API.getMail(ref)
    //console.log(JSON.stringify(data))
    if(data.error) {
      pushNotification("error", data.error, 5000)
    }
    else {
      let stat_icons = {
        queued: "fa-clock-o",
        running: "fa-repeat",
        failed: "fa-times text-red-600",
        completed: "fa-check text-green-600"
      }

      let stat_bg = {
        queued: "fa-clock-o",
        running: "fa-repeat",
        failed: "bg-red-300",
        completed: "fa-check-circle"
      }

      let stat_class = {
        running: "info",
        completed: "success",
        failed: "error",
        queued: "warning"
      }

      $(".sp-stat").html(`<span class="status-badge ${stat_class[data.status]} text-center text-2xl"><i class="fa ${stat_icons[data.status]}"></i> ${data.status}</span>`)
      $("#sp-id").html(data.message_id)
      $("#sp-sub").html(data.subject)
      $("#sp-rec").html(data.recipients.join(', '))
      $("#sp-from").html(data.account.smtp_username)
      $("#sp-acc").html(data.account.name)
      $("#sp-mode").html(data.mode.toUpperCase())
      $("#sp-ip").html(data.ip_address?.toStrig() || 'N/A')
      $("#sp-call").html(data.callback_url || 'N/A')
      $("#sp-created").html(datify(data.created_at, true))
      $("#sp-updated").html(datify(data.cupdated_at, true))
      $("#sp-web").html(data.callback_sent ? `
        <span class="status-badge success text-center text-sm">Yes</span>` : `
        <span class="status-badge error text-center text-sm">No</span>`)
      $(".mail-con").addClass("active")
    }
  }
  catch(err) {pushNotification("error", `Error occurred: ${err}`, 3000)}
  finally {hideLoader()}
  
}

$("#acc_id").on('change', function() {
    let val = $(this).val();
    location.href = `/mails?account_id=${val}`
})

$("#status-filter").on('change', () => {
  $("#emp_page").val(1)
  getMails()
})


$(".logout-btn").click(async function(e) {
  e.preventDefault();
  await API.clearKey("access_token")
  await API.clearKey("refresh_token")
  pushNotification("success", "Logout successful", 3000)
  location.href = "/login"
})