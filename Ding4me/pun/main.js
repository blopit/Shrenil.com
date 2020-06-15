////////////////////////////////////////////////////////////////////////////////
// Ajax sync script require
// sync aditional JS scripts, makes things modular
////////////////////////////////////////////////////////////////////////////////
$(function(){
  $('#header_nav').data('size','big');
});

$(window).scroll(function(){
  if($(document).scrollTop() > 0)
{
    if($('#header_nav').data('size') == 'big')
    {
        $('#header_nav').data('size','small');
        $('#header_nav').stop().animate({
            height:'40px'
        },600);
    }
}
else
  {
    if($('#header_nav').data('size') == 'small')
      {
        $('#header_nav').data('size','big');
        $('#header_nav').stop().animate({
            height:'100px'
        },600);
      }
  }
});


var _table_ = document.createElement('table'),
    _thead_ = document.createElement('thead'),
    _tr_ = document.createElement('tr'),
    _th_ = document.createElement('th'),
    _td_ = document.createElement('td'),
    _tbody_ = document.createElement('tbody');

// Builds the HTML Table out of myList json data from Ivy restful service.
 function buildHtmlTable(arr) {
     var table = _table_.cloneNode(false),
         B =  _tbody_.cloneNode(false),
         H = _thead_.cloneNode(false),
         columns = addAllColumnHeaders(arr, H);
         table.setAttribute("id", "keywords");
         table.setAttribute("cellspacing", 0);
         table.setAttribute("cellpadding", 0);
         H.setAttribute("id", "header_nav");
         table.appendChild(H);
         table.appendChild(B);

     for (var i=0, maxi=arr.length; i < maxi; ++i) {
         var tr = _tr_.cloneNode(false);
         for (var j=0, maxj=columns.length; j < maxj ; ++j) {
             var td = _td_.cloneNode(false);
                 cellValue = arr[i][columns[j]];
             if (j === 0){
                td.style.fontWeight = "900";
                td.setAttribute("class", "lalign");
             }else if (j === 2){
                cellValue = (100*cellValue).toFixed(1)+'%';
             }else if (j === 3){
                cellValue = (cellValue).toFixed(4);
                if (cellValue == 0){
                    cellValue = "-----"
                }
             }


             td.appendChild(document.createTextNode(cellValue || ''));
             tr.appendChild(td);
         }
         B.appendChild(tr);
     }
     return table;
 }

 // Adds a header row to the table and returns the set of columns.
 // Need to do union of keys from all records as some records may not contain
 // all records
 function addAllColumnHeaders(arr, H)
 {
     var columnSet = [],
         tr = _tr_.cloneNode(false);
     for (var i=0, l=arr.length; i < l; i++) {
         for (var key in arr[i]) {
             if (arr[i].hasOwnProperty(key) && columnSet.indexOf(key)===-1) {
                 columnSet.push(key);
                 var th = _th_.cloneNode(false);
                 th.setAttribute("class", "header");
                 th.appendChild(document.createTextNode(key));
                 tr.appendChild(th);
             }
         }
     }
     H.appendChild(tr);
     return columnSet;
 }


/*document.addEventListener("scroll",function(){
   var translate = "translate(0,"+this.scrollTop+"px)";
   document.getElementById("keywords").querySelector("thead").style.transform = translate;
});*/

function getPuns() {
    var DIV = document.getElementById("wrapper");
    document.getElementById("btn").disabled = true;
    DIV.style.visibility = 'visible';
    var query = String(document.getElementById('txtJob').value);
    var am = Math.max(parseInt(document.getElementById('numJob').value),1);
    if (isNaN(am)){
        am = 30;
    }

    if (query === ""){
        document.getElementById("btn").disabled = false;
        DIV.style.visibility = 'hidden';
        return;
    }
    document.getElementById("hr").innerHTML = "loading ... " + query;
    document.getElementById("hr").style.color = '#C9C9C9';

    $.ajax({
        type: "GET",
        jsonp: "callback",
        dataType: 'jsonp',
        url: 'https://pungenerator.herokuapp.com',
        crossDomain : true,
        data: {
            q: query,
            amount: am,
            format: "json"
        },
        success: function( response ) {
            DIV.replaceChild(buildHtmlTable(response['results']),document.getElementById("keywords"));
            $("#keywords").tablesorter();
            //$("#keywords").stickyTableHeaders({fixedOffset: 0});
        }
    })
    .done(function( data ) {
        document.getElementById("btn").disabled = false;
        document.getElementById("hr").innerHTML = "Results - " + query;
        document.getElementById("hr").style.color = '#000';
    })
    .fail( function(xhr, textStatus, errorThrown) {
        alert(xhr.responseText);
        alert(textStatus);
        document.getElementById("btn").disabled = false;
        document.getElementById("hr").innerHTML = "Results - " + query;
        document.getElementById("hr").style.color = '#000';
    });
}
