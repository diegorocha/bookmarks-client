/**
 * Created by diego on 09/04/17.
 */
$(document).ready(function(){

    $('.bookmark-form').hide();

    $('.btn-edit').click(function(){
        var id = $(this).attr('data-id');
        $('#bookmark-content-' + id).hide();
        $('#bookmark-form-' + id).show();
    });

    $('.btn-save').click(function(e){
        var id = $(this).attr('data-id');
        $('form#bookmark-' + id + ' input#__operation').val("__update__");
        $('form#bookmark-' + id + ' input#__id').val(id);
    });

    $('.btn-cancel').click(function(e){
        e.preventDefault();
        var id = $(this).attr('data-id');
        $('#bookmark-content-' + id).show();
        $('#bookmark-form-' + id).hide();
    });

    $('.btn-remove').click(function(){
        var id = $(this).attr('data-id');
        $('form#bookmark-' + id + ' input#__operation').val("__remove__");
        $('form#bookmark-' + id + ' input#__id').val(id);
        $('form#bookmark-' + id).submit();
    });
});