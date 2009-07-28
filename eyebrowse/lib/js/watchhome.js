jQuery(document).ready(function(){
    var name = $("#id_username"), email = $("#id_email"), password1 = $("#id_password1"), password2 = $("#id_password2"), allFields = $([]).add(name).add(email).add(password1).add(password2), tips = $("#validateTips");

    function updateTips(t){
        tips.text(t).effect("highlight", {}, 1500);

    }

    function checkLength(o, n, min, max){
        if (o.val().length > max || o.val().length < min) {
            o.addClass('ui-state-error');
            updateTips("Length of " + n + " must be between " + min + " and " + max + ".");
            return false;
        }
        else {
            return true;
        }
    }

    function checkRegexp(o, regexp, n){
        if (!(regexp.test(o.val()))) {
            o.addClass('ui-state-error');
            updateTips(n);
            return false;
        }
        else {
            return true;
        }
    }

    jQuery("#registerSubmit").click(function(){
        $(".error").hide();
        var bValid = true;
        allFields.removeClass('ui-state-error');

        bValid = bValid && checkLength(name, "name", 3, 16);
        bValid = bValid && checkLength(email, "email", 6, 80);
        bValid = bValid && checkLength(password1, "password", 5, 16);
        bValid = bValid && checkLength(password2, "password", 5, 16);

        bValid = bValid && checkRegexp(name, /^[a-z]([0-9a-z_])+$/i, "Username may consist of a-z, 0-9, underscores, begin with a letter.");
        // From jquery.validate.js (by joern), contributed by Scott Gonzalez: http://projects.scottsplayground.com/email_address_validation/
        bValid = bValid && checkRegexp(email, /^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?$/i, "eg. ui@jquery.com");
        bValid = bValid && checkRegexp(password1, /^([0-9a-zA-Z])+$/, "Password field only allow : a-z 0-9");
        bValid = bValid && checkRegexp(password2, /^([0-9a-zA-Z])+$/, "Password field only allow : a-z 0-9");

        if (bValid) {
	    $("form:first").submit();
            jQuery("#messageSent").show("slow");
        }
        return false;
    });
    jQuery("#signUpLink").click(function(){
        if (jQuery("#signUpForm").is(":hidden")) {
            jQuery("#signUpForm").slideDown("slow");
        }
        else {
            jQuery("#signUpForm").slideUp("slow");
        }
    });
});