var nodeFactory = ({
                       initialize: function(viz, params){
			   this.viz = viz;
			   this.canvas = this.viz.canvas;
			   this.type = params.type;
			   this.displayType = "clock";
			   this.windowHeight = params.windowHeight;
			   this.windowWidth = params.windowWidth;	 
			   this.maxR = 20; 
			   this.minR = 10;
			   this.maxBarH = 15;
			   this.barWidth = 15;
			   this.maxLineWidth = 15; 
			   this.objPadding = 20;
			   this.maxHourData = 0;			   
			   this.maxWeekData = 0;			   
			   this.setPosition('grid');
			   this.barLabels = ['S', 'M', 'T', 'W', 'R', 'F', 'Sa'];
			   this.setupData();
			   this.draw();
                       },
                       draw: function(){
			   var ctx = this.canvas.getContext('2d');
			   var this_ = this;
			   var index = 0;
			   var xPos = 0;
			   var yPos = 0;
			   var maxWeekData = 0;
			   var color = "";

			   // draw node lines
			   ctx.lineWidth = 0.5;
			   ctx.strokeStyle = "#333333";
			   this.data.map(function(dta){
					     ctx.font = "800 9pt Arial";
					     ctx.fillStyle = "#333333";
					     ctx.fillText("" + dta.name, dta.xPos - (ctx.measureText(dta.name).width/2), dta.yPos - 2*(this_.maxR + this_.minR) - this_.objPadding);

					     // draw the circles
					     ctx.fillStyle = dta.color;
					     ctx.lineWidth = 0.5;
					     ctx.beginPath();
					     ctx.arc(dta.xPos, dta.yPos, dta.size, 0, Math.PI * 2, true);
					     ctx.fill();					     
					     ctx.stroke();
					     ctx.closePath();
					     

					     if (this_.displayType == 'clock'){
						 

					     // draw bar graphs under the circles
					     index = 0;
					     //maxWeekData = Math.max.apply(undefined, dta.weekPts.concat());
					     //if (!maxWeekData) { maxWeekData = 1;};
					     ctx.font = "400 7pt Arial";
					     dta.weekPts.map(function(hr){
								 xPos = dta.xPos - (dta.weekPts.length * this_.barWidth)/2 + (this_.barWidth * index);
								 yPos = dta.yPos +  2*(this_.maxR + this_.minR) + this_.objPadding*2;
								 color = 'hsl(' + Math.floor((130 * (Math.abs(hr)/this_.maxWeekData)) + 180) + ", 100%, 50%)";
								 ctx.fillStyle = color;
								 ctx.fillRect(xPos, yPos, this_.barWidth, -this_.maxBarH*(hr/this_.maxWeekData));
								 ctx.fillStyle = "#333333";
								 ctx.fillText(this_.barLabels[index], xPos + 3, yPos + 15);
								 index += 1;
							     });
					     // draw the mini circles n such  // 30
					     index = 0;
					     dta.hrPts.map(function(hr){
							       ctx.beginPath();
							       if (index > 11) { ctx.strokeStyle = 'rgba(236,0,140, 0.7)'; } else { ctx.strokeStyle =  'rgb(0,174,239)'; }

							       ctx.lineWidth = this_.maxLineWidth * (hr/this_.maxHourData);
							       ctx.arc(dta.xPos, dta.yPos, 2*(this_.maxR + this_.minR), degToRadMinusNinty(30 * index), degToRadMinusNinty(30 * index + 30), false);
							       ctx.stroke();
							       ctx.closePath();
					     		       index += 1;
							   });

					     // draw the hover state
					     if (this_.hoverID == dta.entity.id) {
						 ctx.fillStyle = "#333333";
						 ctx.strokeStyle = "#333333";
						 ctx.lineWidth = 0.6;
						 ctx.font = "800 9pt Arial";

						 ctx.fillText("12", dta.xPos - (ctx.measureText('12').width/2), dta.yPos - 2*(this_.maxR + this_.minR) - this_.objPadding/4);
						 ctx.fillText("9", dta.xPos - (ctx.measureText('9').width/2) - 2*(this_.maxR + this_.minR), dta.yPos);
						 ctx.fillText("6", dta.xPos - (ctx.measureText('6').width/2) + 2*(this_.maxR + this_.minR), dta.yPos);
						 ctx.fillText("3", dta.xPos - (ctx.measureText('3').width/2), dta.yPos + 2*(this_.maxR + this_.minR));

						 for (var i = 0; i < 12; i++){						    
						     ctx.beginPath();
						     ctx.moveTo(dta.xPos + ((this_.maxR*2 + 5) * Math.cos(degToRad(i * 30))), dta.yPos - (((this_.maxR*2 + 5)) * Math.sin(degToRad(i * 30))));
						     ctx.lineTo((dta.xPos + (this_.maxR*2) * Math.cos(degToRad(i * 30))), dta.yPos - (this_.maxR*2 * Math.sin(degToRad(i * 30))));
						     ctx.stroke();	
						     ctx.closePath();
						 }
					     }
					     }


					 });			   
                       },
		       setupData: function(){
			   var this_ = this;
			   var weekday = 0;
			   var hour = 0;			   
			   var index = undefined;
			   var timeSpent = 0;
			   var obj = {};
			   var size = 0;
			   var data = {};
			   var start = 0;
			   var end = 0;
			   
			   this.viz.data.filter(
			       function(vizData){ return vizData.type == this_.type; }).map(
				   function(dta){
				       if (!dta.entity) { return; };
				       start = dta.start.valueOf();
				       end = dta.end.valueOf();
				       
				       if (!data[dta.entity.id]) { 
					   data[dta.entity.id] = {
					       id: dta.entity.id,
					       ent: dta.entity,
					       total: 0,
					       hrPts: JV3.plumutil.intRange(0,24).map(function(){return 0;}),
					       weekPts: JV3.plumutil.intRange(0,7).map(function(){return 0;}),
					       topPages: {},
					       start: [start],  
					       end: [end]
					   };
				       } else {
					   data[dta.entity.id].start.push(start);
					   data[dta.entity.id].end.push(end);
				       }
				       
				       data[dta.entity.id].total += end - start;
				   });

			   
			   var top5 = JV3.plumutil.objVals(data);
			   top5 = top5.sort(function(a,b) { return data[b.id].total - data[a.id].total; }).slice(0,5);

			   top5.map(function(obj){
					for (var i = 0; i < obj.end.length; i++){
					    weekday = new Date(obj.end[i]).getDay();	  
					    if (obj.weekPts[weekday]){
						obj.weekPts[weekday] += obj.end[i] - obj.start[i];
					    } else { 
						obj.weekPts[weekday] = obj.end[i] - obj.start[i];
					    }	

					    getTimeSpentPerHour(obj.start[i], obj.end[i]).map(function(t){
												  if (obj.hrPts[t.hour]) {
												      obj.hrPts[t.hour] += t.timeSpent;
												  } else { 
												      obj.hrPts[t.hour] = t.timeSpent;					
												  }
											      });
					};
					this_.maxWeekData = Math.max.apply(undefined, obj.weekPts.concat(this_.maxWeekData));
					this_.maxHourData = Math.max.apply(undefined, obj.hrPts.concat(this_.maxHourData));
				    });

			   // find the top webpages			   
			   //this.viz.data.filter(
			   //    function(vizData){ return vizData.type == this_.type; }).map(

			   index = 0;
			   this.data = top5.map(function(dta){
						    size = (this_.maxR - this_.minR) * ((dta.total - top5[4].total) / (top5[0].total - top5[4].total)) + this_.minR;
						    obj = { 
							xPos: this_.pos.x[index],
							yPos: this_.pos.y[index],
							size: size
						    };
						    index += 1;
						    dta.ent.total = dta.total;
						    dta.ent.topHours = dta.hrPts.concat().sort(function(a,b){ return b - a; }).slice(0,5).map(function(x){if (x > 0) { return dta.hrPts.indexOf(x); }}); // not working
						    dta.ent.topDOW = dta.weekPts.concat().sort(function(a,b){ return b - a; }).slice(0,5).map(function(x){if (x > 0) { return this_.barLabels[dta.weekPts.indexOf(x)]; }});
						    return {	
							name: dta.ent.id,
							entity: dta.ent, // maybe should add to this entity - top times of day hours of day total time spent etc
							duration: dta.total,
							xPos: obj.xPos,
							yPos: obj.yPos,
							hrPts: dta.hrPts,
							weekPts: dta.weekPts,
							size: size,
							color: selectColorForDomain(dta.ent.id),
							poly: circleToPoly(obj)
						    };
						});
		       },
		       setPosition: function(posType){
			   var this_ = this;
			   var foo = 0;
			   var bar = 0;
			   this.pos = {};

			   if (posType == "grid"){
			       this.pos.x = function(){
				   foo = this_.windowWidth/3;
				   bar = this_.windowWidth/4;
				   return [bar,bar*2,bar*3,foo,foo*2];			       
			       }();
			       
			       this.pos.y = function(){
				   foo = this_.windowHeight/3;
				   return [foo - this_.objPadding*2,foo - this_.objPadding*2,foo - this_.objPadding*2,foo*2 + this_.objPadding*2,foo*2 + this_.objPadding*2];
			       }();
			   }
		       },
		       drawNodeConnections: function(params){
			   this.canvas = canvas;
			   var ctx = this.canvas.getContext('2d');
			   this.nodeName = params.name;
		       },
		       mouseMove: function(mousePos){
			   var this_ = this;
			   this.data.map(function(dta){
					     if (isPointInPoly(dta.poly, mousePos)){
						 this_.hoverID = dta.entity.id;
						 this_.viz.drawHoverTxt(dta.entity, mousePos);							      
						 return;
					     };							  
					 });
		       },
		       mouseDown: function(params){			  
		       },
		       mouseUp: function(){
                       }
		   });
