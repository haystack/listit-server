var stackBarGraphFactory = ({
				initialize: function(viz, params){
				    this.viz = viz;
				    this.canvas = viz.canvas;
				    this.type = params.type;
				    this.windowHeight = params.windowHeight;
				    this.windowWidth = params.windowWidth;	 
				    this.height = params.height;
 				    this.bottomPadding = 70;
				    this.textPadding = 0;
				    this.barPadding = 7;
				    this.padding = 2;
				    this.topPadding = 0;
				    this.labelLeft = params.labelLeft;
				    this.labelRight = params.labelRight;					
				    this.midPad = 15;
				    this.dataMax = [];
				    this.setupData(params.type);
				    this.draw();
				},
				draw: function(){
				    var ctx = this.canvas.getContext('2d');
				    ctx.clearRect(0,0,this.windowWidth,this.windowHeight);
				    var this_ = this;

				    // draw the bars
				    this.data.map(function(dta){
						      dta.map(function(column){
								  column.map(function(item){
										 ctx.beginPath();
										 ctx.fillStyle = item.color;
										 ctx.fillRect(item.poly[0].x, item.poly[0].y, item.width, item.height);
										 
										 if (item.ent.id == this_.hoverID){
										     ctx.fillStyle = "#00ff00";
										     ctx.fillRect(item.poly[0].x, item.poly[0].y, item.width, item.height);
										 }
										 ctx.closePath();
									     });
							      });
						  });

				    
				    // draw the key
				    ctx.beginPath();
				    ctx.fillStyle = "#333333";
				    ctx.fillRect(0, this.windowHeight - this.bottomPadding + 4, this.windowWidth/2 - this.midPad, 1);
				    ctx.fillRect(this.windowWidth/2 + this.midPad, this.windowHeight - this.bottomPadding + 4, this.windowWidth/2 - this.midPad, 1);
				    
				    ctx.strokeStyle = "#666666";
				    ctx.font = "9pt Arial";
				    ctx.fillStyle = "#666666";
				    ctx.lineWidth = 0.5;

				    // draw the labels
				    var xPos = 0, marginLeft = -this.windowWidth/2, textMarginLeft = 0;
				    [this.labelRight, this.labelLeft].map(function(labelSet){
								    	      marginLeft += this_.windowWidth/2;
									      textMarginLeft = 0;
									      labelSet.map(function(label){
											       xPos = this_.textPadding + (ctx.measureText(label).width)/2 + marginLeft + textMarginLeft;
											       ctx.fillText("" + label, xPos, this_.windowHeight - this_.bottomPadding + 16);
											       textMarginLeft += (this_.windowWidth/2 - this_.midPad)/labelSet.length;
											   });
									  });
				    
				    ctx.fillStyle = "#333333";				   
				    xPos = 0, marginLeft = -this.windowWidth/2 - (this_.midPad * 2);
				    this.dataMax.map(function(dataMax){
							 marginLeft += this_.windowWidth/2 + (this_.midPad * 2);
							 ctx.fillText(timeCounterClock(dataMax/1000), marginLeft + 2, 10);
							 for (var i = 1; i < 3; i++) {								
							     ctx.fillText(timeCounterClock(Math.floor(((this_.dataMax[1]) / 3) * (3 - i))/1000), marginLeft, ((this_.windowHeight - this_.bottomPadding) / 3) * i + 8);
							 }
						     });

				    ctx.closePath();
				},
				setupData: function(type){
				    var this_ = this;

				    var data = undefined;
				    var weekday = 0;
				    var hour = 0;
				    var hrPts = JV3.plumutil.intRange(0,24).map(function(){return {};});
				    var weekPts = JV3.plumutil.intRange(0,7).map(function(){return {};});
				    
				    var idToEnt = {};
				    this.viz.data.filter(
					function(data){ if (data.type == type) { return data; }; }).map(
					    function(dta){
						weekday = dta.end.getDay();	   
						hour = dta.end.getHours();	
						
						if (hrPts[hour][dta.entity.id]){
						    hrPts[hour][dta.entity.id] += dta.end - dta.start;
						} else { 
						    hrPts[hour][dta.entity.id] = dta.end - dta.start;					
						}
						
						if (weekPts[weekday][dta.entity.id]){
						    weekPts[weekday][dta.entity.id] += dta.end - dta.start;
						} else { 
						    weekPts[weekday][dta.entity.id] = dta.end - dta.start;
						}
						
						idToEnt[dta.entity.id] = dta.entity;
					    });
				    
				    hrPts = hrPts.map(function(hr){
							  var foo =  JV3.plumutil.unzipdict(hr);
							  foo.sort(function(a,b){ return b[1] - a[1]; });
							  return foo.slice(0,10).map(function(x){
											 return {evt:idToEnt[x[0]], val:x[1]};
										     });
						      });

				    weekPts = weekPts.map(function(hr){
							      var foo =  JV3.plumutil.unzipdict(hr);
							      foo.sort(function(a,b){ return b[1] - a[1]; });
							      return foo.slice(0,10).map(function(x){
											     return {evt:idToEnt[x[0]], val:x[1]};
											 });
							  });
				    var leftSide = -this_.windowWidth/2 + 30;
				    this.data = [hrPts, weekPts].map(function(dta){
									 var height = 0, xPos = 0, yPos = 0, columnHeight = 0, columnNumber = -1;
									 var objWidth =  (this_.windowWidth/2)/(dta.length*2) - this_.padding;
									 var dataMax = function(){
									     var maxArray = [];
									     var max = 0;
									     dta.map(function(time){
							   				 max = 0;									 
											 time.map(function(evt){ max += evt.val; });
											 maxArray.push(max);	 
										     });
									     return maxArray.sort(function(a,b){ return b - a; })[0];
									 }();
									 this_.dataMax.push(dataMax);
								    	 leftSide += this_.windowWidth/2;
									 return dta.map(
									     function(column){
										 columnHeight = 0;
										 columnNumber += 1;
										 return column.map(
										     function(obj){
											 height = (this_.windowHeight - this_.bottomPadding) * (obj.val / dataMax);
											 columnHeight -= height;
											 xPos = (this_.windowWidth/2/dta.length)*columnNumber + (this_.padding + dta.length)/dta.length + this_.midPad/2 + leftSide;
											 yPos = this_.windowHeight - this_.bottomPadding + columnHeight;
											 return {														 
											     ent: obj.evt,
											     color: selectColorForDomain(obj.evt.id),
											     height: height,
											     width: objWidth,
											     poly: rectToPoly({
														  xPos: xPos,
														  yPos: yPos,
														  height: height,
														  width: objWidth
													      })
											 };
										     });
									     });
								     });
				},
				mouseMove: function(mousePos){
				    var this_ = this;
				    this.data.map(function(dta){
						      dta.map(function(column){
								  column.map(function(item){
										 if (isPointInPoly(item.poly, mousePos)){
										     this_.hoverID = item.ent.id;											  
										     this_.viz.drawHoverTxt(item.ent, mousePos);			
										     return;  
										 };							  
									     });
							      });
						  });
				},				
				mouseDown: function(){
				},
				mouseUp: function(params){
				}
			    });
