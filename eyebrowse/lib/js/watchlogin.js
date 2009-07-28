jQuery(document).ready(function(){
    var name = $("#id_username"), password1 = $("#id_password1"), allFields = $([]).add(name).add(password1), tips = $("#validateTips");
    
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
        bValid = bValid && checkLength(password1, "password", 5, 16);                
        bValid = bValid && checkRegexp(name, /^[a-z]([0-9a-z_])+$/i, "Username may consist of a-z, 0-9, underscores, begin with a letter.");
        bValid = bValid && checkRegexp(password1, /^([0-9a-zA-Z])+$/, "Password field only allow : a-z 0-9");

        if (bValid) {
            // send to server
	  jQuery("#messageSent").show("slow");
	  $("form:first").submit();
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
