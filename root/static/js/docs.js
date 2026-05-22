function switchCode(lang) {
    ['js','py','php'].forEach(l => {
      document.getElementById(`code-${l}`).style.display = l === lang ? 'block' : 'none';
    });
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');
  }
document.addEventListener('DOMContentLoaded', () => {
    hljs.highlightAll();
})

async function showView(view) {
    $(".content").addClass('w-hide');
    view.removeClass('w-hide')
}

  $(".scrollBtn").click(async function(e) {
    e.preventDefault();
    let target = $(this).data('name')
    let page = $(this).data('id');
    let view = $(`#${page}`)
    await showView(view)
    view.animate({
      scrollTop: $(`#${target}`).offset().top + 150
    }, 800)
  })


  var dropdown = document.querySelectorAll(".dropdown-btn");
  var i;

for (i = 0; i < dropdown.length; i++) {
  dropdown[i].addEventListener("click", function(e) {
    e.preventDefault()
    //this.classList.toggle("active");
    var dropdownContent = this.nextElementSibling;
    dropdownContent.classList.toggle('close')
  });
}