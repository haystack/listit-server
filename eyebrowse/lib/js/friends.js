var WatchmeVisualisation = {
    initialize: function(canvas, windowWidth, windowHeight, timeZoneCorrect, endTime, zoom, data, startDate){
        this.canvas = canvas;
        this.windowWidth = windowWidth;
        this.windowHeight = windowHeight;
        this.OGwindowHeight = windowHeight;
        this.timeZoneCorrect = timeZoneCorrect;
        this.endDate = new Date(endTime);
        if (startDate) {
            this.startDate = new Date(startDate + this.timeZoneCorrect);
            zoom = this.endDate - this.startDate;
        }
        else {
            this.startDate = new Date(this.endDate.valueOf() - zoom + this.timeZoneCorrect);
        }
        this.now = new Date(new Date().valueOf() + this.timeZoneCorrect);
        this.endTime = this.endDate.valueOf();
        this.startTime = this.startDate.valueOf();
        this.OGendTime = this.endDate.valueOf();
        this.OGstartTime = this.startDate.valueOf();
        this.interp = zoom / 168;
        this.drag = undefined;
        this.zoom = zoom;
        this.marginLeft = 0;
        this.user = "{{ username }}";            
	this.friendName = "";
        this.friendTotal = "";
        this.drawArray = [];
	this.statusArray = []; // could init more of these if there are more types of graphs
	this.graphCanvas = document.getElementById("main");
        this.newData = function getViews(startTime, endTime, viz){
	    jQuery("#loadimg1").show();
            try {
                jQuery.get("/get_following_views/{{ username }}/", {
                               from: startTime,
                               to: endTime
			   }, function(data){
			       jQuery("#loadimg1").hide();
                               if (data.code == 200) {
				   document.getElementById("status").setAttribute("height", data.results.length * 32);
				   
				   viz.initLineGraph(data.results[0], startTime, endTime, viz, 0, data.results.length * 40, true);
				   for (var i = 1; i < data.results.length; i++){
				       viz.initLineGraph(data.results[i], startTime, endTime, viz, i, data.results.length * 40, false);
				   }
				   viz.setupDraw();
                               }
                               else {
				   console.log("yaaaa!!!H!H!H!" + data.code + " ");
                               }
			   }, "json");
            } 
            catch (e) {
                console.log(e);
            }
        }(this.startTime, this.endTime, this); // passing this around like a hot 
        this.getTopPages(this.endTime - zoom, this.endTime);
    },
    initLineGraph: function(newData, startTime, EndTime, viz, i, height, drawKey){
	var this_ = this;
	var friendLineGraph = []; // kinda silly to do this but makes sure names are all unique

	this_.windowHeight = this_.OGwindowHeight;
	var friendLineGraph = newify(lineGraphFactory, this_, {
					 canvas: this_.graphCanvas,
					 windowHeight: this_.windowHeight,
					 windowWidth: this_.windowWidth,
					 xOffset: 0,
					 yOffset: 0,
					 padding: 0,
					 topPadding: 10,
					 padding: this_.windowHeight - 63,
					 color: selectColorForDomain(newData.username),
					 dashed: false,
					 key: drawKey,
					 avg: false,
					 data: newData.events,
            				 label: "websites viewed",
					 maxData: this_.maxData
				     });
	
	// this is a bit nasty but it lets the 1st init set the maxData for all
	if (!this_.maxData){
	    this_.maxData = friendLineGraph.maxData;
	}

	this_.windowHeight = height;
	var wwwBars = newify(statusFactory, this_, {
				 startTime: this_.startTime,
				 endTime: this_.endTime,
				 xOffset: 0,
				 yOffset: 0,
				 padding:0,
				 marginTop: 25 * i + 18,
				 height: 20,
				 staticStatic: true,
     				 fooTxtY: 450,
				 fooTxtX: (getClientCords().width - this_.windowWidth)/2,
				 data: newData.events
			     });
	this_.statusArray.push(wwwBars);            
	var fooColor = undefined;
	fooColor = selectColorForDomain(newData.username);
	this_.friendName += "<a href=\"/profile/" + newData.username + "/\" style=\"font-weight:bold; border-bottom:3px solid " + fooColor + "\">" + newData.username + "</a><br />";
        this_.friendTotal += function(){
            var foo = 1;
            for (var j = 0; j < wwwBars.data.length; j++) {
                foo += wwwBars.data[j].end - wwwBars.data[j].start;
            }
            return timeCounterClock(foo / 1000) + "<br />";
        }();
        jQuery("#fooDate").html(this_.friendName);
        jQuery("#fooTotal").html(this_.friendTotal);
    },
    setupDraw: function(params){
	var this_ = this;
	this_.drawArray.push(this_.statusArray);

        var mainEvtHandlers = newify(evtHandlers, this_);

	this_.windowHeight = this_.OGwindowHeight;
        var mainDateSlider = newify(dateSlider, this_, {
					canvas: this_.graphCanvas,
					xOffset: 0,
					yOffset: 0,
					padding: 52
				    });
        this_.draw();
    },
    draw: function(){
        if (this.canvas !== undefined && this.canvas.getContext) {
            var ctx = this.canvas.getContext('2d');
            ctx.clearRect(0, 0, this.windowWidth, this.OGwindowHeight);
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
    },        
    drawTopPagesList: function(data){
        var this_ = this;
        var newData = data;
        var html = "<ul>";
        for (var i = 0; i < newData.length; i++) {
            var trigger = true;
            html += "<li>";
            html += "<h6><b><a href=\"http://" + newData[i][0] + "\">" + newData[i][0] + "</a></b></h6>";                
            if (newData[i][2] < 0) {
                trigger = false;
                html += "<div class=\"imgbox\">";
                html += "<img src=\"/lib/img/arrow_full_down_16.png\" />";
                html += "<b>" + newData[i][2] + "</b>";
                html += "</div>";
            }
            if (newData[i][2] > 0) {
                trigger = false;
                html += "<div class=\"imgbox\">";		   
		html += "<img src=\"/lib/img/arrow_full_up_16.png\" />";                         
		html += "<b>" + newData[i][2] + "</b>";
		html += "</div>";
            }
            if (trigger) {
                html += "<div class=\"imgbox\">&nbsp;";
                // html += "<img src=\"/lib/img/star_16.png\" />";
                html += "</div>";
            }
            html += "<h7>" + timeCounterLong((newData[i][1]) / 1000) + "</h7>";
            html += "</li>";
        }
	html += "</ul>";
        jQuery("#list").html(html);
    },
    getTopPages: function(startTime, endTime, data){
        var this_ = this;
        try {
	    jQuery("#loadimg").show();
            jQuery.get("/get_top_hosts_comparison_friends/{{ username }}/25/", {
			   first_start: startTime - 86400000,
			   first_end: endTime - 86400000,
			   second_start: startTime,
			   second_end: endTime
		       }, // this gets top 25 pages
		       function(data){
			   jQuery("#loadimg").hide();
			   if (data.code == 200) {
			       this_.drawTopPagesList(data.results);
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
    refresh: function(endTime, startTime){
        var this_ = this;
	this_.friendName = "";
        this_.friendTotal = "";
	this_.drawArray = [];

        this.newData = function getViews(startTime, endTime, viz){
	    jQuery("#loadimg").show();
            try {
                jQuery.get("/get_following_views/{{ username }}/", {
                               from: startTime,
                               to: endTime
			   }, function(data){
			       jQuery("#loadimg").hide();
                               if (data.code == 200) {
				   // starting at 1  because 0 is undefined
				   for (var i = 0; i < data.results.length; i++){
				       viz.initLineGraph(data.results[i], startTime, endTime, viz, i);
				   }
				   this_.setupDraw();
                               }
                               else {
				   console.log("yaaaa!!!H!H!H!" + data.code + " ");
                               }
			   }, "json");
            } 
            catch (e) {
                console.log(e);
            }
        }(startTime, endTime, this_); // passing this around like a hot tomalie       
    }
};


jQuery(document).ready(function(){
			   // init the datepicker
			   var currentDate = new Date();
			   jQuery("#datepicker").val(currentDate.format('mm/dd/yyyy'));
			   
			   jQuery('#datepicker').DatePicker({
								format: 'm/d/Y',
								date: jQuery('#datepicker').val(),
								current: jQuery('#datepicker').val(),
								starts: 1,
								position: 'bottom',
								current: '2009-07-29',
								
								onBeforeShow: function(){
								    jQuery('#datepicker').DatePickerSetDate(jQuery('#datepicker').val(), true);
								},
								onChange: function(formated, dates){
								    var fooDate = jQuery.datepicker.formatDate("@", new Date(jQuery('#datepicker').DatePickerGetDate(true)));
								    if (fooDate > new Date().valueOf()) {
									fooDate = new Date().valueOf();
									jQuery('#datepicker').val(currentDate.format('mm/dd/yyyy'));
									jQuery("#messageSent").show("slow");
								    }
								    else {
									jQuery('#datepicker').val(formated);
									self.viz.refresh(parseInt(fooDate), parseInt(fooDate) - self.viz.zoom), jQuery("#messageSent").hide("slow");
								    }
								    jQuery('#datepicker').DatePickerHide();
								    
								}
							    });
			   
			   jQuery("#datepickertop").val(currentDate.format('mm/dd/yyyy'));
			   
			   jQuery('#datepickertop').DatePicker({
								   format: 'm/d/Y',
								   date: jQuery('#datepickertop').val(),
								   current: jQuery('#datepickertop').val(),
								   starts: 1,
								   position: 'bottom',
								   current: '2009-07-29',
								   
								   onBeforeShow: function(){
								       jQuery('#datepickertop').DatePickerSetDate(jQuery('#datepicker').val(), true);
								   },
								   onChange: function(formated, dates){
								       var fooDate = jQuery.datepicker.formatDate("@", new Date(jQuery('#datepickertop').DatePickerGetDate(true)));
								       if (fooDate > new Date().valueOf()) {
									   fooDate = new Date().valueOf();
									   jQuery('#datepickertop').val(currentDate.format('mm/dd/yyyy'));
									   jQuery("#messageSent").show("slow");
								       }
								       else {
									   jQuery('#datepickertop').val(formated);
									   self.viz.refresh(parseInt(fooDate), parseInt(fooDate) - self.viz.zoom), jQuery("#messageSent").hide("slow");
								       }
								       jQuery('#datepickertop').DatePickerHide();
								       
								   }
							       });


			   
			   var myWidth = undefined;
			   var myHeight = undefined;
			   
			   myWidth = 700;
			   myHeight = 350;
			   
			   document.getElementById("main").setAttribute("width", myWidth);
			   document.getElementById("main").setAttribute("height", myHeight);
			   document.getElementById("status").setAttribute("width", myWidth);
			   document.getElementById("status").setAttribute("height", myHeight);
			   
			   self.viz = newify(WatchmeVisualisation, document.getElementById("status"), myWidth, myHeight, 0, currentDate.valueOf(), 604800000); // 1 week
		       });
