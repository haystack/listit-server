var lifestream = {
    initialize: function(canvas){
        this.canvas = canvas;
	this.now = new Date();
        this.drag = undefined;
        this.drawArray = [];
	this.endTime = new Date().valueOf();
	this.startTime = this.endTime - 604800000;
	this.data = this.getData();	
	this.mouseMargin = {x: 20, y:130 };					
	jQuery("#loadimg").show();
	//this.createStackTime('timeline');
	//jQuery('.btn:eq(0)').addClass('sel');
	jQuery('.btn:eq(2)').addClass('sel');
	this.createNodeGraph('location');
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
				       type: type
				   });

	    var mainEvtHandlers = newify(evtHandlers, this);
	    this.drawArray.push(stackTime);	    	    
	    this.draw();
	}
    },
    createStackGraph: function(type){
	this.drawArray = []; // clean the draw array 
	this.windowWidth = getClientCords().width - 50;
	this.windowHeight = 500;

	document.getElementById("main").setAttribute("width", this.windowWidth);
	document.getElementById("main").setAttribute("height", this.windowHeight);
	
	if (this.data){							
	    var stackGraph = newify(stackBarGraphFactory, this, {
					type: type,
					windowWidth: this.windowWidth,
					windowHeight: this.windowHeight,
					columnWidth:8,
					labelLeft: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', '  Friday', 'Saturday', 'Sunday'],
					labelRight: [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
				    });

	    var mainEvtHandlers = newify(evtHandlers, this);
	    this.drawArray.push(stackGraph);	    	    
	    this.draw();
	}
    },
    createNodeGraph: function(type){
	this.drawArray = []; // clean the draw array 
	this.windowWidth = getClientCords().width - 50;
	this.windowHeight = 500;

	document.getElementById("main").setAttribute("width", this.windowWidth);
	document.getElementById("main").setAttribute("height", this.windowHeight);
	
	if (this.data){							
	    var nodeGraph = newify(nodeFactory, this, {
					type: type,
					windowWidth: this.windowWidth,
					windowHeight: this.windowHeight
				    });

	    var mainEvtHandlers = newify(evtHandlers, this);
	    this.drawArray.push(nodeGraph);	    	    
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
    drawHoverTxt:function(entity, mousePos){
	var html = "<b>Label:</b> " + entity.id + "<br />"
	    + "<b>Id:</b> " + entity.id + "<br />"
	    + "<b>Date:</b> " + entity.id + "<br />"
	    + "<b>Duration:</b> " + entity.id + "<br />";
	jQuery("#hoverTxt").html(html);
	jQuery("#hoverTxt").css({"left" : mousePos.x + this.mouseMargin.x + "px", "top" : mousePos.y + this.mouseMargin.y + "px" });				
	jQuery("#hoverTxt").show();
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

	    jQuery('.btn').removeClass('sel');
	    jQuery(graph).addClass('sel');
	    
	    if (text == "timeline"){
		jQuery('#rightNav').html("");
		this.createStackTime('timeline');
	    }
	    if (text == "stacked bar graph"){
		jQuery('#rightNav').html("");
		JV3.CMS.event_store.getEventTypes().map(function(type){							   
							    jQuery('#rightNav').append("<div class=\"btn\" onClick=\"viz.createStackGraph(" + type +")\" >" + type + "</div>");							    
							});
		this.createStackGraph('www-viewed');
	    }
	    if (text == "locations"){
		this.createNodeGraph('location');
	    }
	    if (text == "explorer"){
		this.createExplorer();
	    }

	    jQuery("#loadimg").hide();	    
	}
    }
};

