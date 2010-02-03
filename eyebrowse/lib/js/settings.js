function swaptab(domobj){
    var text = jQuery.trim(jQuery(domobj).text());
    jQuery('#nav a').removeClass('bold');	         
    jQuery(domobj).addClass('bold');
    if (text == 'Share Websites'){
	jQuery('#profleeditform, #newtab').hide();
	jQuery('#add_sites, #faq').show();	      
    } else if (text == 'Edit Your Profile'){
	jQuery('#add_sites, #faq, #newtab').hide();
	jQuery('#profleeditform').show();	      
    } else if (text == 'Firefox Plugin'){
	jQuery('#add_sites, #faq, #profleeditform').hide().removeClass('bold');	      
	jQuery('#add_sites, #faq, #profleeditform').hide().removeClass('bold');	      
	jQuery('#newtab').show();
    }
};

function addGroups(){
    var groups = [];
    
    jQuery('#groups :checkbox:checked').each(function(check){ groups.push(this.name); });
    if (jQuery('#groupstextinput').val()) {groups.push(jQuery('#groupstextinput').val()); };

    jQuery.post("/add_groups/", {groups: groups}, 
		function(data){
		    if (data.code == 200) {
			jQuery('#groups :checkbox:checked').each(function(check){  this.checked = !this.checked; });
			jQuery('#groupstextinput').val("");
			jQuery('#id_tags').val(data.results);
		    }
		    else {
		    }
		}, "json");
}

function initMenu(){
    jQuery('#popularsites ul').hide();
    jQuery('#popularsites li a').click(
	function() {
	    jQuery(this).next().slideToggle('normal');
	}
    );
    var html = "";
    var typesArray = ["news","blogs","media","shopping","social","reference"];
    for (var i = 0; i < typesArray.length; i++){			
	html = "<a href=\"javascript:addAllPrivacyURLS(\'" + pageList[typesArray[i]] + "\');\" style=\"font-weight:bold;\"> add all</a>";
	for (var j = 0; j < pageList[typesArray[i]].length; j++){
	    html += "<li>";
	    html += "<a href=\"javascript:addPrivacyURL(\'" + pageList[typesArray[i]][j] + "\');\">" + pageList[typesArray[i]][j] + "</a>";
	    html += "</li>";			
	}
	jQuery("#" + typesArray[i]).html(html);
    }
};
function addPrivacyURL(url){
    var urlEncoded = encodeURIComponent(url);
    jQuery("<li>" + url + "<a href=\"/delete_privacy_url/?input=" + url + "\"><img src=\"/lib/img/cancel_16.png\"/></a>" + "</li>").prependTo('#urladdul');
    jQuery.get("/add_privacy_url/", {input:url}); 
};

function addAllPrivacyURLS(urls){
    var urlsArray = urls.split(",");
    for (var i = 0; i < urlsArray.length; i++){
	jQuery("<li>" + urlsArray[i] + "<a href=\"/delete_privacy_url/?input=" + urlsArray[i] + "\"><img src=\"/lib/img/cancel_16.png\"/></a>" + "</li>").prependTo('#urladdul');		
    }
    jQuery.get("/add_privacy_url/", {input:urls}); 
};


// this code is so bad sorry
jQuery(document).ready(
    function(){
	jQuery('#header').width(window.innerWidth - 15);
	initMenu();
	// no params :(
	jQuery.get("/get_privacy_urls/", {}, 
		   function(data){
		       if (data.code == 200) {
			   var html = "";
			   for (var i = 0; i < data.results.length; i++) {
			       html += "<li>";
			       html += data.results[i];
			       html += "<a href=\"/delete_privacy_url/?input=" + data.results[i] + "\"><img src=\"/lib/img/cancel_16.png\"/></a>";
			       html += "</li>";
			   }
			   jQuery("#urladdul").html(html);
		       }
		       else {
		       }
		   }, "json");

	jQuery.get("/get_most_shared_hosts/25/", {}, 
		   function(data){
		       if (data.code == 200) {
			   var html = "";
			   for (var i = 0; i < data.results.length; i++) {
			       html += "<li>";
			       html += "<a href=\"javascript:addPrivacyURL(\'" + data.results[i][0] + "\');\">" + data.results[i][0] + "</a>";
			       html += "</li>";			
			   }
			   jQuery("#top_logged").html(html);
		       }
		       else {
		       }
		   }, "json");

	self.addURL = function(){
	    var input = jQuery("#urladdtextinput").val();
	    jQuery.ajax({
			    type:"GET",
			    url:"../add_privacy_url/",
			    dataType:"json",
			    data:{input:input},
			    success:function(data){
				if (data.host && data.host.length > 0) {
				    jQuery("<li>" + data.host + "<a href=\"/delete_privacy_url/?input=" + data.host + "\"><img src=\"/lib/img/cancel_16.png\"/></a>" + "</li>").prependTo('#urladdul');
				}
			    },
			    error:function() {}
			});
	};
	jQuery('#groupstextinput').val("");
    });
