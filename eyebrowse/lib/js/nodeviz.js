var nodeFactory = ({
                       mouse: {
			   x: 0,
			   y: 0
                       },
                       initialize: function(canvas, params){
			   this.canvas = canvas;
			   this.data = params.data;
			   this.color = params.color;
			   this.maxR = 30; // max and min size of the node
			   this.size = this.maxR * (((params.timeSpent - params.minTimeSpent) / (params.maxTimeSpent - params.minTimeSpent)) + 2);
			   this.maxLat = params.latMax;
			   this.maxLong = params.longMax;
			   this.minLat = params.latMin;
			   this.minLong = params.longMin;
			   this.xPos = (windowWidth - this.size - 155) * ((params.long - this.minLong) / (this.maxLong - this.minLong)) + this.size + 55;
			   // this is reveresed, higher lat value = lower on page
			   this.yPos = (windowHeight - this.size - 150) * ((params.lat - this.minLat) / (this.maxLat - this.minLat)) + topNavPadding + this.size + 10;
			   this.poly = [{
					    x: this.size * Math.cos(0) + this.xPos,
					    y: this.size * Math.sin(0) + this.yPos
					}, {
					    x: this.size * Math.cos(45) + this.xPos,
					    y: this.size * Math.sin(45) + this.yPos
					}, {
					    x: this.size * Math.cos(90) + this.xPos,
					    y: this.size * Math.sin(90) + this.yPos
					}, {
					    x: this.size * Math.cos(135) + this.xPos,
					    y: this.size * Math.sin(135) + this.yPos
					}, {
					    x: this.size * Math.cos(180) + this.xPos,
					    y: this.size * Math.sin(180) + this.yPos
					}, {
					    x: this.size * Math.cos(225) + this.xPos,
					    y: this.size * Math.sin(225) + this.yPos
					}, {
					    x: this.size * Math.cos(270) + this.xPos,
					    y: this.size * Math.sin(270) + this.yPos
					}, {
					    x: this.size * Math.cos(315) + this.xPos,
					    y: this.size * Math.sin(315) + this.yPos
					}, {
					    x: this.size * Math.cos(0) + this.xPos,
					    y: this.size * Math.sin(0) + this.yPos
					}];
			   this._ev_handlers();
                       },
		      mouseMove: function(params){
			  this.pIH = isPointInPoly(this.poly, params.mouseVal);
		      },
		      mouseDown: function(params){			  
			  if (this.pIH) {
			      selectedNode = this.name;
			      // might not be the fastest solution
			      for (var j = 0; j < nodeNameArray.length; j++) {
				  mapNav.tabIS[j] = false;
			      }
			      mapNav.tabIS[this.i] = true;
			      swopHTML(this.i);
			  }			  
		      },
		      mouseUp: function(){
			  jQuery("#fooTxt").html("");
			  this.draw();		      
                       },
                       draw: function(){
			   var ctx = this.canvas.getContext('2d');
			   var this_ = this;

			   // draw node lines
			   ctx.lineWidth = 0.5;
			   ctx.strokeStyle = this.color;
			   ctx.fillStyle = this.color;
			   
			   for (var i = 0; i < mapNav.checkBoxx.length; i++) {
                               if (mapNav.checkIS[i]) {
				   drawNodeConnection(document.getElementById("map"), {
							  i: i,
							  name: this_.name,
							  connection: this_.connections[i],
							  xPos: this_.xPos,
							  yPos: this_.yPos,
							  size: this_.size,
							  color: this_.color
						      });
                               }
			   }
			   if (selectedNode === this_.name) {
                               ctx.lineWidth = 3;
			   }
			   ctx.beginPath();
			   ctx.arc(this_.xPos, this_.yPos, this_.size, 0, Math.PI * 2, true);
			   ctx.stroke();
			   ctx.closePath();
			   
                       }
		   });

function drawNodeConnection(canvas, params){
    this.canvas = canvas;
    var ctx = this.canvas.getContext('2d');
    this.nodeName = params.name;
    this.checkBox = checkBoxNames[params.i];
    this.xPos = params.xPos;
    this.yPos = params.yPos;
    this.size = params.size;
    this.color = params.color;
    var thisNodeData = undefined;
    var connection = params.connection;
    var bezierArray = [];
    var testPaths = [], spacing = 2, firstDistance = 0, drawFirst = false, ctx, animating = false, pointerX = pointerY = 0, canvasOffset;
    
    var theta = 0;
    var innerTheta = 0;
    var xFoo = 0;
    var yFoo = 0;

    // check to see if current node is selected node
    if (selectedNode === this.nodeName) {
        for (var k = 0; k < connection.length; k++) {
            theta = (k) / (connection.length) * 360;
            xFoo = this.size * Math.cos(theta) + this.xPos;
            yFoo = this.size * Math.sin(theta) + this.yPos;
            // run through each node, then run through the friends in that node
            for (var y = 0; y < nodeNameArray.length; y++) {
                // there's got to be a better way of doing this
                if (this.checkBox === "friends") {
                    thisNodeData = nodeData[y].name.friends;
                }
                if (this.checkBox === "projects") {
                    thisNodeData = nodeData[y].name.projects;
                }
                if (this.checkBox === "events") {
                    thisNodeData = nodeData[y].name.events;
                }
                for (var q = 0; q < thisNodeData.length; q++) {
                    if (connection[k].name === thisNodeData[q].name) {
                        innerTheta = [q] / (thisNodeData.length) * 360;
                        ctx.beginPath();
                        ctx.fillStyle = this.color;
                        ctx.arc(nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.xPos, nodeData[y].name.size * Math.sin(innerTheta) + nodeData[y].name.yPos, 4, 0, Math.PI * 2, true);
                        ctx.fill();
                        ctx.closePath();
                        if (xFoo < (nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.xPos)) {
                            bezierArray.push({
						 "point": [{
							       x: xFoo,
							       y: yFoo
							   }, {
							       x: (xFoo - nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.xPos) * 0.3,
							       y: (yFoo - nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.yPos) * 0.2 
							   }, {
							       x: (xFoo - nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.xPos) * 0.7,
							       y: (yFoo - nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.yPos) * 0.7 
							   }, {
							       x: nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.xPos,
							       y: nodeData[y].name.size * Math.sin(innerTheta) + nodeData[y].name.yPos
							   }]
                                             });
                        }
                        
                        
                        if (xFoo > (nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.xPos)) {
                            bezierArray.push({
						 "point": [{
							       x: xFoo,
							       y: yFoo
							   }, {
							       x: (xFoo - nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.xPos) * 0.3,
							       y: (yFoo - nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.yPos) * 0.2
							   }, {
							       x: (xFoo - nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.xPos) * 0.7,
							       y: (yFoo - nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.yPos) * 0.7 
							   }, {
							       x: nodeData[y].name.size * Math.cos(innerTheta) + nodeData[y].name.xPos,
							       y: nodeData[y].name.size * Math.sin(innerTheta) + nodeData[y].name.yPos
							   }]
                                             });
                        }
                    }
                }
            }
        }
        
        // draw the paths
        // this is within the "if (selectedNode === this.nodeName)" statement
        function newTestPaths(){
            var fooBezier = [];
            for (var i = 0; i < bezierArray.length; i++) {
                fooBezier.push(new Bezier([new Point(bezierArray[i].point[0].x, bezierArray[i].point[0].y), new Point(bezierArray[i].point[1].x, bezierArray[i].point[1].y), new Point(bezierArray[i].point[2].x, bezierArray[i].point[2].y), new Point(bezierArray[i].point[3].x, bezierArray[i].point[3].y)]));
            }
            return [new Path(fooBezier)];
        }
        
        testPaths[0] = newTestPaths();
        
        ctx.beginPath();
        ctx.lineWidth = 0.8;
        ctx.strokeStyle = this.color;
        testPaths.each(function(paths){
                           paths.each(function(path){
					  path.makeDashedPath(ctx, spacing, firstDistance);
				      });
                       });
        ctx.stroke();
        ctx.closePath();
    }
}
