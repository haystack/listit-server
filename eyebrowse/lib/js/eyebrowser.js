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
    search: function(){
	jQuery('#query').show();
	this.refreshQueryInterface(this.mainPanel);
	this.runQuery(this.type);
    },
    initQueryInterface: function(query, div) {	
	var this_ = this;
	jQuery("#search .subpanel a.add").each(
	    function(i, item) {
		var type = jQuery(item).parent().find('.name').text();
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
	setInterval(function(){ if (viz.type == "pages"){ viz.runQuery(viz.type);} }, 10000);
	this.runQuery(this.type);
    },
    runQuery: function(type){
	if (type == "pages") {	   
	    try {		
		jQuery('#trending').show();
		this.getRecentPages("#mainpanel", 60);	
		this.getRecs('#trending');
	    } catch (x) {
		console.log(x);
	    }
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
	var this_ = this;
	this.lastPageID = 0;
	jQuery('#mainpanel').html('');
	jQuery("#search .subpanel a.add").each(
	    function(i, item) {
		var type = jQuery(item).parent().find('.name').text();
		if (this_.baseQuery[type] == jQuery(item).text()){ jQuery(item).addClass('selected');}
		else { jQuery(item).removeClass('selected');}
	    });
	
	this.displayQuery(this_.baseQuery, div, this.type);
    },
    displayQuery: function(query, div, type) {
	var stmnt = "showing " + type + " ";
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
	var this_ = this;
	
	this.trendingLoading(true);
	jQuery.getJSON("/get_trending_sites", {
		       groups: jQuery('#group').val(),
		       country: jQuery('#country').val(),
		       friends: jQuery('#friends .selected').text(),
		       gender: jQuery('#gender .selected').attr('data-val'),
		       age: jQuery('#age .selected').attr('data-val'),
		       time: 'recently',
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
		      try {
			  if (site.title && site.url){			  
			  var np = jQuery('#templates>.recpage').clone();			 
			  
			  var title = np.find('.title')
			      .text(site.title)
			      .attr({'href':site.url});

			  var link = np.find('.url')
			      .text(site.url)
			      .attr({'href':site.url});

			  np.find('.stats').click(
			      function(){
				  jQuery(this).text('loading...');


				  jQuery(this).text('hide stats');
			      });
			  			  
			  jQuery(divid).append(np);		      
			  }
		      } catch (x) {
			  
		      }		      
		  });
    },
    getUsers: function(divid, num){
	// should get trending for the current query
	var this_ = this;
	this.mainLoading(true);
	jQuery.getJSON("/get_top_users_for_filter", {
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
	var this_ = this;
	var np = jQuery('#templates>.user').clone();			 
	
	var title = np.find('.title')
	    .text(user.username)
	    .attr({'href':"/profile/" + user.username});

	if (user.has_photo == true){
	    np.find('img.profileimage')
		.attr({'src':"/profiles/" + user.id + ".jpg"});	    
	} else {
	    np.find('img.profileimage')
		.attr({'src':"/profiles/o.jpg"});	    	   
	}

	var number = np.find('.number').append("<b>" + number + "</b>");		

	if (user.is_following == 0) { 
	    np.find('a.follow').click(function(){ this_.followUser(user.username, np); });
	    np.find('.isfollowing').hide();
	} else if (user.is_following == -1) {
	    np.find('.isfollowing').hide();
	    np.find('a.follow').hide();
	}
	else {
	    np.find('.isfollowing').html("<img src='/lib/img/go.png'></img> following");
	    np.find('a.follow').hide();}
	
	if (user.is_followed_by == 1) { np.find('.isfollowedby').html(" is following you"); }

	if (user.age){np.find('.age').append(user.age[0]);} else  { np.find('.age').html("");};	
	if (user.location){ np.find('.location').append(user.location); } else { np.find('.location').html("");};		
	//if (user.tags) {np.find('.tags').append(user.tags); } else { np.find('.tags').html(''); };	
	if (user.website) { 
	    np.find('.website')
		.html("<span class=\"italicsname\">website:</span>&nbsp;<a href=" + user.website + ">" + user.website + "</a>");}
	else {  np.find('.website').html("");};		

	if (user.latest_view[0]) { np.find('.latest').html("<span class=\"italicsname\">last viewed:</span>&nbsp;<a href=" + user.latest_view[0].url + ">" + user.latest_view[0].url + "</a>"); }
	else { np.find('.latest').html(""); }
		
	jQuery(divid).append(np);		      
    },
    followUser: function(username, div){
	jQuery.post("/friend/add?username=" + username, {}, function(data){
			jQuery(div).find('a.follow').html('you are now following ' + username).removeClass('follow');
			});

    },
    getRecentPages: function(divid, num){
        var this_ = this;
	this.mainLoading(true);
	// should get latest for the current query
	jQuery.getJSON("/get_latest_sites_for_filter", {
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
			   jQuery('#help').html('');
			   if (data.code == 200) {
			       var now = new Date().valueOf();
			       data.results.map(function(item) { this_.addRecentPage(divid, item, now); });
			       this_.lastPageID = data.results[0].id;
			   }
			   else { jQuery('#mainpanel').html("<div id='help' class='recentpage'><div class='title'>sorry! no results ;(</div></div>"); } 
		       }, "json");
    },
    addRecentPage: function(divid, page, now) {
	var name = page.title?page.title:cleanupURL(page.url);
	
	/*  keep track of times displayed and hide old ones
	this_.recentTimesArray.unshift(newData[i].end);
	if (this_.recentTimesArray.length > num){
	    jQuery("#" + this_.recentTimesArray[num + 1]).hide();
	    this_.recentTimesArray.pop();   
	}  */

	var np = jQuery('#templates>.recentpage').clone();
	np.id = page.id;
	
	np.find('.colorbox').css({'background-color': 'hsl(' + page.hue + ',100%, 50%)'});

	var title = np.find('.title')
	    .text(name)
	    .attr({'href':page.url});

	var time = np.find('.time')
	    .html(timeCounterClock((now - page.end)/1000) + " ago");	

	if (page.user.length > 0){
	    var user = np.find('user')
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
		.css({top:'600px', left: jQuery('#query').position().left*2 });
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
		.css({top:'600px', left: jQuery('#trending').position().left + (jQuery('#trending').width()/2)  });
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
jQuery(document).ready(function(){ self.viz = Eyebrowser; self.viz.initialize('#query', 'pages'); });