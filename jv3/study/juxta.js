
log = function() {
    if (window.console !== undefined) console.log.apply(console,arguments);
};
error = function(x) {
    log(x);
    alert(x);
};
keys = function (o) {  var a = []; for (var k in o) a.push(k); return a; };


jQuery(document).ready(
    function() {
	// do something
	jQuery(".shownotes").click(function(e) {
				       var notes = jQuery(this).parent().find(".notes");
				       notes.is(":visible") ?  jQuery(this).parent().find(".notes").slideUp() : jQuery(this).parent().find(".notes").slideDown();
				   });
	
	jQuery(".note_current").live("click", 
				     function(e) {
					 oldes = jQuery("tr[jid="+jQuery(this).attr('jid')+"]").filter("[owner="+jQuery(this).attr('owner')+"]").not(".note_current");
					 if (oldes.is(":visible")) {  oldes.fadeOut(); } else { oldes.fadeIn(); }
				     });

	jQuery(".comments").live("click",
				 function(evt) {
				     var comments = jQuery(this).parent().find(".commentfield");
				     comments.is(":visible") ?  jQuery(this).parent().find(".commentfield").slideUp() : jQuery(this).parent().find(".commentfield").slideDown();				     				 });

	var postcomment = function(jQC) {
		var username = jQC.parent().attr("owner");
		var comment = jQC.val();	    
		jQuery.ajax({url:"http://astroboy.csail.mit.edu:8000/listit/jv3/tfig_post_comment/",
			     data:{ uid:username, comment:comment },
			     dataType:"jsonp",
			     success:function(x,foo,status) {				 
				 log('comment post complete',x);
			     },
			     error:function(x) {
				 errorlog(x);
			     }});
	};	
	jQuery(".commentfield").live("blur", function() { postcomment(jQuery(this));   });

	// now update all the dudes

	jQuery.ajax({url:"http://astroboy.csail.mit.edu:8000/listit/jv3/tfig_get_comments",
		     dataType:"jsonp",
		     success:function(commentsall) {
			 log("commentsall", commentsall);
			 keys(commentsall).map(function(user) {
						   log("setting ",user,commentsall[user].slice(0,10), jQuery("div[owner="+user+"]").find(".commentfield").val(commentsall[user]).length);
						   jQuery("div[owner="+user+"]").find(".commentfield").val(commentsall[user]);
					       });
		     },
		     error:function(x) {
			 errorlog(x);
		     }});	
    });