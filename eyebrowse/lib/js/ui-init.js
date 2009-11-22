var lifestream = {
    initialize: function(canvas){
        this.canvas = canvas;
	this.now = new Date();
        this.drag = undefined;
        this.drawArray = [];
	this.endTime = new Date().valueOf();
	this.startTime = this.endTime - (604800000 * 4);
	this.data = this.getData();	
	this.numberNodes = 5;
	this.mouseMargin = {x: 14, y:170 };					
	jQuery("#loadimg").show();
	//this.createStackTime('timeline');
	//jQuery('.btn:eq(0)').addClass('sel');
	jQuery('.btn:eq(2)').addClass('sel');
	this.createNodeGraph('location');

	JV3.CMS.event_store.getEventTypes().map(function(type){					
						    jQuery('#rightNav').append("<div class=\"btn\" onClick=\"viz.nodeGraph.changeMode('" + type +"')\" >" + type + "</div>");			    
						});
	jQuery("#loadimg").hide();
    },
    getData:function(){
	/*
	 return JV3.CMS.event_store.getEventTypes().map(
	 function(type){ return JV3.CMS.event_store.getEvents(type, [startTime, endTime]); }).filter(
	 function(ent) { if (ent.length > 0) { return ent }; }); 
	 */
	if (JV3.__debug__data === undefined) {
	    JV3.__debug__data = JV3.CMS.event_store.getEvents("", [this.startTime, this.endTime]);
	}
	return JV3.__debug__data;
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
					labelLeft: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', '  Friday', 'Saturday'],
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
	this.windowHeight = 550;

	document.getElementById("main").setAttribute("width", this.windowWidth);
	document.getElementById("main").setAttribute("height", this.windowHeight);
	
	if (this.data){							
	    this.nodeGraph = newify(nodeFactory, this, {
					type: type,
					currentLocation: currentLocation, // TODO NEED TO FIND OUT HOW TO GET THIS
					numNodes: this.numberNodes,
					windowWidth: this.windowWidth,
					windowHeight: this.windowHeight
				    });

	    var mainEvtHandlers = newify(evtHandlers, this);
	    this.drawArray.push(this.nodeGraph);	    	    
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
	if (!entity.id){
	    jQuery("#hoverTxt").hide();
	    return;	    
	}
	if (!(this.selectedEnt == entity.id)){
	    this.selectedEnt = entity.id;
	    var html = "<div class=\"hoverHeader\"><b> " + entity.id + "</b><br /></div>";
	    if (entity.commonenglish) {html += "<b>Type: </b>" + entity.commonenglish + "<br />";};
	    if (entity.host) {html += "<b>Host: </b>" + entity.host + "<br />";};
	    if (entity.firstspotted) {html += "<b>First Spotted: </b>" + new Date(entity.firstspotted).format('dddd, mmmm dd h:MM TT') + "<br />";};
	    if (entity.total) { html += "<b>Total Time: </b> " + timeCounterLong(entity.total/1000) + "<br />";}
	    if (entity.topHours) { html += "<b>Top Hours Of Day: </b>" + entity.topHours.join(', ') + "<br />";}
	    if (entity.topDOW) { html += "<b>Top Day of the Week: </b>" + entity.topDOW.join(', ') + "<br />";}
	    if (entity.topWWW) { 
		html += "<b>Top Domains: </b><br /><div style='margin-left:20px; font-size:10.5px;'";
		entity.topWWW.map(function(www){				     
				      html += "<div class=\"hoversubtext\">" + www[0] + "</div> " + timeCounterLong(www[1]/1000) + "<br />";
				  });	    
		html += "</div>";
	    }
	    jQuery("#hoverTxt").html(html);	    
	}
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
							    jQuery('#rightNav').append("<div class=\"btn\" onClick=\"viz.createStackGraph('" + type +"')\" >" + type + "</div>");			    
							});
		this.createStackGraph('www-viewed');
	    }
	    if (text == "locations"){
		jQuery('#rightNav').html("");
		JV3.CMS.event_store.getEventTypes().map(function(type){					
							    jQuery('#rightNav').append("<div class=\"btn\" onClick=\"viz.nodeGraph.changeMode('" + type +"')\" >" + type + "</div>");			    
							});

		this.createNodeGraph('location');
	    }
	    if (text == "explorer"){
		this.createExplorer();
	    }

	    jQuery("#loadimg").hide();	    
	}
    }
};
