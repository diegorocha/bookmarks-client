/**
 * Created by diego on 11/04/17.
 */
$(document).ready(function(){
   $('#sign-in').submit(function(e) {
       var email = $('#password').val();
       var confirm = $('#confirm_password').val();
       if (email != confirm) {
           e.preventDefault();
           $('#confirm-passoword-error').show();
        }
   });

   $('#password').on('input',function(){
        $('#confirm-passoword-error').hide();
    });

   $('#confirm_password').on('input',function(){
        $('#confirm-passoword-error').hide();
    });
});