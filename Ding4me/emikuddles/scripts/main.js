var currentIndex = -1;
var limit = false;
var offset = $("#sidebar-container").offset();

$( document ).ready(function() {
    getOutput();
});


$("#show-nav").click(function () {
    $('.nav').toggle();
});

function createElementsFromJSON(json, parent) {
    for (var i in json) {
        var object = json[i];

        var container = document.getElementById('');

            var post = "<div class='post shadow'><h1 class='post-title'>"
                    + object["title"]
                    + "</h1>"
                    + object["content"]
                    + "</div>";

        parent.append(post);
    }
}

function getOutput() {
    currentIndex++;
    $.ajax({
        url: 'scripts/get.php?page=' + currentIndex,
        complete: function (response) {
            if (response.responseText !== '0 results') {

                var json = JSON.parse(response.responseText);
                createElementsFromJSON(json, $("#post-container"));
                checkShouldLoad()
            } else {
                limit = true;
            }
        },
        error: function () {
            $('#output').html('Bummer: there was an error!');
        }
    });
    return false;
}

function checkShouldLoad() {
    if($(window).scrollTop() + $(window).height() > $(document).height() - 100 && !limit) {
        getOutput();
    }
}

$(window).scroll(function() {
    checkShouldLoad();
});

// extension:
$.fn.scrollEnd = function(callback, timeout) {
    $(this).scroll(function(){
        var $this = $(this);
        if ($this.data('scrollTimeout')) {
            clearTimeout($this.data('scrollTimeout'));
        }
        $this.data('scrollTimeout', setTimeout(callback,timeout));
    });
};

$(window).scrollEnd(function(){
    var offset = $('#sidebar-container').parent().offset().top;
    var top = Math.max($(document).scrollTop()-offset, 0);
    $("#sidebar-container").css({top:top});
}, 1000);

