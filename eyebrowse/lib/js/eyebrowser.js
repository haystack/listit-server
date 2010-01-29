var Eyebrowser = {
    initialize: function(mainPanelDiv) {
	this.lastPageID = 0;
	this.type = 'global';
	this.mainPanel = mainPanelDiv;
    },
    refreshMainPanelQuery: function(){
	this.refreshMainPanelDisplay();

	// need to do real filtering/display stuff here
    },
    refreshMainPanelDisplay: function(){
	let this_ = this;
	jQuery(this.mainPanel).html('webpages '); // remove all old items

	if (jQuery('#leftpanel .item').find('.selected').length) {	   
	    jQuery('#leftpanel .item').parent().each(
		function(i, group) {
		    let text = jQuery(group).parent().find('.label').text();
		    
		    // nasty - this will prepend the next section with what type it is
		    if (text == 'friends' && jQuery(group).children().find('.selected').length) {
			jQuery(this_.mainPanel).append('viewed by ');		   
		    } else if (text =='groups' && jQuery(group).children().find('.selected').length){
			jQuery(this_.mainPanel).append('in the group(s) ');		   
		    }

		    jQuery(group).children().find('.selected').each(
			function(i, item) {
			    let np = jQuery('#templates>.filterquery')
				.clone();
			    np.find('.name')
				.text(jQuery(item).parent().find('name').text())
				.addClass('selected');	
			    jQuery(this_.mainPanel).append(np);
			});
		});
	} else {
	    jQuery(this.mainPanel).html(''); // cleanup if nothing happened
	}
    },
    getRecentPages: function(divid, num, type, div){
        let this_ = this;
	jQuery("#loadimg").show();

	// return if 
	if (jQuery(div).text() == 'show latest views') {
	    jQuery('#notifications>.recentpage').remove();
	    return;
	} else {
	    jQuery.get("/get_latest_views", {
			   id: this_.lastPageID,
			   type: type,
			   num: num,
			   username: 'zamiang'
		       }, function(data){
			   jQuery("#loadimg1").hide();
			   if (data.code == 200) {
			       let now = new Date().valueOf();
			       data.results.map(function(item) { this_.addRecentPage(divid, item, now); });
			       this_.lastPageID = data.results[0].id;
			   }
		       }, "json");
	}
    },
    addRecentPage: function(divid, page, now) {
	let name = page.title?page.title.substring(0,30):cleanupURL(page.url);

	/*  keep track of times displayed and hide old ones
	this_.recentTimesArray.unshift(newData[i].end);
	if (this_.recentTimesArray.length > num){
	    jQuery("#" + this_.recentTimesArray[num + 1]).hide();
	    this_.recentTimesArray.pop();   
	}  */

	let np = jQuery('#templates>.recentpage').clone();
	np.id = page.id;
	
	let title = np.find('.title')
	    .text(name)
	    .attr({'href':page.url});

	let time = np.find('.time')
	    .html(timeCounterClock((now - page.end)/1000) + " ago");	

	if (page.user.length > 0){
	    let user = np.find('.user')
		.html(" by <a href=\"/profile/" + page.user + 
		      "\ style=\"float:right\">" + page.user + "</a>"); 
	}
	jQuery(divid).append(np);
    }

};

// ui events
let showNotifications = function(div) { 
    jQuery(div).text()=='show latest views'?
	jQuery(div).text('hide latest views')
	:jQuery(div).text('show latest views');    
    self.viz.getRecentPages(jQuery(div).parent(), 30, self.viz.type, div);
 };

let addUser = function(div) { toggleAdd(div); }; //more later
let addGroup = function(div) { toggleAdd(div); }; // more later

let addGroups = function(div) {
    // more verbose but safer
    if (jQuery('#mainpanel #recs').is(':hidden')) {
	jQuery('#mainpanel #addGroups').hide();
	jQuery('#mainpanel #recs').show();	  
    } else {
	jQuery('#mainpanel #addGroups').show();
	jQuery('#mainpanel #recs').hide();	
    }
};
 

let toggleAdd = function(div) {     
    // potential bug here with removing items via the list in main panel
    (jQuery(div).text()=='show')?jQuery(div).addClass('selected').text('hide'):
	jQuery(div).removeClass('selected').text('show'); 
    viz.refreshMainPanelQuery(div);
};

jQuery(document).ready(
    function(){	
	var currentDate = new Date();				   
	self.viz = newify(Eyebrowser, '#mainpanel #recs #query');
    });

