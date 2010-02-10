function clone(obj){ // TODO: is there something like this in plumutil??
    if(obj == null || typeof(obj) != 'object')
        return obj;
    var temp = new obj.constructor(); 
    for(var key in obj)
        temp[key] = clone(obj[key]);
    return temp;
}

var Eyebrowser = {
    initialize: function(mainPanelDiv) {
	this.lastPageID = 0;
	this.type = 'global';
	this.mainPanel = mainPanelDiv;
	this.blankQuery = {
	    group: "any", //[],
	    seen: "all sites", //[],
	    country: "any", //[],
	    friends: "everyone",
	    gender: "all",
	    age: "all",
	    time: "recently"
	};
	this.baseQuery = clone(this.blankQuery);
	this.initQueryInterface(this.baseQuery, mainPanelDiv);
	this.getRecentPages("#mainpanel", 60, this.type, jQuery("#latest .sign"));
	this.getRecs('#latest');
    },
    getRecs: function(divid) {
	let this_ = this;
	
	jQuery("#loadimg").show();
	jQuery.get("/get_trending_sites", {
		       groups: jQuery('#group').val(),
		       country: jQuery('#country').val(),
		       friends: jQuery('#friends .selected').text(),
		       gender: jQuery('#gender .selected').attr('data-val'),
		       age: jQuery('#age .selected').attr('data-val'),
		       time: jQuery('#recently .selected').text(),
		       seen: jQuery('#hasseen .selected').text()
		   }, function(data){
		       jQuery("#loadimg").hide();
		       if (data.code == 200) {
			   this_.addQueryRecs(data.results, divid);
		       }
		       else {
			   // console.log("yaaaa!!!H!H!H!" + data.code + " ");
		       }
		   }, "json");
    },
    addQueryRecs: function(sites, divid){
	jQuery(divid).html('<h2>trending sites</h2>');
	sites.map(function(site){
		      if (site.title && site.url){			  
			  let np = jQuery('#templates>.recpage').clone();			 
			  
			  let title = np.find('.title')
			      .text(site.title)
			      .attr({'href':site.url});

			  let link = np.find('.url')
			      .text(site.url)
			      .attr({'href':site.url});

			  np.find('.stats').click(
			      function(){
				  jQuery(this).text('loading...');


				  jQuery(this).text('hide stats');
			      });
			  			  
			  jQuery(divid).append(np);		      
		      }
		  });
    },
    initQueryInterface: function(query, div) {	
	let this_ = this;
	jQuery("#search .subpanel a.add").each(
	    function(i, item) {
		let type = jQuery(item).parent().find('.name').text();
		if (query[type] == jQuery(item).text()){ jQuery(item).addClass('selected');}
		jQuery(item).click(
		    function() {
			jQuery(this).parent().find('a.add').each(function(i, item){ jQuery(item).removeClass('selected');});
			jQuery(this).addClass('selected');
			query[type] = jQuery(this).text();
			this_.refreshQueryInterface(query, div);
		    });
	    });	

	jQuery("#search select").each(
	    function(i, item) {
		jQuery(item).click(
		    function(){
			query[jQuery(this).attr('name')] = jQuery(this).val();
			this_.refreshQueryInterface(query, div);
		    });
	    });
	this.refreshQueryInterface(query, div);
    },
    initCompareQueryInterface: function(blankQuery, baseQuery){	  
	jQuery('.panel').append(jQuery('.subpanel').clone().addClass('compare'));
	
	jQuery('#report').append(jQuery('#latest').clone().addClass('compare').show().css({'float':'left'}));
	jQuery('#report').append(jQuery('#latest').clone().addClass('compare').show());
    },
    refreshQueryInterface: function(query, div){
	let this_ = this;
	//this.refreshQueryResults(query);
	this.displayQuery(query, div);
    },
    displayQuery: function(query, div) {
	// TODO

	jQuery(div).html("showing websites viewed " +
			// "<b>" + query['time'] + "</b> by " +
			 "<b>" + query['friends'] + "</b>" +
			 " of the <b>" + query['gender'] + "</b> gender(s) " +
			 " age <b>" + query['age'] + "</b>" +
			 " in <b>" + query['country'] + "</b> country" +
			 " and <b>" + query['group'] + "</b> group");
    },
    getRecentPages: function(divid, num, type){
        let this_ = this;
	jQuery("#loadimg").show();

	// should get latest for the current query
	jQuery.get("/get_latest_sites_for_filter", {
		       id: this_.lastPageID,
		       groups: jQuery('#group').val(),
		       country: jQuery('#country').val(),
		       friends: jQuery('#friends .selected').text(),
		       gender: jQuery('#gender .selected').attr('data-val'),
		       age: jQuery('#age .selected').attr('data-val'),
		       time: jQuery('#recently .selected').text(),
		       seen: jQuery('#hasseen .selected').text()
		   }, function(data){
		       jQuery("#loadimg").hide();
		       if (data.code == 200) {
			   let now = new Date().valueOf();
			   data.results.map(function(item) { this_.addRecentPage(divid, item, now); });
			   this_.lastPageID = data.results[0].id;
		       }
		   }, "json");
    },
    getUsers: function(divid, num, type){
        let this_ = this;
	jQuery("#loadimg").show();

	// should get latest for the current query
	jQuery.get("/get_users_for_filter", {
		       groups: jQuery('#group').val(),
		       country: jQuery('#country').val(),
		       friends: jQuery('#friends .selected').text(),
		       gender: jQuery('#gender .selected').attr('data-val'),
		       age: jQuery('#age .selected').attr('data-val'),
		       time: jQuery('#recently .selected').text(),
		       seen: jQuery('#hasseen .selected').text()
		   }, function(data){
		       jQuery("#loadimg").hide();
		       if (data.code == 200) {
			   let now = new Date().valueOf();
			   data.results.map(function(item) { this_.addRecentPage(divid, item, now); });
			   this_.lastPageID = data.results[0].id;
		       }
		   }, "json");
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
	
	np.find('.colorbox').css({'background-color': 'hsl(' + page.hue + ',100%, 50%)'});

	//console.log(page.hue);

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
	
	np.find('.stats').click(
	    function(){
		jQuery(this).text('loading...');
		
		
		jQuery(this).text('hide stats');
	    });

	jQuery(divid).append(np);
    },
    makeSearch: function(){
	if (this.mode == "search"){ return;}
	this.mode = "search";

	jQuery('#topnav a:eq(1)').removeClass('selected');	
	jQuery('#topnav a:eq(0)').addClass('selected');	

	jQuery('#mainpanel, #latest').show();
	jQuery('#comparetitle, .compare').hide();
	this.deleteCompare();
    },
    makeCompare: function(){
	if (this.mode == "compare"){ return;}
	this.mode = "compare";
	
	jQuery('#topnav a:eq(0)').removeClass('selected');	
	jQuery('#topnav a:eq(1)').addClass('selected');	

	jQuery('#mainpanel, #latest').hide();
	jQuery('#comparetitle').show();
	this.initCompareQueryInterface(clone(this.blankQuery), this.baseQuery);	
    },
    makePeople: function(){
	if (this.mode == "compare"){ return;}
	this.mode = "compare";
	
	jQuery('#topnav a:eq(0)').removeClass('selected');	
	jQuery('#topnav a:eq(1)').addClass('selected');	

	jQuery('#mainpanel, #latest').hide();
	jQuery('#comparetitle').show();
	//this.initCompareQueryInterface(clone(this.blankQuery), this.baseQuery);	
    },
    deleteCompare: function() {
	jQuery('.subpanel:eq(1)').remove(); // TODO delete everything past 0 
    }
};

jQuery(document).ready(
    function(){	
	var currentDate = new Date();				   
	self.viz = newify(Eyebrowser, '#query');
    });


/*
 * CRUFT

let toggleAdd = function(div) {     
    // potential bug here with removing items via the list in main panel
    (jQuery(div).text()=='show')?jQuery(div).addClass('selected').text('hide'):
	jQuery(div).removeClass('selected').text('show'); 
    viz.refreshMainPanelQuery(div);
};


 // ui events
 
    showNotifications: function(div) { 
	jQuery(div).text()=='show latest views'?
	    jQuery(div).text('hide latest views')
	    :jQuery(div).text('show latest views');    
	self.viz.getRecentPages(jQuery(div).parent(), 30, self.viz.type, div);
    },
    addUser: function(div) { toggleAdd(div); }, //more later
    addGroup: function(div) { toggleAdd(div); }, // more later
    addGroups: function(div) {
	// more verbose but safer
	if (jQuery('#mainpanel #recs').is(':hidden')) {
	    jQuery('#mainpanel #addGroups').hide();
	    jQuery('#mainpanel #recs').show();	  
	} else {
	    jQuery('#mainpanel #addGroups').show();
	    jQuery('#mainpanel #recs').hide();	
	}
    }

 */
