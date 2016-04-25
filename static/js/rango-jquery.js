$(document).ready(function() {

    // JQuery code to be added in here.

    $("#about-btn").click( function(event) {
        msgstr = $("#msg").html()
        msgstr = msgstr + "!"
        $("#msg").html(msgstr)
     });

    $("#about-btn").addClass('btn btn-primary'); 

    $('.rango-add').click( function(){
        var catid = $(this).attr("data-catid");
        var title = $(this).attr("data-title");
        var url = $(this).attr("data-url");
        var me = $(this);
        $.get('/rango/auto_add_page', {category_id: catid, url: url, title: title}, function(data){
            $('#pages').html(data);
            me.hide();
        });
    });

    $(".ouch").click( function(event) {
           alert("You clicked me! ouch!");
    });

    // $("p").hover( function() {
    //         $(this).css('color', 'red');
    //     },
    //     function() {
    //             $(this).css('color', 'black');
    // });
});