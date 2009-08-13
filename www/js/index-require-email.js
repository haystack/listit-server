
// for the background
    var resetbackground = function() {
	$('#back').attr('width',$(window).width());
	//$('#back').attr('height',$(window).height());      
    }
$(window).resize(resetbackground);
$(document).resize(resetbackground);
$(document).ready(resetbackground);

var init_accordion = function() {
    $(".feature-list").accordion({
	header: "div.feature-title",
	autoheight:false,
	alwaysOpen: false,
        active:	""
    });
};

$(document).ready( function() {
    // checks navigator version and stuff.    
    try {
        var browser=navigator.appName;
	      var b_version=navigator.appVersion;
	      var version=parseFloat(b_version);
	      if (browser=="Netscape" && version >= 5 && 
            navigator.userAgent.match("rv:1\.9")) {
	          $("#main-content").fadeIn();
	          init_accordion();	
	          return;
	      } 
    } catch(e) { }
    $("#browser-version-problem").fadeIn();
    $("#main-content").hide();
    
    $(".feature-list").accordion({
	      header: "div.feature-title",
	      autoheight:false,
	      alwaysOpen: false,
        active:	""
    });
    // Allow users to override a faulty browser version detection
    $("#ff3-continue").click(function() {
        $("#browser-version-problem").slideUp();
        $("#main-content").slideDown();
        return false;
    });

});

var BASE_URL = "/listit/jv3";

var setmsg = function(msg) {
    if (msg && msg.length > 0) {
        $("#msg").html(msg);
	//$("#msg").fadeIn("fast");				    
    } else {
       $("#msg").html("&nbsp;");
	//$("#msg").fadeOut("fast");
    }
};
var setok = function(ok) {
    if (ok) {
	$("#submit").fadeIn("fast");
	$("#submit").show();
    } else {
	$("#submit").fadeOut("fast");
    }
};


var getEmailVal = function() { return $("#email").val(); }
var setReturningUser = function(isReturning, username) {
   if (isReturning) {
       $("#login").fadeIn("fast");
       $("#login").show();
       $("#register").fadeOut("fast");
   } else {
       $("#login").fadeOut("fast");
       $("#register").fadeIn("fast");
   }
};
var determineWhetherUserIsNewOrReturningBasedOnEmail = function(cont) {
    var emailval = getEmailVal()
    emailval = plumutil.trim(emailval);
    if (emailval.length == 0) {
	return cont(false, "Please type an e-mail address");
    }
    if (!plumutil.isValidEmail(emailval)) {
	return cont(false, "That doesn't look like a valid e-mail address.");
    } else {
	return jQuery.ajax({ type:"GET",
			     url: BASE_URL + "/userexists?email="+encodeURIComponent(emailval),
			     success: function(data,success, x) {
				 //success means that there exists already such an email adddr
				 setReturningUser(true,emailval);
				 cont(false,"I remember you. Please supply your password");
			     },
			     cache:false,
			     error: function(req,status) {
				 if (req.status == 404){
				     setReturningUser(false);
				     cont(true);
				 } else {
				     cont(false,"Uh oh the server seems to be down.");
				 }
			     }});
    }
};
var doLogin = function(username, password, cont) {
    jQuery.ajax( {type:"GET",
       		  url:BASE_URL + "/notes/",
		  beforeSend:function(username,password) {
		      return function(req) { 
			  var header = plumutil.make_base_auth(username,password);
			  //req.channel.loadFlags |= Components.interfaces.nsIRequest.LOAD_BYPASS_CACHE;
			  req.setRequestHeader('Authorization','');
			  req.setRequestHeader('Authorization',header);
		      };
		  }(username,password),
		  success: function(data,success, x) {
		      cont(true);
		  },
		  cache:false,
		  error: function(req,status) {
		      if (req.status == 401){
			  cont(false,"Username or password incorrect");
		      } else {
			  cont(false,"Uh oh the server seems to be down.");			  
		      } 
		  }});
};
var validateRegistrationPass = function(cont) {
    var p1 = $("#pass1").val();
    var p2 = $("#pass2").val();
    p1 = plumutil.trim(p1);
    p2 = plumutil.trim(p2);
    if (p1.length > 3) {
	if (p1 == p2) {
	    return cont(true);
	} else {
	    return cont(false, "Your passwords don't seem to match. Try re-typing?");
	}
    }
    cont(false, "Passwords must have more than 3 characters");    
};

var sendCreateRequest = function() {
    var emailval = getEmailVal()
    var p1 = $("#pass1").val();
    var couhes  = $("#consent")[0].checked && $("#participate")[0].checked;
    var firstname ="", lastname = "";
    
    if (couhes) {
	firstname = $("#firstname").val();
	lastname = $("#lastname").val();
    }    
    setok(false);
    setmsg("Sending request...");
    var cont = function(success, info) {
	if (success) {
	    setmsg();
	    setmsg("Please check your email.<BR>I sent " + emailval + " download instructions. ");
	} else {
	    setmsg();
	    setmsg(info);
	}
    };
    return jQuery.ajax({ type:"POST",
			 url: BASE_URL + "/createuser/",
			 data:({ username: emailval, password: p1, couhes:couhes, firstname: firstname, lastname: lastname }),
			 success: function(data,success) {
			     //success means that there exists already such an email adddr
			     cont(true);
			 },
			 cache:false,
			 error: function(data,status) {
			     cont(false,data.responseText);
			 }
		       });
    
}
var validate = function() {
    var cont = function(ok, msg) {
	if (ok) {
	    setok(true);
	    setmsg("");
	} else {
	    setok(false);
	    setmsg(msg);
	}
    };
    determineWhetherUserIsNewOrReturningBasedOnEmail(function(doregister,msg) {
	if (!doregister) { cont(doregister,msg); }
	else {
	    validateRegistrationPass(function(ok,msg) {
		if (!ok) { cont(ok,msg); }
		else {
		    if ($("#participate")[0].checked) {
			if (plumutil.trim($("#firstname").val()).length > 0 && plumutil.trim($("#lastname").val()).length > 0 ){
			    $("#consent").attr("disabled",false);
			    if ($("#consent")[0].checked) {
				cont(true);
			    } else {
				cont(false,"Please consent to participate in the study, or uncheck the Paricipate in Study check mark above.");
			    }
			} else {
			    // names not blank
			    $("#consent").attr("disabled",true);
			    cont(false,"Please supply your first and last name and consent to participate in the study, or uncheck the Paricipate in Study check mark above.");
			}
		    } else {
			cont(true);
		    }
		}});
	}			    
    });
};
var ajax_requests = [];
var login_success = false;
$(document).ready(function() {
    $("#email").val("");
    setok(false);
    setmsg("");
    $("#couhes").hide();
    $("input:checked").attr("checked",false);
    $("#consent").attr("disabled",true);
    $("#email").keyup(function() {validate();   });
    $("#email").blur(function() {validate();   });
    var login_ = function() {
	ajax_requests.push(1);
	setmsg("Checking..");
        doLogin(getEmailVal(),
		$("#loginpassword").val(),
		function(isLoggedIn,msg) {
		    ajax_requests.pop();
		    if(isLoggedIn) {
			// login successful.
			setmsg("You are already registered. Thanks!");
			login_success = true;
			// enableDownload();
			$("#email").attr("disabled",true);
			$("#loginpassword").attr("disabled",true);
       			$("#submitlogin").fadeOut("fast");
			$("#submitchangepassword").fadeOut("fast");
		    } else {
			if (ajax_requests.length == 0 && !login_success) {
			    setmsg(msg);
			}
		    }
		});
    };
    $("#loginpassword").keyup(login_);
    $("#loginpassword").blur(login_);
    $("#submitchangepassword").click(function() {
	var email = getEmailVal();
	var url = BASE_URL + "/changepasswordrequest?username="+email;
	window.location = url;
    });
    $("#pass1").keyup(function() {
	validate();
    });
    $("#pass2").keyup(function() {
	validate();
    });
    $("#submit").click(function() {
	sendCreateRequest();
    });	
    $("#participate").click(function() {
        var Hfudge = 20;
 	if ($("#participate")[0].checked)  {
            $("#couhes").fadeIn();
	} else {
	    $("#couhes").fadeOut();
	}
	validate();
    });
    $("#firstname").keyup(function() {
	validate();	   
    });
    $("#lastname").keyup(function() {
	validate();	   
    });
    $("#consent").click(function() {
	validate();
	signeddate = new Date();
	if ($("#consent")[0].checked) {
	    $("#consentdate").html( "" + (new Date()) );
	    $("#consentdate").fadeIn();		
	} else {
	    $("#consentdate").fadeOut();
	}
    });
    $("#tandc").click(function() {
	$("#terms").fadeIn();
    });
    $("#showtroubleshooting").click(function() {
	$("#troubleshooting").fadeIn();
    });    
});

