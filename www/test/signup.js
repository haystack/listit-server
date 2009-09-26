
function signUpMode() {
   jQuery("#regular_login").slideUp();
   jQuery("#signup").slideDown();
   jQuery(".signup_welcome").slideDown();
}

function isSignupMode() { return jQuery("#signup").is(":visible"); }
function getErrorDiv() { if (isSignupMode()) return jQuery("#signupMessage"); return jQuery("#loginMessage"); }

var spinnerController = {
    spin:function(text) {
	var spinner = jQuery("#login_spinner");
	this.setText((text === undefined) ? "please wait" : text);
	if (!spinner.is(":visible")) { spinner.show(); }
    },
    hide:function() {
	var spinner = jQuery("#login_spinner");
	spinner.hide();
    },
    setText:function(text) {
	var spinner = jQuery("#login_spinner");
	spinner.children(".text")[0].innerHTML = text;
    },
    hideOnlySpinner:function() {
	jQuery("#login_spinner").children("img").fadeOut();
    }
};

var formEnabler = {
    entries : ["passwd","email","pass1","pass2","participate","firstname","lastname","submit", "loginButton", "signupButton"],
    disableForm: function() {				  
	jQuery.map(this.entries,function(control) {
		jQuery("#"+control).attr("disabled",true);		
	    })
    },
    enableForm: function() {	
		jQuery.map(this.entries,function(control) {
			jQuery("#"+control).attr("disabled",false);
			});
		if (zenCore.browserInfo.browser !== 'IE') {
			document.getElementById('email').focus();
		}
    }
};

var errorMessageOutputter =   {
    error: function(errmsg) {
	var ed = getErrorDiv();
	ed[0].innerHTML=errmsg;
	if (!ed.is(":visible")) {
	    ed.fadeIn();
	}
    },
    reset: function() {
	var ed = getErrorDiv();
	ed[0].innerHTML="";
	if (ed.is(":visible")) {
	    ed.fadeOut();
	}
    }
};

var validate_email_address = function(emailval, output_component) {
	/** PLUMTIL-BREAKS-IE
    if (!plumutil.isValidEmail(emailval)) {
	if (output_component) {
	    output_component[0].innerHTML = "Please type an email address";
	    output_component.slideDown();	    
	}
	return false;
    }
    if (output_component) {
	output_component.innerHTML = "";
	output_component.slideUp();
    }
	**/
    return true;
}

var signup_validate_passwords = function(output_component) {
    var p1 = jQuery("#pass1").val();
    var p2 = jQuery("#pass2").val();
	/**
    p1 = plumutil.trim(p1);
    p2 = plumutil.trim(p2);  zenUtil.trim !
	**/
    if (p1.length > 3) {
	if (p1 == p2) {
	    if (output_component) {
		output_component[0].innerHTML = "Passwords match";
		output_component.slideUp();
	    }
	    return true;
	} else {
	    if (output_component) {
		output_component[0].innerHTML = "Your passwords don't seem to match. Try re-typing?";
		output_component.slideDown();
	    }
	    return false;
	}
    }
    if (output_component) {
	output_component[0].innerHTML = "Passwords must have at least 3 characters";
	output_component.slideDown();
    }	
    return false;
};

var signup_validate_enable_submit = function() {
    var submit = jQuery("#submit");  // (jQuery("#email").val()) && (!jQuery("#participate")[0].checked || (jQuery("#consent")[0].checked && plumutil.trim(jQuery("#firstname").val()).length > 0 && plumutil.trim(jQuery("#lastname").val()).length > 0)))
    if ( signup_validate_passwords() &&
	 validate_email_address(jQuery("#email").val()) &&
	 (!jQuery("#participate")[0].checked || (jQuery("#consent")[0].checked && (jQuery("#firstname").val().length > 0) && jQuery("#lastname").val().length > 0))) {	
	submit.attr("disabled",false);
	return true;
    }
    submit.attr("disabled",true);
    return false;
}


var signup_submit = function() {
    // 
    //var email = plumutil.trim(jQuery("#email").val());
	var email = jQuery("#email").val();
    var p1 = jQuery("#pass1").val();
    debug(p1);
    var couhes  = jQuery("#consent")[0].checked && jQuery("#participate")[0].checked;
    var firstname = jQuery("#firstname").val();
    var lastname = jQuery("#lastname").val();
/**
    if (!plumutil.isValidEmail(email)) {
	errorMessageOutputter.error("Invalid email address " + email);
	return;
    }    
	**/
    if (p1.length <= 3) {
	errorMessageOutputter.error("Password too short");
	return;
    }
    
    spinnerController.spin("Submitting a request for a new account for " + email);
    formEnabler.disableForm();

    debug(email + " " + p1 + " " + couhes + " " + firstname + " " + lastname);
    
    return jQuery.ajax({ type:"POST",
			 url: zenCore.baseURL + "createuser/",
			 data:({ username: email, password: p1, couhes:couhes, firstname: firstname, lastname: lastname }),
			 success: function(data,success) {
			     //success means that there exists already such an email adddr
			     spinnerController.hideOnlySpinner();
			     spinnerController.setText("Your account has been created. <p> Please refresh the page to log in.");
			 },
			 cache:false,
			 error: function(data,status) {
			     formEnabler.enableForm();
			     spinnerController.hide();
			     if (data.responseText == "User exists") {
				 errorMessageOutputter.error("I'm sorry, we already have a user with that e-mail. <br> Do you sign up already?");				 
			     } else {
				 errorMessageOutputter.error("I'm sorry, "  + data.responseText);
			     }
			     
			 }
		       });
};
