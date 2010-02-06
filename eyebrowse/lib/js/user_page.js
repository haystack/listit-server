var WatchmeVisualisation = {
    initialize: function(canvas, windowWidth, windowHeight, timeZoneCorrect, zoom, username){
        this.canvas = canvas;
        this.windowWidth = windowWidth;
        this.windowHeight = windowHeight;
        this.username = username;
        this.timeZoneCorrect = timeZoneCorrect;
        this.endDate = new Date();
	this.now = new Date().valueOf();
        this.startDate = new Date(this.endDate.valueOf() - zoom);
        this.endTime = this.endDate.valueOf();
        this.startTime = this.startDate.valueOf();
        this.OGendTime = this.endDate.valueOf();
        this.OGstartTime = this.startDate.valueOf();
	this.urlID = 0;
        this.interp = zoom / 192;
        this.drag = undefined;
        this.zoom = zoom;
	this.recentID = 0;
        this.getLatestPages();
	this.getProfile(this.endTime); 
    },
    getProfile: function(endTime){
	var this_ = this;
	jQuery("#loadimg").show();
        try {
            jQuery.get("/get_profile", {
			   type: this_.username
		       }, function(data){
			   jQuery("#loadimg").hide();				
			   if (data.code == 200) {
			       this_.drawProfile(data.results[2]);
			       this_.drawTopPages(data.results[1]);
			       this_.drawGraphs(data.results[0]);
			   }
			   else {
			       //log("yaaaa!!!H!H!H!" + data.code + " ");
			   }
		       }, "json");
        } 
        catch (e) {
            console.log(e);
        }
    },
    drawProfile: function(data){
	var newData = data;	
	jQuery("#totalTime").html("<i>total time spent: </i> " +
				  timeCounterLongAbv(newData.totalTime));
	jQuery("#num").html("<i>total visits: </i>" + newData.number);
	jQuery("#avgTime").html("<i>average time spent: </i>"+ 
		timeCounterLongAbv(newData.average));					
    },
    drawTopPages: function(data){
        var this_ = this;
        var newData = data;
        var html = "<ul>";
        for (var i = 0; i < newData.length; i++) {
            var trigger = true;
            html += "<li>";
            html += "<h6><i><a href=\"http://" + newData[i][0] + "\">" + newData[i][0] + "</a></i></h6>";                
            if (newData[i][2] < 0) {
                trigger = false;
                html += "<div class=\"imgbox\">";
                html += "<img src=\"/lib/img/arrow_full_down_16.png\" />";
                html += "<i>" + newData[i][2] + "</i>";
                html += "</div>";
            }
            if (newData[i][2] > 0) {
                trigger = false;
                html += "<div class=\"imgbox\">";	
		html += "<img src=\"/lib/img/arrow_full_up_16.png\" />";                         	   
		html += "<i>" + newData[i][2] + "</i>";
		html += "</div>";
            }
            if (trigger) {
                html += "<div class=\"imgbox\">&nbsp;";
                html += "</div>";
            }
            html += "<h7>" + timeCounterLong((newData[i][1]) / 1000) + "</h7>";
            html += "</li>";
        }
	html += "</ul>";
        jQuery("#list").html(html);
    },
    drawGraphs: function(data){
	var this_ = this;

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
    },
    drawLatestPagesList: function(data){
	var this_ = this;
        var newData = data;
        var html = "";
	jQuery("#latestlist").html(" ");
	html = "<ul >";
	var num = 9; 
	if (newData.length < num){ num = newData.length; };

        for (var i = 0; i < num; i++) {
            html += "<li id=\"url" + i +  "\">";
	    if (newData[i].title){
		html += "<h6><i><a href=\"" + newData[i].url + "\">" + newData[i].title + "</a></i></h6>";
	    }
	    else{
		html += "<h6><i><a href=\"" + newData[i].url + "\">" + newData[i].url + "</a></i></h6>";
	    }				
            html += "<h7>" + timeCounterLong((this_.now - newData[i].end)/1000) + " <i>ago</i></h7>";
            html += "</li>";
	}
        html += "</ul>";
	jQuery("#latestlist").prepend(html);			
    },
    getLatestPages: function(){
        var this_ = this;
	jQuery.get("/get_latest_views", {
		       num: 40,
		       id: this_.recentID,
		       type: 'user',
		       username: this_.username
		   }, function(data){
		       if (data.code == 200) {
			   this_.drawLatestPagesList(data.results);
		       }
		       else {
			   console.log("yaaaa!!!H!H!H!" + data.code + " ");
		       }
		   }, "json");
    },
    deletePage: function(urlID, num){
	try {
	    jQuery.post("/delete_url_entry/", {
			    'ID': "" + urlID
			}, function(data){							   
			    if (data.code == 200) {
				jQuery("\#url" + num).hide("slow");
			    }
			    else {
				console.log("yaaaa!!!H!H!H!" + data.code + " ");
			    }
			}, "json");
        } 
        catch (e) {
            console.log(e);
        }			
    },
    refresh: function(startTime, endTime){
        var this_ = this;
        this_.endTime = endTime;
        this_.startTime = startTime;
        
	this.getProfile(endTime); 
    }
};
