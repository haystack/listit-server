function clone(obj){ // TODO: is there something like this in plumutil??
    if(obj == null || typeof(obj) != 'object')
        return obj;
    var temp = new obj.constructor(); 
    for(var key in obj)
        temp[key] = clone(obj[key]);
    return temp;
}

var Eyebrowser = {
    initialize: function(mainPanelDiv, type) {
	this.lastPageID = 0;	
	this.type = type;
	this.setQueryHeader(type);
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
	this.resetQuery();
    },
    setQueryHeader: function(type) {
	if (type == "pages") {
	    this.queryHeader = " websites viewed ";	    
	} else {
	    this.queryHeader = " users ";	    
	}
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
									  this_.baseQuery[type] = jQuery(this).text();
									  this_.refreshQueryInterface(div);
									  this_.runQuery(this_.type);
								      });
					       });

	jQuery("#search select").each(
				      function(i, item) {
					  jQuery(item).change(
							      function(){
								  this_.baseQuery[jQuery(this).attr('name')] = jQuery(this).val();
								  this_.refreshQueryInterface(div);
								  this_.runQuery(this_.type);
							      });
				      });

	this.refreshQueryInterface(query, div);
	this.runQuery(this.type);
    },
    runQuery: function(type){
	if (type == "pages") {	   
	    jQuery('#trending').show();
	    this.getRecentPages("#mainpanel", 60);	
	    this.getRecs('#trending');
	} else if (type == "users") {
	    jQuery('#trending').hide();
	    this.getUsers("#mainpanel", 40);
	}
    },
    initCompareQueryInterface: function(blankQuery, baseQuery){	  
	jQuery('.panel').append(jQuery('.subpanel').clone().addClass('compare'));
	jQuery('#report').append(jQuery('#trending').clone().addClass('compare').show().css({'float':'left'}));
	jQuery('#report').append(jQuery('#trending').clone().addClass('compare').show());
    },
    refreshQueryInterface: function(div){
	// this runs evertime an item is clicked
	let this_ = this;
	this.lastPageID = 0;
	jQuery('#mainpanel').html('')
	jQuery("#search .subpanel a.add").each(
					       function(i, item) {
						   let type = jQuery(item).parent().find('.name').text();
						   if (this_.baseQuery[type] == jQuery(item).text()){ jQuery(item).addClass('selected');}
						   else { jQuery(item).removeClass('selected');}
					       });

	this.displayQuery(this_.baseQuery, div, this.type);
    },
    displayQuery: function(query, div, type) {
	let stmnt = "showing " + type + " ";
	if (type == "pages"){
	    stmnt = "showing websites "; // REASSIGNMENT
	}

	if (type == "users"){
	    stmnt += "who are ";
	}

	if (query['seen'] != "all sites"){
	    stmnt += "<b>" + "i haven't visited</b>, visited by ";
	} else if (type == "pages") {
	    stmnt += "visited by ";
	}

	stmnt += "<b>" + query['friends'] + "</b>";
       

	if (query['gender'] != "all"){
	    stmnt += " of the <b>" + query['gender'] + "</b> gender ";
	}
	if (query['age'] != 'all') {
	    stmnt += " ages <b>" + query['age'] + "</b>";
	}

	if (query['country'] != 'any'){
	    stmnt += " in <b>" + query['country'] + "</b> ";  
	}

	if (query['group'] != 'any'){
	    stmnt += " in the <b>" + query['group'] + "</b> group";   
	}

	if (stmnt == "showing pages websites visited by ") {
	    stmnt = "";
	}

	if (stmnt == "showing users who are ") {
	    stmnt = "";
	}

	jQuery(div).html(stmnt);
    },
    getRecs: function(divid) {
	let this_ = this;
	
	this.trendingLoading(true);
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
			   jQuery(divid).html("");
			   this_.addQueryRecs(data.results, divid);
			   this_.trendingLoading(false);
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
    getUsers: function(divid, num){
	// should get trending for the current query
	let this_ = this;
	this.mainLoading(true);
	jQuery.get("/get_top_users_for_filter", {
		       id: this_.lastPageID,
		       groups: jQuery('#group').val(),
		       country: jQuery('#country').val(),
		       friends: jQuery('#friends .selected').text(),
		       gender: jQuery('#gender .selected').attr('data-val'),
		       age: jQuery('#age .selected').attr('data-val'),
		       time: jQuery('#recently .selected').text(),
		       seen: jQuery('#hasseen .selected').text()
		   }, function(data){
		       this_.mainLoading(false);
		       if (data.code == 200) {
			   jQuery(divid).html("");
			   data.results.map(function(item) { this_.addUser(divid, item[0], item[1]); });
		       }
		   }, "json");
    },
    addUser: function(divid, user, number){
	let np = jQuery('#templates>.user').clone();			 
	
	let title = np.find('.title')
	    .text(user.username)
	    .attr({'href':"/profile/" + user.username});

	let img = np.find('img.profileimage')
	    .attr({'src':"/profiles/" + user.id + ".jpg"});

	let number = np.find('.number').append("<b>" + number + "</b>");		

	if (user.is_friend == 0) { 
	    np.find('a.follow').attr({'href':"/friend/add?username=" + user.username});
	} else { np.find('a.follow').html('');}

	if (user.is_followed_by == 1) { np.find('.isfollowing').text('is following you');}
	if (user.age){np.find('.age').append(user.age[0]);} else  { np.find('.age').html("");};	
	if (user.location){ np.find('.location').append(user.location); } else { np.find('.location').html("");};		
	if (user.tags) {np.find('.tags').append(user.tags); } else { np.find('.tags').html(''); };	
	if (user.website) { 
	    np.find('.website')
		.html("<span class=\"italicsname\">website:</span>&nbsp;<a href=" + user.website + ">" + user.website + "</a>");}
	else {  np.find('.website').html("");};		

	if (user.latest_view[0]) { np.find('.latest').html("<span class=\"italicsname\">last viewed:</span>&nbsp;<a href=" + user.latest_view[0].url + ">" + user.latest_view[0].url + "</a>"); }
	else { np.find('.latest').html(""); }
		
	jQuery(divid).append(np);		      
    },
    getRecentPages: function(divid, num){
        let this_ = this;
	this.mainLoading(true);
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
		       this_.mainLoading(false);
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

	let title = np.find('.title')
	    .text(name)
	    .attr({'href':page.url});

	let time = np.find('.time')
	    .html(timeCounterClock((now - page.end)/1000) + " ago");	

	if (page.user.length > 0){
	    let user = np.find('.user')
		.html(" by <a href=\"/profile/" + page.user + 
		      "\">" + page.user + "</a>"); 
	}
	
	np.find('.stats').click(
	    function(){
		jQuery(this).text('loading...');
		
		
		jQuery(this).text('hide stats');
	    });

	jQuery(divid).append(np);
    },
    makeCompare: function(){
	if (this.type == "compare"){ return;}
	this.type = "compare";
	
	jQuery('#topnav a:eq(0)').removeClass('selected');	
	jQuery('#topnav a:eq(1)').addClass('selected');	

	jQuery('#trending').hide();
	jQuery('#comparetitle').show();	this.runQuery(this.type);
	this.initCompareQueryInterface(clone(this.blankQuery), this.baseQuery);	
    },
    makeSearch: function(){
	if (this.type == "pages"){ return;}
	this.type = "pages";

	jQuery('#topnav a:eq(1)').removeClass('selected');	
	jQuery('#topnav a:eq(0)').addClass('selected');	

	jQuery('#mainpanel, #trending, #hasseen').show();
	jQuery('#mainpanel').css({width:'44%'}).html('');
	this.lastPageID = 0;
	this.setQueryHeader(this.type);
	this.resetQuery();
	this.refreshQueryInterface(this.mainPanel);
	this.runQuery(this.type);
    },
    makePeople: function(){
	if (this.type == "users"){ return;}
	this.type = "users";
	
	jQuery('#topnav a:eq(0)').removeClass('selected');	
	jQuery('#topnav a:eq(1)').addClass('selected');	

	jQuery('#trending, #trendingloading, #mainloading, #hasseen').hide();
	jQuery('#mainpanel').css({width:'80%'});
	this.setQueryHeader(this.type);
	this.resetQuery();
	this.refreshQueryInterface(this.mainPanel);
	this.runQuery(this.type);
    },
    mainLoading: function(isloading) {
	if (isloading) {
	    jQuery('#mainpanel').css({opacity:0.4});
	    jQuery('#mainloading')
		.show()
		.css({top:'400px', left: jQuery('#query').position().left*2 });
	} else {
	    jQuery('#mainpanel').css({opacity:1});
	    jQuery('#mainloading').hide();	    
	}
    },
    trendingLoading: function(isloading) {
	if (isloading) {
	    jQuery('#trending').css({opacity:0.4});
	    jQuery('#trendingloading')
		.show()
		.css({top:'400px', left: jQuery('#trending').position().left + (jQuery('#trending').width()/2)  });
	} else {
	    jQuery('#trending').css({opacity:1});
	    jQuery('#trendingloading').hide();	    
	}
    },   
    resetQuery: function(){
	jQuery('select').removeAttr("selectedIndex");
	this.baseQuery = clone(this.blankQuery);
    }
};

jQuery(document).ready(
    function(){	
	self.viz = newify(Eyebrowser, '#query', 'pages');
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
