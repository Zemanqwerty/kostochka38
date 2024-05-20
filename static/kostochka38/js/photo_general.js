function view_delete_form(id){
                $('#delete_form_'+id).css("display",'block');
            }
            function close_form_delete(id){
                $('#delete_form_'+id).css("display",'none');
            }
            function view_form(id){
                $('#title_form_'+id).css("display",'block');
                $('#photo_title_'+id).focus()
            }
            function close_form(id){
                $('#title_form_'+id).css("display",'none');
            }
            function is_cover(id){
                $('#photo_id').val(id);
                $('#block_photo').html("<img src='/image/loader.gif'> сохраняется");
                $('#cover_form').submit();
            }
            $(document).ready(function(){ 
                $(".photo_element").hover(
                    function(){ 
                        $('.meta', this).css("display",'block');
                    },
                    function(){
                        $('.meta', this).css("display",'none');
                    }
                ); 
                $(".photo_element_cover").hover(
                    function(){ 
                        $('.meta', this).css("display",'block');
                    },
                    function(){
                        $('.meta', this).css("display",'none');
                    }
                ); 
            	$(function() {
            		$( "#sortable" ).sortable({
                        revert : "true",
                        opacity: 0.6,
                    });
            		$( "#sortable" ).disableSelection();
            	});
            }); 
            function save_photo_title(id){
                title = $('#photo_title_'+id).val();
                close_form(id);
                photo_html = $('#photo_element_'+id).html();
                $('#photo_element_'+id).html("<div id='save_layer'><img src='/image/loader.gif'> сохраняется</div>"+photo_html);
                $('#photo_title_'+id).val(title);
                url="/photo/save_title/";
                
                var mycontent='photo_id=' + id + '&title=' + title;
                $.post(url, mycontent, function(data){
                    $('#save_layer','#photo_element_'+id).html("<p>Сохранено успешно!</p>");
                    $('#save_layer','#photo_element_'+id).animate({'background-color': '#99ee99'},50); 
                    $('#save_layer','#photo_element_'+id).animate({'background-color': '#fffff'},2500);
                    $('#save_layer','#photo_element_'+id).hide('highlight');
                }, 'json');  
            }            
            function save_album_title(){
                title = $('#album_title').val();
                album_html = $('#album_element').html();
                $('#album_element').html("<div id='save_layer_album'><img src='/image/loader.gif'> сохраняется</div>"+album_html);
                $('#album_title').val(title);
                url="/photo/save_album_title/";
                album_id = $('#gallery_id').val();
                var mycontent='title=' + title+ '&album_id=' + album_id;
                $.post(url, mycontent, function(data){}, 'json'); 
                
                url_sortable = "/photo/save_sortable/";
                
                $('.number_box').html('..');
                
                $('.number').each(function(index) {
                    photo_id = $('.photo_sortable',this).val();
                    var number_el = $(this);
                    var index_el = index+1;
                    //$('#number',this).html(i);
                    //$(this).animate({'background-color': '#99ee99'},50).animate({'background-color': '#eeeeee'},1500); 
                    var mycontent='photo_id=' + photo_id+ '&number=' + index_el;
                    $.post(url_sortable, mycontent, function(data){
                        var el = number_el;
                        var number = index_el;
                        el.animate({'background-color': '#99ee99'},50).animate({'background-color': '#eeeeee'},1500); 
                        $('#number_'+data).html(number);
                    }, 'json');                     
                    
                }); 
                
                $('#save_layer_album','#album_element').html("<p>Сохранено успешно!</p>");
                $('#save_layer_album','#album_element').animate({'background-color': '#99ee99'},50); 
                $('#save_layer_album','#album_element').animate({'background-color': '#fffff'},2500);
                $('#save_layer_album','#album_element').hide('highlight');
            }
            function delete_photo(id){
                $('#photo_element_'+id).hide('explode');
                url="/photo/delete_photo/";
                
                var mycontent='photo_id=' + id;
                $.post(url, mycontent, function(data){}, 'json');  
            }