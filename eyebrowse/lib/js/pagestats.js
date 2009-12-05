var WatchmeVisualisation = {
    initialize: function(canvas, windowWidth, windowHeight, timeZoneCorrect, zoom, url) {
        this.canvas = canvas;
        this.windowWidth = windowWidth;
        this.windowHeight = windowHeight;
        this.timeZoneCorrect = timeZoneCorrect;
	this.now = new Date().valueOf();
        this.endTime = this.now;
        this.startTime = new Date(this.endTime - zoom).valueOf();
        this.interp = zoom / 192;
        this.drag = undefined;
        this.zoom = zoom;
	this.url = url;
	this.type = "global";
	this.getClosestUrl(this.url);
    },
    getClosestUrl: function(type){
	var this_ = this;	
	jQuery.get("/get_closest_url/", { url:this_.url },
		   function(data) {						   
		       if (data.code == 200) {
			   this_.url = data.results.length > 0 ? data.results[0] : "";
			   jQuery("#urladdtextinput").val(this_.url);							   
			   this_.getProfile(); 
		       } else {
			   //console.log("error calling get_closest_url: " + data.code + " " + data);
		       }
		   }, "json");	    	           	
    },
    getProfile: function(){
	var this_ = this;
	jQuery("#loadimg").show();
	jQuery.get("/get_pagestats", {
		       from: this_.startTime,
		       to: this_.endTime,
		       type: this_.type,
		       url:this_.url,
		       username: '{{ request_user }}'
		   }, function(data){
		       jQuery("#loadimg").hide();
		       if (data.code == 200) {		
			   var newData = data.results;
			   jQuery("#topuser").html("<a href=\"http://eyebrowse.csail.mit.edu/profile/" + data.results[1][0].user + "/\">" + data.results[1][0].user + "</a>");
			   jQuery("#user").css("font-weight","lighter");
			   jQuery("#friends").css("font-weight","lighter");
			   jQuery("#global").css("font-weight","lighter");
			   jQuery("#" + this_.type).css("font-weight","bold");

			   this_.drawToFromGraph(data.results[3]);
			   this_.drawProfile(data.results[2]);
			   this_.drawGraphs(data.results[0]);
			   this_.drawTopUsers(data.results[1]);
		       }
		       else {
			   //console.log("yaaaa!!!H!H!H!" + data.code + " ");
		       }
		   }, "json");
    },
    drawProfile: function(data){
	var newData = data;
	jQuery("#totalTime").html("&nbsp; &#124; &nbsp;<b>total time: </b> " + timeCounterLongAbv(newData.totalTime));
	jQuery("#num").html("<b>visit count: </b>" + newData.number);
	jQuery("#avgTime").html("&nbsp; &#124; &nbsp;<b>avg time per visit: </b>" + timeCounterLongAbv(newData.average));
    },
    drawTopUsers: function(data){
	var this_ = this;
	var html = "";
	for (var i = 0; i < data.length; i++) {
	    if (data[i].number > 0){
		html += "<li>";
		html += "<a href=\"/profile/" + data[i].user + "/\">" + data[i].user + "</a><h7>" + data[i].number + "</h7>";
		html += "</li>";					
	    }
 	}
	jQuery("#topvisitors").html(html);					   			
    },
    drawToFromGraph: function(data){
	var this_ = this;
	// 3 columns of divs
	var leftHTML = "";
	var rightHTML = "";
	var centerHTML = "<h6 style=\"padding:0px\"><a href=\"" + this_.url + "\" style=\"font-weight:bold\">" + this_.url + "</a></h6>";
	
	for (var i = 0; i < data.pre.length; i++){
	    if (data.pre_titles[i]){
		leftHTML += "<h6 class=\"leftside\"><a href=\"" + data.pre[i][0] + "\" target=\"_blank\">" + data.pre_titles[i].substring(0,50) + "</a></h6>";
	    }
	    else{
		leftHTML += "<h6 class=\"leftside\"><a href=\"" + data.pre[i][0] + "\" target=\"_blank\">" + data.pre[i][0].substring(0,50) + "</a></h6>";
	    }									  
	    leftHTML += "<a href=\"javascript: viz.swopURL('" + data.pre[i][0] + "')\"><img src=\"/lib/img/smallbird_b.jpg\" style=\"margin-left:3px;display:inline-block;margin-bottom:4px;\"/></a>";
	    leftHTML += "<br />";
	}
	for (var i = 0; i < data.next.length; i++){
	    rightHTML += "<a href=\"javascript: viz.swopURL('" + data.next[i][0] + "')\"><img src=\"/lib/img/smallbird_b.jpg\" style=\"margin-right:3px;display:inline-block;margin-bottom:4px;\"/></a>";
	    if (data.next_titles[i]){
		rightHTML += "<h6><a href=\"" +  data.next[i][0] + "\" target=\"_blank\">" + data.next_titles[i].substring(0,50) + "</a></h6>";
	    }
	    else{
		rightHTML += "<h6><a href=\"" + data.next[i][0] + "\" target=\"_blank\">" + data.next[i][0].substring(0,50) + "</a></h6>";					
	    }
	    rightHTML += "<br />";
	}			
	jQuery("#urlLeft").html(leftHTML);
	jQuery("#urlRight").html(rightHTML);
	jQuery("#urlCenter").css({'left' : 475 - (this_.url.length * 7)/2 + "px"});					   			
	jQuery("#urlCenter").html(centerHTML);					   			

	var toFromGraph = newify(compareFactory, this_, {
				     canvas: document.getElementById("main"),
				     windowHeight: 145,
				     windowWidth: 950,
				     lineWidth: 5,
				     minH: 190,
				     maxH: 300, // hue
				     xOffset: 302,
				     data: data
				 });			
    },
    drawGraphs: function(data){
	var this_ = this;
	
	var timeDayGraph = newify(barGraphLite, {
				      canvas: document.getElementById("dayTimeGraph"),
				      windowHeight: this_.windowHeight,
				      windowWidth: this_.windowWidth,
				      color: "#ff00ff",
				      bottomPadding:30,
				      columnWidth:8,
				      barPadding:0,
				      textPadding:0,
				      label: [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
				      data: data['timeDay']
				  });

	var dayWeekGraph = newify(barGraphLite, {
				      canvas: document.getElementById("dayWeekGraph"),
				      windowHeight: this_.windowHeight,
				      windowWidth: this_.windowWidth,
				      bottomPadding:30,
				      barPadding:10,
				      textPadding:4,
				      columnWidth:20,																 
				      label: ['Monday', 'Tuesday', 'Wednes', 'Thursday', '  Friday', 'Saturday', 'Sunday'],
				      data: data['dayWeek']
				  });
    },
    refresh: function(){
	var this_ = this;	    
	this_.url = jQuery("#urladdtextinput").val();
	jQuery.get("/get_closest_url/", { url:this_.url },
		   function(data) {
		       if (data.code == 200) {
			   this_.url = data.results.length > 0 ? data.results[0] : "";
			   jQuery("#urladdtextinput").val(this_.url);
			   this_.getProfile(); 
		       } else {
			   // console.log("error calling get_closest_url: " + data.code + " " + data);
		       }
		   }, "json");	    	    
    },
    changeType: function(type){
	var this_ = this;	    
	this_.type = type;
	this_.getProfile();
    },
    swopURL: function(newURL){
	jQuery("#urladdtextinput").val(newURL);
	viz.refresh();
    }
};
jQuery(document).ready(function(){
			   jQuery('#header').width(window.innerWidth - 15);
			   
			   jQuery("#urladdtextinput").focus();
			   var currentDate = new Date();																			
			   var myWidth = 700;
			   var myHeight = 400;
			   var input = jQuery("#urladdtextinput").val();

			   document.getElementById("dayTimeGraph").setAttribute("width", 335);
			   document.getElementById("dayTimeGraph").setAttribute("height", 175);
			   document.getElementById("dayWeekGraph").setAttribute("width", 335);
			   document.getElementById("dayWeekGraph").setAttribute("height", 175);
			   document.getElementById("main").setAttribute("width", 950);
			   document.getElementById("main").setAttribute("height", 230);

			   self.viz = newify(WatchmeVisualisation, document.getElementById("main"), 335, 175, 0, 2419200000, input);// 4 weeks
		       });
