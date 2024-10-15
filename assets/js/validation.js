/*

Template:  Webmin - Bootstrap 4 & Angular 5 Admin Dashboard Template
Author: potenzaglobalsolutions.com
Design and Developed by: potenzaglobalsolutions.com

NOTE: 

*/

 (function($){
  "use strict";
    $.validator.setDefaults( {
        submitHandler: function () {
          alert( "submitted!" );
        }
      });
     $.validator.setDefaults( {
      submitHandler: function () {
        alert( "submitted!" );
      }
    });

    $( document ).ready( function () {
      $( "#signupForm" ).validate( {
        rules: {
          fname: "required",
          lname: "required",
          uname: {
            required: true,
            minlength: 2
          },
          upassword: {
            required: true,
            minlength: 5
          },
          uconfirm_password: {
            required: true,
            minlength: 5,
            equalTo: "#password"
          },
          uemail: {
            required: true,
            email: true
          },
          uagree: "required"
        },
        messages: {
          fname: "لطفا نام خود را وارد کنید",
          lname: "لطفا نام خانوادگی خود را وارد کنید",
          uname: {
            required: "لطفا یک نام کاربری را وارد کنید",
            minlength: "نام کاربری شما باید حداقل 2 کاراکتر باشد"
          },
          upassword: {
            required: "لطفا رمز عبور را وارد کنید",
            minlength: "گذرواژه شما حداقل 5 کاراکتر دارد"
          },
          uconfirm_password: {
            required: "لطفا رمز عبور را وارد کنید",
            minlength: "گذرواژه شما حداقل 5 کاراکتر دارد",
            equalTo: "لطفا رمز عبور همانند بالا را وارد کنید"
          },
          uemail: "لطفا یک آدرس ایمیل معتبر وارد کنید",
          uagree: "لطفا سیاست ما را بپذیرید"
        },
        errorElement: "em",
        errorPlacement: function ( error, element ) {
          // Add the `help-block` class to the error element
          error.addClass( "help-block" );

          if ( element.prop( "type" ) === "checkbox" ) {
            error.insertAfter( element.parent( "label" ) );
          } else {
            error.insertAfter( element );
          }
        },
        highlight: function ( element, errorClass, validClass ) {
          $( element ).parents( ".col-sm-5" ).addClass( "has-error" ).removeClass( "has-success" );
        },
        unhighlight: function (element, errorClass, validClass) {
          $( element ).parents( ".col-sm-5" ).addClass( "has-success" ).removeClass( "has-error" );
        }
      } );

      $( "#signupForm1" ).validate( {
        rules: {
          firstname1: "required",
          lastname1: "required",
          username1: {
            required: true,
            minlength: 2
          },
          password1: {
            required: true,
            minlength: 5
          },
          confirm_password1: {
            required: true,
            minlength: 5,
            equalTo: "#password1"
          },
          email1: {
            required: true,
            email: true
          },
          agree1: "required"
        },
        messages: {
          firstname1: "لطفا نام خود را وارد کنید",
          lastname1: "لطفا نام خانوادگی خود را وارد کنید",
          username1: {
            required: "لطفا یک نام کاربری را وارد کنید",
            minlength: "نام کاربری شما باید حداقل 2 کاراکتر باشد"
          },
          password1: {
            required: "لطفا رمز عبور را وارد کنید",
            minlength: "گذرواژه شما حداقل 5 کاراکتر دارد"
          },
          confirm_password1: {
            required: "لطفا رمز عبور را وارد کنید",
            minlength: "گذرواژه شما حداقل 5 کاراکتر دارد",
            equalTo: "لطفا رمز عبور همانند بالا را وارد کنید"
          },
          email1: "لطفا یک آدرس ایمیل معتبر وارد کنید",
          agree1: "لطفا سیاست ما را بپذیرید"
        },
        errorElement: "em",
        errorPlacement: function ( error, element ) {
          // Add the `help-block` class to the error element
          error.addClass( "help-block" );

          // Add `has-feedback` class to the parent div.form-group
          // in order to add icons to inputs
          element.parents( ".col-sm-5" ).addClass( "has-feedback" );

          if ( element.prop( "type" ) === "checkbox" ) {
            error.insertAfter( element.parent( "label" ) );
          } else {
            error.insertAfter( element );
          }

          // Add the span element, if doesn't exists, and apply the icon classes to it.
          if ( !element.next( "span" )[ 0 ] ) {
            $( "<span class='fa fa-times form-control-feedback pr-2'></span>" ).insertAfter( element );
          }
        },
        success: function ( label, element ) {
          // Add the span element, if doesn't exists, and apply the icon classes to it.
          if ( !$( element ).next( "span" )[ 0 ] ) {
            $( "<span class='fa fa-check form-control-feedback'></span>" ).insertAfter( $( element ) );
          }
        },
        highlight: function ( element, errorClass, validClass ) {
          $( element ).parents( ".col-sm-5" ).addClass( "has-error" ).removeClass( "has-success" );
          $( element ).next( "span" ).addClass( "fa fa-times" ).removeClass( "fa fa-check" );
        },
        unhighlight: function ( element, errorClass, validClass ) {
          $( element ).parents( ".col-sm-5" ).addClass( "has-success" ).removeClass( "has-error" );
          $( element ).next( "span" ).addClass( "fa fa-check" ).removeClass( "fa fa-times" );
        }
      });
      $( "#signupForm3" ).validate( {
        rules: {
          firstname: "required",
          lastname: "required",
          username: {
            required: true,
            minlength: 2
          },
          password: {
            required: true,
            minlength: 5
          },
          confirm_password: {
            required: true,
            minlength: 5,
            equalTo: "#password"
          },
          email: {
            required: true,
            email: true
          },
          agree: "required"
        },
        messages: {
          firstname: "لطفا نام خود را وارد کنید",
          lastname: "لطفا نام خانوادگی خود را وارد کنید",
          username: {
            required: "لطفا یک نام کاربری را وارد کنید",
            minlength: "نام کاربری شما باید حداقل 2 کاراکتر باشد"
          },
          password: {
            required: "لطفا رمز عبور را وارد کنید",
            minlength: "گذرواژه شما حداقل 5 کاراکتر دارد"
          },
          confirm_password: {
            required: "لطفا رمز عبور را وارد کنید",
            minlength: "گذرواژه شما حداقل 5 کاراکتر دارد",
            equalTo: "لطفا رمز عبور همانند بالا را وارد کنید"
          },
          email: "لطفا یک آدرس ایمیل معتبر وارد کنید",
          agree: "لطفا سیاست ما را بپذیرید"
        },
        errorPlacement: function ( error, element ) {
          error.addClass( "ui red pointing label transition" );
          error.insertAfter( element.parent() );
        },
        highlight: function ( element, errorClass, validClass ) {
          $( element ).parents( ".row" ).addClass( errorClass );
        },
        unhighlight: function (element, errorClass, validClass) {
          $( element ).parents( ".row" ).removeClass( errorClass );
        }
      } );

    });

 })(jQuery);