var stackBarGraphFactory = ({
			 initialize: function(viz, params){
			     this.viz = viz;
			     this.canvas = viz.canvas;
			     this.type = params.type;
			     this.windowHeight = params.windowHeight;
			     this.windowWidth = params.windowWidth;	 
			     this.height = params.height;
			     this.mouseMargin = params.mouseMargin;
 			     this.bottomPadding = 60;
			     this.textPadding = 0;
			     this.barPadding = 7;
			     this.padding = 20;
			     this.topPadding = 0;
			     this.pIH = undefined;
			     this.trigger = undefined;
			     this.mouseVal = 0;							 
			     this.labelLeft = params.labelLeft;
			     this.labelRight = params.labelRight;					
			     this.labelLeftXpos = [];
			     this.labelRightXpos = [];
			     this.midPad = 15;
			     this.setPos(params.data);
			 },
			 draw: function(){
			     var ctx = this.canvas.getContext('2d');
			     var this_ = this;
			     ctx.clearRect(0,0,this_.windowWidth,this_.windowHeight);
			     ctx.save();
			     ctx.translate(0,0-10);
			     ctx.beginPath();
			     
			     // draw the bars
			     for (var i = 0; i < this_.da.length; i++){
				 for (var k = 0; k < this_.da[i].length; k++){
				     for (var l = 0; l < this_.da[i][k].length; l++){
					 if (isPointInPoly(this_.da[i][k][l].poly, this_.mouseVal)){
					     this_.viz.highlight = this_.da[i][k][l].url;
					     this_.trigger = true;
					     jQuery("#fooTxt").html("<a href=\"" + this_.da[i][k][l].url + "\">" +  this_.da[i][k][l].title + "</a>");
					     jQuery("#fooTxt").css({"left" : this_.mouseVal.x + this_.fooTxtX + "px", "padding": "3px", "top" : this_.mouseVal.y + 160 + "px" });	
					 }																		
					 ctx.fillStyle = this_.da[i][k][l].fillStyle;
					 ctx.fillRect(this_.da[i][k][l].xPos, this_.da[i][k][l].yPos, this_.da[i].width, this_.da[i][k][l].height);
					 if (this_.viz.highlight == this_.da[i][k][l].url){
					     ctx.fillStyle = "rgba(255,255,255,0.85)"; 
					     ctx.fillRect(this_.da[i][k][l].xPos, this_.da[i][k][l].yPos, this_.da[i].width, this_.da[i][k][l].height);
					 }								
				     }
				 }
			     }

			     ctx.closePath();
			     ctx.restore();
			     
			     
			     // draw the key
			     ctx.beginPath();
			     ctx.fillStyle = "#333333";
			     ctx.fillRect(0, this_.windowHeight - this_.bottomPadding - 4, this_.windowWidth/2 - this_.midPad, 1);
			     ctx.fillRect(this_.windowWidth/2 + this_.midPad, this_.windowHeight - this_.bottomPadding - 4, this_.windowWidth/2 - this_.midPad, 1);
			     
			     ctx.strokeStyle = "#666666";
			     ctx.font = ".7pt helvetiker";
			     ctx.fillStyle = "#666666";
			     ctx.lineWidth = 0.5;

			     // draw the labels
			     for (var i = 0; i < this_.labelLeft.length; i++){
				 ctx.fillText("" + this_.labelLeft[i], this_.labelLeftXpos[i] + this_.textPadding - 3 + (this_.labelLeftWidth - ctx.measureText(this_.labelLeft[i]).width)/2, this_.windowHeight - this_.bottomPadding + 12);
			     }

			     for (var i = 0; i < this_.labelRight.length; i++){
				 ctx.fillText("" + this_.labelRight[i], this_.labelRightXpos[i] + this_.textPadding + (this_.labelRightWidth - ctx.measureText(this_.labelRight[i]).width)/2 - 3, this_.windowHeight - this_.bottomPadding + 12);

			     }
			     
			     ctx.fillStyle = "#333333";
			     
			     // left key numbers
			     ctx.fillText("" + this_.dataMaxLeft + "  visits", 2, 10);
			     for (var i = 1; i < 3; i++) {								
				 ctx.fillText("" + Math.floor(((this_.dataMaxRight) / 3) * (3 - i)), 2, ((this_.windowHeight - this_.bottomPadding) / 3) * i + 8);
			     }
			     // right key numbers
			     ctx.fillText("" + this_.dataMaxRight + "  visits", (this_.windowWidth/2) - this_.padding + this_.midPad * 2, 10);
			     for (var i = 1; i < 3; i++) {								
				 ctx.fillText("" + Math.floor(((this_.dataMaxRight) / 3) * (3 - i)), (this_.windowWidth/2) - this_.padding + this_.midPad * 2, ((this_.windowHeight - this_.bottomPadding) / 3) * i + 8);
			     }

			     ctx.closePath();
			     
			     if (!(this_.pIH) && this_.trigger) {
				 this_.trigger = false;
				 this_.viz.highlight = "booo";
				 jQuery("#fooTxt").html("");
				 jQuery("#fooTxt").css({"padding" : "0px"});
			     }
			 },
			 mouseMove: function(params){
			     var this_ = this;
			     this_.mouseVal = {
				 x: params.mouseVal.x,
				 y: params.mouseVal.y + 6
			     };
			     this_.pIH = true;
			 },
			 mouseDown: function(){
			 },
			 mouseUp: function(params){
			 },
			 setPos: function(data){
			     var this_ = this;
			     this_.da = [];
			     var newData = data;
			     var newBar = {};
			     var leftData  = newData[0]; 
			     var rightData  = newData[1]; 
			     var lObj = [];
			     var rObj = [];
			     lObj.width = (this_.windowWidth/2)/(leftData.length)/(this_.padding/leftData.length/2);
			     rObj.width = (this_.windowWidth/2)/(rightData.length)/(this_.padding/6);

			     this_.labelLeftWidth = (this_.windowWidth/2)/leftData.length - this_.padding - this_.midPad; 
			     this_.labelRightWidth = (this_.windowWidth/2)/rightData.length - this_.padding - this_.midPad; 

			     // left graph
			     this_.dataMax = function(){
				 var maxArray = [];
				 var max = 0;
				 for (var i = 0; i < leftData.length; i++){
				     max = 0;									 
				     for (var k = 0; k < leftData[i][1].length; k++){
					 max += leftData[i][1][k][1].val;
				     }									 
				     maxArray.push(max);
				 }
				 return maxArray.max();
			     }();

			     this_.dataMaxLeft = this_.dataMax;
			     for (var i = 0; i < leftData.length; i++){
				 lObj.push([]);
				 this_.labelLeftXpos.push(((this_.windowWidth/2 - this_.midPad)/leftData.length)*i + this_.padding/2 + this_.midPad/2);
				 for (var k = 0; k < leftData[i][1].length; k++){
				     newBar = {};
				     newBar.title = leftData[i][1][k][0];									 
				     newBar.url = leftData[i][1][k][0];
				     newBar.fillStyle = "hsl("+ leftData[i][1][k][1].hue + ",100%,50%)";
				     newBar.height = -(this_.windowHeight - this_.bottomPadding) * (leftData[i][1][k][1].val / this_.dataMax);
				     newBar.xPos = ((this_.windowWidth/2 - this_.midPad)/leftData.length)*i + (this_.padding + leftData.length)/leftData.length + this_.midPad/2;
 				     newBar.yPos = function(){
					 var yPos = this_.windowHeight - this_.bottomPadding;
					 // -sum all heights in height array including this one
					 for (var p = 0; p < lObj[i].length; p++){
					     yPos += lObj[i][p].height;
					 }
					 return yPos;
				     }();
				     newBar.poly = rectToPoly({
								  xPos: newBar.xPos,
								  yPos: newBar.yPos,
								  height: newBar.height,
								  width: lObj.width
							      });
				     lObj[i].push(newBar);
				 }
			     }

			     // right graph
			     this_.dataMax = function(){
				 var maxArray = [];
				 var max = 0;
				 for (var i = 0; i < rightData.length; i++){
				     max = 0;									 
				     for (var k = 0; k < rightData[i][1].length; k++){
					 max += rightData[i][1][k][1].val;
				     }									 
				     maxArray.push(max);
				 }
				 return maxArray.max();
			     }();
			     this_.dataMaxRight = this_.dataMax;
			     for (var i = 0; i < rightData.length; i++){
				 rObj.push([]);
				 this_.labelRightXpos.push((this_.windowWidth/2 - this_.midPad) + (((this_.windowWidth/2 - this_.midPad)/rightData.length)*i) + this_.midPad*3);
				 for (var k = 0; k < rightData[i][1].length; k++){
				     newBar = {};
				     newBar.title = rightData[i][1][k][0];									 
				     newBar.url = rightData[i][1][k][0];
				     newBar.fillStyle = "hsl("+ rightData[i][1][k][1].hue + ",100%,50%)";
				     newBar.height = -(this_.windowHeight - this_.bottomPadding) * (rightData[i][1][k][1].val / this_.dataMax);
				     newBar.xPos = (this_.windowWidth/2 - this_.midPad) + (((this_.windowWidth/2 - this_.midPad)/rightData.length)*i) + this_.barPadding + (this_.padding + leftData.length)/leftData.length + this_.midPad*2;
 				     newBar.yPos = function(){
					 var yPos = this_.windowHeight - this_.bottomPadding;
					 // -sum all heights in height array including this one
					 for (var p = 0; p < rObj[i].length; p++){
					     yPos += rObj[i][p].height;
					 }
					 return yPos;
				     }();
				     newBar.poly = rectToPoly({
								  xPos: newBar.xPos,
								  yPos: newBar.yPos,
								  height: newBar.height,
								  width: rObj.width
							      });
				     rObj[i].push(newBar);
				 }
			     }
			     this_.da.push(lObj);
			     this_.da.push(rObj);
			     this_.draw();
			 }
		     });
