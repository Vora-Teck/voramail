import * as API from "../module/api.js";

showLoader("Loading data...")

function initProgressChart(data) {
  let labels = Object.keys(data);
  let values = Object.values(data);
  const ctx = document.getElementById("progressChart");
  if (!ctx) return;

  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "API Usage",
          data: values,
          borderColor: "#8b5cf6",
          backgroundColor: "rgba(139, 92, 246, 0.1)",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          beginAtZero: true,
          max: Math.max(values),
          ticks: { callback: (value) => shortify(value) },
        },
      },
    },
  });
}

function initCategoryChart(data) {
  const ctx = document.getElementById("categoryChart");
  if (!ctx) return;

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Queued", "Completed", "Failed"],
      datasets: [
        {
          data: [data.queued, data.completed, data.failed],
          backgroundColor: ["#8b5cf6", "#10b981", "#ef4444"],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            padding: 20,
            usePointStyle: true,
          },
        },
      },
    },
  });
}

async function getKPI() {
  try {
    let data = await API.userKPI()
    //console.log(data)
    if(data.error) {
      pushNotification("error", data.error, 5000)
    }
    else {
      $(".tot-call").html(shortify(data.total_api_calls))

      $(".tod-call").html(`${shortify(data.daily_api_used)} / ${shortify(data.daily_api_limit)}`)
      $(".mon-used").html(`${shortify(data.monthly_api_used)} / ${shortify(data.monthly_api_limit)}`)
      
      $(".tok-text").html(`${digify(data.monthly_api_limit - data.monthly_api_used)} calls left for this month.`)

      $(".tot-age").html(`${digify(data.total_accounts)} / ${digify(data.max_accounts)}`)
      $(".act-age").html(digify(data.active_accounts))
      showProjects(data.jobs)
      initCategoryChart(data.categories)
      initProgressChart(data.token_usage)
    }
  }
  catch(err) {
    pushNotification("error", err, 5000)
  }
  finally {hideLoader()}
  
}

getKPI()


function showProjects(data) {
  let project_icons = {
    api: "fa-cloud-upload",
    platform: "fa-laptop"
  }
  let stat_class = {
    queued: "info",
    completed: "success",
    failed: "danger",
    invalid: "warning"
  }

  $(".pro-list").empty();

  if(data.length > 0) {
    for(let i in data) {
      let temp = `
      <tr>
            <td>
              <div class="project-title-cell">
                <div class="project-icon">
                  <span class="fa ${project_icons[data[i].mode]}"></span>
                </div>
                <div class="project-info">
                  <div class="project-title-text">${data[i].job_id}</div>
                  <div class="project-meta-text">${data[i].account}</div>
                </div>
              </div>
            </td>
            <td><span class="status-badge ${stat_class[data[i].status]}">${data[i].status}</span></td>
            <td>${datify(data[i].created_at)}</td>
          </tr>`;
      $(".pro-list").append(temp);
    }
  }
  else {
    let temp = `
    <tr>
      <td colspan="3"><i>No recent messages found.</i></td>
    </tr>`;
    $(".pro-list").append(temp);
  }
}

$(".logout-btn").click(async function(e) {
  e.preventDefault();
  await API.clearKey("access_token")
  await API.clearKey("refresh_token")
  pushNotification("success", "Logout successful", 3000)
  location.href = "/login"
})