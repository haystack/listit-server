var lifestream = {
    initialize: function(canvas){
        this.canvas = canvas;
	this.now = new Date();
        this.drag = undefined;
        this.drawArray = [];
	this.endTime = new Date().valueOf();
	this.startTime = this.endTime - 604800000;
	this.data = this.getData();	

	jQuery("#loadimg").show();
	this.createStackTime('timeline');
	jQuery("#loadimg").hide();
    },
    getData:function(){
	var startTime = this.startTime;
	var endTime = this.endTime;
	/*
	return JV3.CMS.event_store.getEventTypes().map(
	    function(type){ return JV3.CMS.event_store.getEvents(type, [startTime, endTime]); }).filter(
		function(ent) { if (ent.length > 0) { return ent }; }); 
	 */
	return JV3.CMS.event_store.getEvents("", [startTime, endTime]);
    },
    createStackTime:function(type){
	this.drawArray = []; // clean the draw array
 	this.windowWidth = getClientCords().width - 50;
	this.windowHeight = 500; //window.innerHeight;

	document.getElementById("main").setAttribute("width", this.windowWidth);
	document.getElementById("main").setAttribute("height", this.windowHeight);

	if (this.data){							
	    var stackTime = newify(stackTimeFactory, this, {
				       windowWidth: this.windowWidth,
				       windowHeight: this.windowHeight,
				       type: type,
				       mouseMargin: {x:((getClientCords().width - this.windowWidth)/2) - 50, y:90 }
				   });

	    var mainEvtHandlers = newify(evtHandlers, this);
	    this.drawArray.push(stackTime);	    	    
	    this.draw();
	}
    },
    createStackGraph: function(type){
	this.windowWidth = getClientCords().width - 50;
	this.windowHeight = window.innerHeight - 279;
	this.drawArray = []; // clean the draw array 
	
	var HTML = "<div id=\"totalGraphKey\" style=\"color:#333; width:" + this.windowWidth/2 + "px;margin-top:15px; margin-bottom:8px;text-align:center; display: inline-block;\">top 20 each day of week</div>"
	    + "<div id=\"avgGraphKey\" style=\"color:#333; width:" + this.windowWidth/3 + "px; text-align:right; display: inline-block;\">top 20 per hour of day</div>";
	
	jQuery('#graph').html("");
	jQuery('#graph').html(HTML);
	
	document.getElementById("main").setAttribute("width", this.windowWidth);
	document.getElementById("main").setAttribute("height", this.windowHeight);
	
	if (data.results.length > 0){							
	    var graphArray = [];
	    var stackGraph = newify(stackBarGraphFactory, this_, {
					type: type,
					windowWidth: this.windowWidth,
					windowHeight: this.windowHeight,
					columnWidth:8,
					mouseMargin: {x:((getClientCords().width - this.windowWidth)/2) - 50, y:140 },
					labelLeft: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', '  Friday', 'Saturday', 'Sunday'],
					labelRight: [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
				    });

	    this.drawArray.push(stackGraph);
	    var mainEvtHandlers = newify(evtHandlers, this_);
	    this.draw();
	}
    },
    draw: function(){
        if (this.canvas !== undefined && this.canvas.getContext) {
	    var ctx = this.canvas.getContext('2d');
	    ctx.clearRect(0, 0, this.windowWidth, this.windowHeight);
	    this.drawArray.map(function(item){ item.draw(); });				  
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
    swopGraph: function(graph){
	var text = jQuery.trim(jQuery(graph).text());
	if (this.graph != text){
	    jQuery("#loadimg").show();
	    
	    this.graph = text;

	    jQuery('.graphNavBtn').removeClass('sel');
	    jQuery(graph).addClass('sel');
	    
	    if (text == "timeline"){
		this.createTimeline();
	    }
	    if (text == "by hour of day"){
		this.createDays();
	    }
	    if (text == "by day of week"){
		this.create20Days();
	    }
	    jQuery("#loadimg").hide();	    
	}
    }
};

