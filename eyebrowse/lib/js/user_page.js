var evtHandlers = ({
		       mouse: {
			   x: 0,
			   y: 0
		       },
		       initialize: function(viz){
			   this.viz = viz;
			   this.body = jQuery('body'); 
			   this.canvas = jQuery(viz.getCanvas());
			   this.dragBegin = {x:0,y:0};
			   this._ev_handlers();
		       },
		       _ev_handlers: function(){
			   var canvas = this.canvas;
			   var this_ = this;

			   jQuery(this.body).mousemove(function(evt){
							   var position = this_.canvas.position();
							   
							   this_.mouse = {
							       x: evt.clientX - position.left,
							       y: evt.clientY - position.top + jQuery(window).scrollTop()
							   };

							   this_.viz.drawArray.map(function(item) { item.mouseMove(this_.mouse); });
							   this_.viz.draw();
						       });
		       }
		   });


var stackBarGraph = ({
			 initialize: function(viz, params){
			     this.viz = viz;
			     this.canvas = viz.canvas;
			     this.windowHeight = params.windowHeight;
			     this.windowWidth = params.windowWidth;	 
			     this.height = params.height;
 			     this.bottomPadding = params.bottomPadding;
			     this.textPadding = params.textPadding;
			     this.barPadding = 7;//params.barPadding;
			     this.padding = 20;
			     this.topPadding = 0;
			     this.pIH = undefined;
			     this.trigger = undefined;
			     this.mouseVal = 0;							 
			     this.labelLeft = params.labelLeft;
			     this.labelRight = params.labelRight;	
			     this.minData = 0;
			     this.dataMax = 0;
			     this.labelLeftXpos = [];
			     this.labelRightXpos = [];
			     this.midPad = 15;
			     this.setPos(params.data);
			     this.hoverTopMargin = jQuery(this.canvas).position().top;
			     this.hoverLeftMargin = jQuery(this.canvas).position().left;
			     if (!(this.fooTxtY)){
				 this.fooTxtY = 0;
			     }
			     if (!(this.fooTxtX)){
				 this.fooTxtX = 0;
			     }
			 },
			 draw: function(){
			     var ctx = this.canvas.getContext('2d');
			     var this_ = this;
			     ctx.clearRect(0,0,this.windowWidth, this.windowHeight);
			     ctx.save();
			     ctx.translate(0,0-10);
			     ctx.beginPath();
			     
			     // draw the bars
			     this.da.map(function(graph){
					     graph.map(function(column){
							   column.map(function(bar){
									  if (isPointInPoly(bar.poly, this_.mouseVal)){
									      this_.drawHoverText(bar, this_.mouseVal);
									  }																		
									  ctx.fillStyle = bar.fillStyle;
									  ctx.fillRect(bar.xPos, bar.yPos, graph.width, bar.height);
									  if (this_.viz.highlight == bar.url){
									      ctx.fillStyle = "rgba(255,255,255,0.85)"; 
									      ctx.fillRect(bar.xPos, bar.yPos, graph.width, bar.height);
									  }								
								      });							   
						       });
					 });
			     ctx.closePath();
			     ctx.restore();
			     
			     
			     // draw the key
			     ctx.beginPath();
			     ctx.fillStyle = "#333333";
			     ctx.fillRect(0, this.windowHeight - this.bottomPadding - 4, this.windowWidth/2 - this.midPad, 1);
			     ctx.fillRect(this.windowWidth/2 + this.midPad, this.windowHeight - this.bottomPadding - 4, this.windowWidth/2 - this.midPad, 1);
			     
			     ctx.strokeStyle = "#666666";
			     ctx.font = "8pt Arial";
			     ctx.fillStyle = "#666666";
			     ctx.lineWidth = 0.5;

			     // draw the labels
			     for (var i = 0; i < this.labelLeft.length; i++){
				 ctx.fillText("" + this.labelLeft[i], this.labelLeftXpos[i] + this.textPadding - 3 + (this.labelLeftWidth - ctx.measureText(this.labelLeft[i]).width)/2, this.windowHeight - this.bottomPadding + 12);
			     }

			     for (var i = 0; i < this.labelRight.length; i++){
				 ctx.fillText("" + this.labelRight[i], this.labelRightXpos[i] + this.textPadding + (this.labelRightWidth - ctx.measureText(this.labelRight[i]).width)/2 - 3, this.windowHeight - this.bottomPadding + 12);
			     }
			     
			     ctx.fillStyle = "#333333";
			     
			     // left key numbers
			     ctx.fillText("" + this.dataMaxLeft + "  visits", 2, 10);
			     for (var i = 1; i < 3; i++) {								
				 ctx.fillText("" + Math.floor(((this.dataMaxRight) / 3) * (3 - i)), 2, ((this.windowHeight - this.bottomPadding) / 3) * i + 8);
			     }
			     // right key numbers
			     ctx.fillText("" + this.dataMaxRight + "  visits", (this.windowWidth/2) - this.padding + this.midPad * 2, 10);
			     for (var i = 1; i < 3; i++) {								
				 ctx.fillText("" + Math.floor(((this.dataMaxRight) / 3) * (3 - i)), (this.windowWidth/2) - this.padding + this.midPad * 2, ((this.windowHeight - this.bottomPadding) / 3) * i + 8);
			     }

			     ctx.closePath();
			     
			     if (!(this.pIH) && this.trigger) {
				 this.trigger = false;
				 this.viz.highlight = "booo";
				 jQuery("#hoverTxt").hide();
			     }
			 },
			 mouseMove: function(params){
			     var this_ = this;
			     this_.mouseVal = {
				 x: params.x,
				 y: params.y + 6
			     };
			     this_.pIH = true;
			 },
			 drawHoverText:function(page, mousePos){
			     this.viz.highlight = page.url;
			     this.trigger = true;

			     
			     var name = page.title?page.title.substring(0,30):cleanupURL(page.url);
			     jQuery("#hoverTxt").html("<a href=\"" + page.url + "\">" +  name + "</a>");
			     jQuery("#hoverTxt").css({"left" : mousePos.x + this.hoverLeftMargin - 5 + "px", "top" : mousePos.y + this.hoverTopMargin - 20 + "px" });				     
			     jQuery("#hoverTxt").show();
			 },
			 getDataMax: function(data){
			     var maxArray = [];
			     var max = 0;
			     data.map(function(dta){
					  max = 0;									 
					  dta[1].map(function(d){ max += d[1].val; });
					  maxArray.push(max);						 
				      });
			     return Math.max.apply(undefined, maxArray);			    
			 },
			 setPos: function(data){
			     var this_ = this;
			     var tmp = {};
			     var leftData  = data[0]; 
			     var rightData  = data[1]; 
			     var lObj = [];
			     var rObj = [];
			     lObj.width = (this.windowWidth/2)/(leftData.length)/(this.padding/leftData.length/2);
			     rObj.width = (this.windowWidth/2)/(rightData.length)/(this.padding/6);
			     this.da = [];
			     this.labelLeftWidth = (this.windowWidth/2)/leftData.length - this.padding - this.midPad; 
			     this.labelRightWidth = (this.windowWidth/2)/rightData.length - this.padding - this.midPad; 
			     
			     // THIS CODE IS OLLLLLLLLLLLLLLD and terrible -- sorry

			     // left graph
			     this.dataMax = this.getDataMax(leftData);
			     this.dataMaxLeft = this.dataMax;
			     for (var i = 0; i < leftData.length; i++){
				 lObj.push([]);
				 this_.labelLeftXpos.push(((this_.windowWidth/2 - this_.midPad)/leftData.length)*i + this_.padding/2 + this_.midPad/2);
				 for (var k = 0; k < leftData[i][1].length; k++){									 
				     tmp = {};
				     tmp.title = leftData[i][1][k][0];									 
				     tmp.url = leftData[i][1][k][0];
				     tmp.fillStyle = "hsl("+ leftData[i][1][k][1].hue + ",100%,50%)";
				     tmp.height = -(this_.windowHeight - this_.bottomPadding) * (leftData[i][1][k][1].val / this_.dataMax);
				     tmp.xPos = ((this_.windowWidth/2 - this_.midPad)/leftData.length)*i + (this_.padding + leftData.length)/leftData.length + this_.midPad/2;
 				     tmp.yPos = function(){
					 var yPos = this_.windowHeight - this_.bottomPadding;
					 // -sum all heights in height array including this one
					 for (var p = 0; p < lObj[i].length; p++){
					     yPos += lObj[i][p].height;
					 }
					 return yPos;
				     }();
				     tmp.poly = rectToPoly({
							       xPos: tmp.xPos,
							       yPos: tmp.yPos,
							       height: tmp.height,
							       width: lObj.width
							   });
				     lObj[i].push(tmp);
				 }
			     }
			     
			     this.dataMax = this.getDataMax(rightData);
			     this.dataMaxRight = this.dataMax;
			     for (var i = 0; i < rightData.length; i++){
				 rObj.push([]);
				 this_.labelRightXpos.push((this_.windowWidth/2 - this_.midPad) + (((this_.windowWidth/2 - this_.midPad)/rightData.length)*i) + this_.midPad*3);
				 for (var k = 0; k < rightData[i][1].length; k++){
				     tmp = {};
				     tmp.title = rightData[i][1][k][0];									 
				     tmp.url = rightData[i][1][k][0];
				     tmp.fillStyle = "hsl("+ rightData[i][1][k][1].hue + ",100%,50%)";
				     tmp.height = -(this_.windowHeight - this_.bottomPadding) * (rightData[i][1][k][1].val / this_.dataMax);
				     tmp.xPos = (this_.windowWidth/2 - this_.midPad) + (((this_.windowWidth/2 - this_.midPad)/rightData.length)*i) + this_.barPadding + (this_.padding + leftData.length)/leftData.length + this_.midPad*2;
 				     tmp.yPos = function(){
					 var yPos = this_.windowHeight - this_.bottomPadding;
					 // -sum all heights in height array including this one
					 for (var p = 0; p < rObj[i].length; p++){
					     yPos += rObj[i][p].height;
					 }
					 return yPos;
				     }();
				     tmp.poly = rectToPoly({
								  xPos: tmp.xPos,
								  yPos: tmp.yPos,
								  height: tmp.height,
								  width: rObj.width
							      });
				     rObj[i].push(tmp);
				 }
			     }
			     this.da.push(lObj);
			     this.da.push(rObj);
			     this.draw();
			 }
		     });


var UserPage = {
    initialize: function(canvas, windowWidth, windowHeight, username){
        this.canvas = canvas;
        this.windowWidth = windowWidth;
        this.windowHeight = windowHeight;
        this.username = username;
	this.now = new Date().valueOf();
        this.getLatestPages();
	this.getProfile(); 
    },
    getProfile: function(){
	var this_ = this;
	jQuery("#mainloading").show();
        jQuery.get("/get_profile", {
		       username: this_.username
		   }, function(data){
		       jQuery("#mainloading").hide();				
		       if (data.code == 200) {
			   this_.drawProfile(data.results[1]);
			   this_.drawGraph(data.results[0]);
		       }
		       else {
			   //log("yaaaa!!!H!H!H!" + data.code + " ");
		       }
		   }, "json");
    },
    drawProfile: function(data){
	jQuery("#totalTime").html("<i>total time spent: </i> " + timeCounterLongAbv(data.totalTime));
	jQuery("#num").html("<i>total visits: </i>" + data.number);
	jQuery("#avgTime").html("<i>average time spent: </i>"+ timeCounterLongAbv(data.average));					
    },
    drawGraph: function(data){
	var this_ = this;
	this.drawArray = [];
	var stackGraph = newify(stackBarGraph, this, {
				    windowWidth: this.windowWidth,
				    windowHeight: this.windowHeight,
				    bottomPadding:30,
				    columnWidth:8,
				    barPadding:0,
				    textPadding:0,
				    data: data,
				    labelLeft: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', '  Friday', 'Saturday', 'Sunday'],
				    labelRight: [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
				});
	this.drawArray.push(stackGraph);	
	this.mainEvtHandlers = newify(evtHandlers, this);	
	this.draw();
    },
    draw: function(){
	this.drawArray.map(function(graph) { graph.draw(); });	
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
			   data.results.map(function(item) { this_.addLatestPage('#latestlist', item, this_.now); });
		       }
		       else {
			   console.log("yaaaa!!!H!H!H!" + data.code + " ");
		       }
		   }, "json");
    },
    addLatestPage: function(divid, page, now) {	
	var name = page.title?page.title.substring(0,30):cleanupURL(page.url);
	var np = jQuery('#templates>.recentpage').clone();

	np.id = page.id;	

	np.find('.colorbox').css({'background-color': 'hsl(' + page.hue + ',100%, 50%)'});

	var title = np.find('.title')
	    .text(name)
	    .attr({'href':page.url});

	var time = np.find('.time')
	    .html(timeCounterClock((now - page.end)/1000) + " ago");	

	jQuery(divid).append(np);
    },
    deletePage: function(urlID, num){
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
    },
    getCanvas: function(){ return this.canvas;  }
};


