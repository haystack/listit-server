var WatchmeVisualisation = {
    initialize: function(zoom, canvas, width, height){
        this.endTime = new Date().valueOf();
        this.startTime = this.endTime - zoom; // 12 hours
	this.endTimeRecent = this.endTime;
	this.start = 0;
        this.now = new Date().valueOf();
        this.timeZoneCorrect = 0;
	this.newDataEnd = 0;
        this.zoom = zoom;
        this.canvas = canvas;
	this.width = width;
	this.height = height;
	this.recentID = 0;
	this.windowHeight = height;
	this.windowWidth = width;
        this.getHomepage(this.startTime, this.endTime);
        this.getRecentPages(15, 3600000);
    },
    getRecentPages: function(num){
        var this_ = this;
	this_.startTimeRecent = this_.endTimeRecent;
        this_.endTimeRecent = new Date().valueOf();
        this_.now = new Date().valueOf();
	jQuery("#loadimg").show();
	jQuery.get("/get_latest_views", {
		       num: num,
		       id: this_.recentID,
		       type: "global",
		       username: "zamiang"
		   }, function(data){
		       jQuery("#loadimg").hide();
		       if (data.code == 200) {
			   var now = new Date().valueOf();
			   data.results.map(function(site) {
			      this_.addRecentPage('#latest', site, now); 
			   });
		       }
		       else {
			   return;
		       }
		   }, "json");
    },
    addRecentPage: function(divid, page, now) {
	var name = page.title?page.title.substring(0,30):cleanupURL(page.url);

	/*  keep track of times displayed and hide old ones
	this_.recentTimesArray.unshift(newData[i].end);
	if (this_.recentTimesArray.length > num){
	    jQuery("#" + this_.recentTimesArray[num + 1]).hide();
	    this_.recentTimesArray.pop();   
	}  */

	var np = jQuery('#templates>.recentpage').clone();
	np.id = page.id;
	
	var title = np.find('.title')
	    .text(name)
	    .attr({'href':page.url});

	var time = np.find('.time')
	    .html(timeCounterClock((now - page.end)/1000) + " ago");	

	if (page.user.length > 0){
	    var user = np.find('.user')
		.html(" by <a href=\"/profile/" + page.user + 
		      "\ style=\"float:right\">" + page.user + "</a>"); 
	}
	jQuery(divid).append(np);
    },
    getHomepage: function(startTime, endTime){
        var this_ = this;
	jQuery("#loadimg").show();
	jQuery.get("/get_homepage", {
		       from: this_.startTime,
		       to: this_.endTime
		   }, function(data){
		       jQuery("#loadimg").hide();
		       if (data.code == 200) {			   this_.drawMiniGraph(data.results[1]);								   
			   /*
			    for (var i = 0; i < newData.length; i++) {
			    if (newData[i].number > 0){
			    var html = "";
			    html += "<li>";
			    html += "<h6><b><a href=\"/profile/" + newData[i].user +  "/\">" + newData[i].user + "</a></b></h6>";
			    html += "<br /><h7>" + newData[i].number + " webpages today</h7>";
			    html += "</li>";
			    jQuery("#topusers").append(html);jQuery(".listItemSmall:first").slideDown("slow");									   
			    
			    }
			    
			    }
			    */
		       }
		       else {
			   return;
			   //console.log("yaaaa!!!H!H!H!" + data.code + " ");
		       }
		   }, "json");	
    },
    drawBG: function(data, startTime, endTime, viz){
	var this_ = this;
	var newData = data;
	var newStartTime = startTime;
	var newEndTime = endTime;
	var dateArray = [];
	var zoom = this_.zoom;
	var wwwBarsArray = [];
	var hour = 1600000; // fudged a litte 1 hour = 3600000
	var bg = {};
	bg.canvas = document.getElementById("bgcanvas");
	bg.windowHeight = window.innerHeight - 50;
	bg.windowWidth = getClientCords().width - 10;
	document.getElementById("bgcanvas").setAttribute("width", bg.windowWidth - 10);
	document.getElementById("bgcanvas").setAttribute("height",bg.windowHeight - 10);
	
	for (var i = 0; i < (zoom / hour); i++) {
            var fooData = newData.filter(function(view){
					     // console.log(view.end + "    " + newEndTime + "    " + view.start);
					     if (view.end < (newEndTime - (hour * i)) && (view.start > (newEndTime - hour - (hour * i)))) {
						 return view;
					     }
					 });
            wwwBarsArray[i] = newify(statusFactory, viz, {
					 canvas: bg.canvas,
					 windowHeight: bg.windowHeight,
					 windowWidth: bg.windowWidth,
					 startTime: newEndTime - hour - (hour * i),
					 endTime: newEndTime - (hour * i),
					 xOffset: 0,
					 yOffset: 0,
					 marginTop: 25 * i + 11,
					 height: 20,
					 color: "#00ff76",
					 staticStatic: true,
					 data: fooData,
					 noHover: true
				     });				
        }
	return wwwBarsArray;
    },
    drawMiniGraph: function(data){
	var this_ = this;
	var newData = data;
	this_.drawArray = [];
	this_.statusArray = [];
	this_.graphArray = [];
	
        var wwwBars = newify(statusFactory, this_, {
				 startTime: this_.startTime,
				 endTime: this_.endTime,
				 xOffset: 0,
				 yOffset: 0,
				 marginTop: 55,
				 height: 20,
				 color: "#00ff76",
				 staticStatic: true,
				 data: newData,
				 fooTxtY: 685,
				 fooTxtX: (getClientCords().width - 700)/2
 			     });
	this_.statusArray.push(wwwBars);

	var bgStatusArray = this_.drawBG(newData, this_.startTime, this_.endTime, this_);
	this_.statusArray = this_.statusArray.concat(bgStatusArray);

        var interpNum = 100; // ALARM yea this is number of points on graph
        // fix this. it should be dynamic or a variable
        var interp = (this_.endTime - this_.startTime) / interpNum;
        var count = (Math.floor((this_.endTime - this_.startTime) / interp));
        // format the data
        var ttData = []; // total time per count
        var avgDataNum = []; // number of websites
        var dateArray = function(){
            var foo = [];
            for (var i = 0; i < count; i++) {
                foo[i] = this_.startTime + (interp * i);
                // set all arrays to 0 so to increment them
                ttData[i] = 0;
                avgDataNum[i] = 0;
            }
            return foo;
        }();
        // function to get total time on websites per time instance (ie count)
        for (var i = 0; i < newData.length; i++) {
            for (var j = 0; j < count; j++) {
                if (j >= count) {
                    if (newData[i].start.valueOf() > dateArray[j]) {
                        ttData[j] += newData[i].end - newData[i].start;
                        avgDataNum[j] += 1;
                    }
                }
                else {
                    if ((newData[i].start.valueOf() > dateArray[j]) && (newData[i].start.valueOf() < dateArray[j + 1])) {
                        ttData[j] += newData[i].end - newData[i].start;
                        avgDataNum[j] += 1;
                    }
                }
            }
        }
        
        var avgData = function(){
            var foo = [];
            for (var i = 0; i < count; i++) {
                foo[i] = (ttData[i] / (avgDataNum[i] + 1));
            }
            return foo;
        }();

        var avgTimeG = newify(lineGraphFactoryLite, {
				  canvas: this_.canvas,
				  startTime: this_.startTime,
				  endTime: this_.endTime,
				  windowHeight: this_.windowHeight,
				  windowWidth: this_.windowWidth,
				  interp: (this_.endTime - this_.startTime) / interpNum,
				  color: "#ff00ff",
				  margintop: 30,
				  topPadding: 0,
				  noKey: true,
				  fillGraph: false,
				  data: avgData
			      });
	this_.graphArray.push(avgTimeG);
        this_.drawArray.push(this_.statusArray);
        this_.drawArray.push(this_.graphArray);
        this_.isStatic = true; // does not move or make more ajax calls
        var mainEvtHandlers = newify(evtHandlers, this_);
    },
    draw: function(){
        if (this.canvas !== undefined && this.canvas.getContext) {
            var ctx = this.canvas.getContext('2d');
            ctx.clearRect(0, 0, this.windowWidth, this.windowHeight);
            for (var i = 0; i < this.drawArray.length; i++) {
                for (var k = 0; k < this.drawArray[i].length; k++) {
                    this.drawArray[i][k].draw();
                }
            }
        }
        else {
            alert('You need Safari 4 or Firefox 3+ to see this.');
        }
    },
    getCanvas: function(){
        return this.canvas;
    },
    setDrawArray: function(p){
        this.drawArray = p;
    }
};
jQuery(document).ready(function(){
			   var myWidth = 840;
			   var myHeight = 80;
			   document.getElementById("main").setAttribute("width", myWidth);
			   document.getElementById("main").setAttribute("height", myHeight);
			   self.viz = newify(WatchmeVisualisation, 43200000, document.getElementById("main"), myWidth, myHeight); //43200000 12 hrs  // possibly should be 86400000
			   //setInterval("self.viz.getRecentPages(10, 0)", 9000);
		       });
