var WatchmeVisualisation = {
    initialize: function(canvas, windowWidth, windowHeight, timeZoneCorrect, zoom) {
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
	this.recentTimesArray = [];
	this.recentID = 0;
	this.type = "global";
	document.getElementById("bgcanvas").setAttribute("width", this.windowWidth);
	document.getElementById("bgcanvas").setAttribute("height", this.windowHeight);
	this.getPage(this.type);
    },
    getPage: function(type){
	this.type = type;
	this.recentID = 0;
        this.getProfile(type);			
        this.getRecentPages(30, type);

    },
    getRecentPages: function(num, type){
        var this_ = this;
	this_.now = new Date().valueOf();
	jQuery("#loadimg1").show();
	jQuery.get("/get_latest_views", {
		       id: this_.recentID,
		       type: type,
		       num: num,
		       username: '{{ request_user }}'
		   }, function(data){
		       jQuery("#loadimg1").hide();
		       if (data.code == 200) {
			   var newData = data.results;
			   var html = "";
			   for (var i = newData.length -1; i >= 0; i--) {
			       html = "<li id=\"" + newData[i].end + "\">";
			       if (newData[i].title){
				   html += "<h6><b><a href=\"" + newData[i].url + "\">" + newData[i].title.substring(0,30) + "</a></b></h6>";
			       }
			       else{
				   html += "<h6><b><a href=\"" + newData[i].url + "\">" + cleanupURL(newData[i].url) + "</a></b></h6>";
			       }
			       html += "<h7>" + timeCounterClock((this_.now - newData[i].end)/1000) + " <b>ago</b></h7>";
			       if (newData[i].user.length > 0) {
				   html += "<br />&nbsp; &nbsp; <a href=\"/profile/" + newData[i].user + "\" style=\"font-weight:normal; font-size:0.8em; display:inline-block\">by " + newData[i].user + "</a>";
			       }
			       html += "</li>";
			       jQuery("#latestviews").prepend(html);
			       jQuery("#" + newData[i].end).slideDown("slow");

			       // keep track of times displayed and hide old ones
			       this_.recentTimesArray.unshift(newData[i].end);
			       if (this_.recentTimesArray.length > num){
				   jQuery("#" + this_.recentTimesArray[num + 1]).hide();
				   this_.recentTimesArray.pop();   
			       }
			   }
			   this_.recentID = newData[0].id;
		       }
		       else {
			   // console.log("yaaaa!!!H!H!H!" + data.code + " ");
		       }
		   }, "json");
    },
    getProfile: function(type){
	var this_ = this;
	jQuery("#loadimg").show();
	try {
	    jQuery.get("/get_pulse", {
			   from: this_.startTime,
			   to: this_.endTime,
			   num: Math.floor((this_.windowWidth/10)*(this_.windowHeight/10)),
			   type: type
		       }, function(data){
			   jQuery("#loadimg").hide();
			   if (data.code == 200) {										   
			       var newData = data.results;
			       jQuery("#user").css("font-weight","lighter");
			       jQuery("#friends").css("font-weight","lighter");
			       jQuery("#global").css("font-weight","lighter");
			       jQuery("#" + type).css("font-weight","bold");

			       this_.drawProfile(data.results[0]);								   

			       this_.drawTopPagesList(data.results[3]);
			       this_.drawTopDomains(data.results[4]);
			       this_.drawMiniGraph(data.results[2]);
			       //this_.drawBG(data.results[1]);
			   }
			   else {
			       //console.log("yaaaa!!!H!H!H!" + data.code + " ");
			   }
		       }, "json");
	} 
	catch (e) {
	    // console.log(e);
	}
    },
    drawProfile: function(data){
	var newData = data;
	jQuery("#totalTime").html("&nbsp; &#124; &nbsp;<b>total time: </b> " + timeCounterLongAbv(newData.totalTime));
	jQuery("#num").html("<b>visit count: </b>" + newData.number);
	jQuery("#avgTime").html("&nbsp; &#124; &nbsp;<b>avg time per visit: </b>" + timeCounterLongAbv(newData.average));
    },
    drawTopPagesList: function(data){
        var this_ = this;
	var html = "";

	jQuery("#pages").hide();
	jQuery("#trending").hide();

	for (var i = 0; i < data.top.length; i++) {
	    var trigger = true;
	    html += "<li>";
	    if (data.top_titles[i]){
		html += "<h6><b><a href=\"" + data.top[i][0] + "\" style=\"width:50px;\">" + data.top_titles[i].substring(0,22) + "</a></b></h6>";                						
	    } else {
		html += "<h6><b><a href=\"" + data.top[i][0] + "\" style=\"width:50px;\">" + cleanupURL(data.top[i][0]).substring(0,22) + "</a></b></h6>";                						
	    }
	    if (data.top[i][2] < 0) {
		trigger = false;
		html += "<div class=\"imgbox\">";
		html += "<img src=\"/lib/img/arrow_full_down_16.png\" style=\"float:left\"/>";
		html += "<b>" + data.top[i][2] + "</b>";
		html += "</div>";
	    }
	    if (data.top[i][2] > 0) {
		trigger = false;
		html += "<div class=\"imgbox\">";		   
		html += "<img src=\"/lib/img/arrow_full_up_16.png\" style=\"float:left\"/>";                         
		html += "<b>" + data.top[i][2] + "</b>";
		html += "</div>";
	    }
	    if (trigger) {
		// foo
	    }
	    html += "</li>";
	}
	jQuery("#pages").html(html);					   			
	html = "";
	for (var i = 0; i < data.trending.length; i++) {
	    var trigger = true;
	    html += "<li>";
	    if (data.tre_titles[i]){
		html += "<h6><b><a href=\"" + data.trending[i][0] + "\" style=\"width:50px;\">" + data.tre_titles[i].substring(0,21) + "</a></b></h6>";                						
	    } else {
		html += "<h6><b><a href=\"" + data.trending[i][0] + "\" style=\"width:50px;\">" + cleanupURL(data.trending[i][0]).substring(0,21) + "</a></b></h6>";                						
	    }
	    if (data.trending[i][2] < 0) {
		trigger = false;
		html += "<div class=\"imgbox\">";
		html += "<img src=\"/lib/img/arrow_full_down_16.png\" style=\"float:left\"/>";
		html += "<b>" + data.trending[i][2] + "</b>";
		html += "</div>";
	    }
	    if (data.trending[i][2] > 0) {
		trigger = false;
		html += "<div class=\"imgbox\">";		   
		html += "<img src=\"/lib/img/arrow_full_up_16.png\" style=\"float:left\"/>";                         
		html += "<b>" + data.trending[i][2] + "</b>";
		html += "</div>";
	    }
	    if (trigger) {
		// foo
	    }
	    html += "</li>";
	}
	jQuery("#trending").html(html);					   			
	jQuery("#pages").slideDown('slow');
	jQuery("#trending").slideDown('slow');
    },
    drawTopDomains: function(data){
	var this_ = this;
	var html = "";
	jQuery("#domains").hide();
	for (var i = 0; i < data.length; i++) {
	    if (typeof(data[i][1]) != 'undefined'){
		var trigger = true;
		html += "<li>";
		html += "<h6><b><a href=\"http://" + data[i][0] + "\" style=\"width:50px;\">" + data[i][0].substring(0,22) + "</a></b></h6>";                
		if (data[i][2] < 0) {
		    trigger = false;
		    html += "<div class=\"imgbox\">";
		    html += "<img src=\"/lib/img/arrow_full_down_16.png\" style=\"float:left\"/>";
		    html += "<b>" + data[i][2] + "</b>";
		    html += "</div>";
		}
		if (data[i][2] > 0) {
		    trigger = false;
		    html += "<div class=\"imgbox\">";		   
		    html += "<img src=\"/lib/img/arrow_full_up_16.png\" style=\"float:left\"/>";                         
		    html += "<b>" + data[i][2] + "</b>";
		    html += "</div>";
		}
		if (trigger) {
		    // foo
		}
		html += "</li>";
	    }
 	}
	jQuery("#domains").html(html);		
	jQuery("#domains").slideDown("slow");
    },
    drawBG: function(data){
	var this_ = this;
	var newData = data;
	var zoom = this_.zoom;
	var hour = 1600000; // fudged a litte 1 hour = 3600000
	var bg = {};
	this_.drawArray = [];
	this_.graphArray = [];

	if (this_.type == 'friends'){
	    jQuery("#bginfo").html("background dots: last " + newData.length + " pages visited by your " + this_.type);				
	} else if(this_.type == 'global'){
	    jQuery("#bginfo").html("background dots: last " + newData.length + " pages visited by everyone");				
	} else {
	    jQuery("#bginfo").html("background dots: last " + newData.length + " pages visited by you");				
	}
	this_.isStatic = true;
	this_.dotGraph = newify(dotFactory, this_, {
				    marginTop: 11,
				    den: 18,
				    isInteractive: false,
				    data: newData
				});	
	this_.graphArray.push(this_.dotGraph);
	this_.drawArray.push(this_.graphArray);
	var mainEvtHandlers = newify(evtHandlers, this_);			
    },
    drawMiniGraph: function(data){
	var this_ = this;
	var newData = data;
	
	var avgTimeG = newify(lineGraphFactoryLite, {
				  canvas: document.getElementById("main"),
				  startTime: this_.startTime,
				  endTime: this_.endTime,
				  windowHeight: 50,
				  windowWidth: 950,
				  interp: (this_.endTime - this_.startTime) / 100,
				  color: "#ff00ff",
				  margintop: 30,
				  topPadding: 0,
				  noKey: true,
				  fillGraph: false,
				  data: data.totalTime
			      });
    },
    draw: function(){
	// do nothing	
    },
    getCanvas: function(){
        return this.canvas;
    }
};
jQuery(document).ready(function(){
			   jQuery('#header').width(window.innerWidth - 15);
			   jQuery("#target").hide();
			   jQuery("#toggle").click(function(){
						       if (jQuery("#profile_content").is(":hidden")) {
							   jQuery("#profile_content").slideDown("slow");
							   jQuery("#footer").slideDown("slow");
							   jQuery("#fooTxt").hide();
							   jQuery("#target").hide();
							   self.viz.dotGraph.isInteractive = false;
							   
						       }
						       else {
							   jQuery("#profile_content").slideUp("slow");
							   jQuery("#footer").slideUp("slow");															   
							   jQuery("#fooTxt").slideDown();
							   jQuery("#target").slideDown();
							   self.viz.dotGraph.isInteractive = true;
						       }
						   });

			   var currentDate = new Date();																					   
			   var myWidth = 950;
			   var myHeight = 50;
			   document.getElementById("main").setAttribute("width", myWidth);
			   document.getElementById("main").setAttribute("height", myHeight);

			   self.viz = newify(WatchmeVisualisation, document.getElementById("bgcanvas"),  getClientCords().width - 10, window.innerHeight - 50, 0, 86400000/2);// 12 hrs
			   setInterval("self.viz.getRecentPages(30, self.viz.type)", 9000);
		       });
