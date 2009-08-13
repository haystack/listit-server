// Graphing Library by Brennan Moore
// DEPENDENCIES
/*
 <script src="lib/js/jquery-1.3.2.min.js">
 </script>
 <script src="lib/js/datepicker.js">
 </script>
 <script src="lib/js/protocrock.js">
 </script>
 <script src="lib/js/zamiang.js">
 </script>
 <script src="lib/js/canvas.text.js">
 </script>
 <script src="lib/js/faces/helvetiker-normal-normal.js">
 </script>
 <script>
 jQuery.noConflict();
 </script>
 */
var evtHandlers = ({
					   mouse: {
						   x: 0,
						   y: 0
					   },
					   initialize: function(viz){
						   this.viz = viz;
						   this.canvas = viz.getCanvas();
						   this.startTime = viz.startTime;
						   this.endTime = viz.endTime;
						   this.OGstartTime = this.startTime;
						   this.OGendTime = this.endTime;
						   this.dragBeginX = 0;
						   this.isStatic = viz.isStatic; // does not make more calls
						   this.getURL = "http://localhost:8000/get_views_user/" + viz.user + "/";
						   this._ev_handlers();
					   },
					   _ev_handlers: function(){
						   var canvas = this.canvas;
						   var this_ = this;

						   jQuery(canvas).mousemove(function(evt){
														var position = jQuery(canvas).position();

														this_.mouse = {
															x: evt.clientX - position.left,
															y: evt.clientY - position.top
														};

														if (this_.viz.drag) {
															this_.viz.startTime -= 24000 * (this_.mouse.x - this_.dragBeginX);
															this_.viz.endTime -= 24000 * (this_.mouse.x - this_.dragBeginX);
															if (this_.viz.endTime >= this_.viz.now) {
																this_.viz.endTime = this_.viz.now.valueOf();
															}
															if ((this_.viz.endTime - 86400000) < this_.viz.startTime) {
																this_.viz.startTime = this_.viz.now - 86400000;
															}
															this_.startTime = this_.viz.startTime;
															this_.endTime = this_.viz.endTime;
														}
														for (var i = 0; i < this_.viz.drawArray.length; i++) {
															for (var k = 0; k < this_.viz.drawArray[i].length; k++) {
																this_.viz.drawArray[i][k].mouseMove({
																										mouseVal: this_.mouse
																									});
															}
														}
														this_.viz.draw();
													});
						   jQuery(canvas).mousedown(function(){
														this_.viz.drag = true;
														this_.dragBeginX = this_.mouse.x;
														for (var i = 0; i < this_.viz.drawArray.length; i++) {
															for (var k = 0; k < this_.viz.drawArray[i].length; k++) {
																this_.viz.drawArray[i][k].mouseDown({
																										mouseVal: this_.mouse
																									});
															}
														}
													});
						   jQuery(canvas).mouseup(function(){
													  if (this_.viz.drag && !this_.isStatic) {
														  this_.viz.drag = false;
														  var p = -(1200 * (this_.mouse.x - this_.dragBeginX)); // "p is weird." - brenn

														  var __gangsta_draw = function(newData) {
															  //
															  for (var i = 0; i < this_.viz.drawArray.length; i++) {
																  for (var k = 0; k < this_.viz.drawArray[i].length; k++) {
																	  this_.viz.drawArray[i][k].mouseUp({
																											p: p,
																											newData: newData
																										});
																  }
															  }
															  this_.OGstartTime = this_.startTime;
															  this_.OGendTime = this_.endTime;
														  };
														  if (p > 0) {
															  try {
																  jQuery.get(this_.getURL, {from:this_.OGendTime,to:this_.endTime},
																			 function(data) {
																				 if (data.code == 200) {
																					 __gangsta_draw(data.results);
																				 } else {
																					 console.log("error -- yaaaa!!!H!H!H!" + data.code + " ");
																				 }
																			 }, "json");
															  } catch(e) {
																  console.log(e);
															  }
														  }
														  else {
															  try {
																  jQuery.get(this_.getURL, {from:this_.startTime,to:this_.OGstartTime}, // i aint even gonna ask.
																			 function(data) {
																				 if (data.code == 200) {
																					 __gangsta_draw(data.results);
																				 } else {
																					 console.log("yaaaa!!!H!H!H!" + data.code + " ");
																				 }
																			 }, "json");
															  } catch(e) {
																  console.log(e);
															  }
														  }
													  }
													  else {
														  this_.viz.drag = false;
													  }
												  });
					   }
				   });


var dateSlider = ({
					  initialize: function(viz, params){
						  this.viz = viz;
						  if (params.canvas) { this.canvas = params.canvas; }
						  else { this.canvas = viz.canvas;}						  
						  this.startDate = viz.startDate;
						  this.endDate = viz.endDate;
						  this.startTime = viz.startTime;
						  this.endTime = viz.endTime;
						  this.OGstartTime = viz.startTime;
						  this.OGendTime = viz.endTime;
						  this.windowHeight = viz.windowHeight;
						  this.windowWidth = viz.windowWidth;
						  this.xOffset = params.xOffset;
						  this.yOffset = params.yOffset;
						  this.padding = params.padding;
						  this.barGraphData = undefined;
						  this.rightSlider = Math.round(-this.windowWidth * ((this.startTime + 5 - this.endTime) / (this.endTime - this.startTime)));
						  this.leftSlider = Math.round(-this.windowWidth * ((this.startTime + 5 - this.startTime) / (this.endTime - this.startTime)));
						  this.sliderTriTop = -2;
						  this.sliderTriBottom = 8;
						  this.sliderTriHeight = this.sliderTriBottom - this.sliderTriTop;
						  this.sliderTriWidth = 10;
						  this.lSP = rectToPoly({
													xPos: this.leftSlider + this.xOffset,
													yPos: this.windowHeight - this.padding + this.sliderTriTop + this.yOffset,
													height: this.sliderTriHeight,
													width: this.sliderTriWidth
												});
						  this.rSP = rectToPoly({
													xPos: this.rightSlider + this.xOffset - this.sliderTriWidth,
													yPos: this.windowHeight - this.padding + this.sliderTriTop + this.yOffset,
													height: this.sliderTriHeight,
													width: this.sliderTriWidth
												});
						  this.lIS = undefined; // is selected
						  this.rIS = undefined;
						  this.lIH = undefined; // is hover
						  this.rIH = undefined;
						  this.trigger = false;
						  this.draw();
					  },
					  draw: function(){
						  var ctx = this.canvas.getContext('2d');
						  var this_ = this;

						  // check to see if there is a new value for max date time
						  if ((this_.startTime !== this_.viz.startTime) || (this_.endTime !== this_.viz.endTime)) {
							  this_.startDate = new Date(this_.viz.startTime);
							  this_.endDate = new Date(this_.viz.endTime);
							  this_.startTime = this_.viz.startTime;
							  this_.endTime = this_.viz.endTime;
						  }

						  ctx.font = "0.8pt helvetiker";

						  // there should be a way to combine the next 3 functions
						  // TODO make that happen				  
 						  // dates
						  ctx.beginPath();
						  ctx.lineWidth = 1;
						  ctx.strokeStyle = "#0f0f0f";
						  var fooHour = 0;
						  var numHrs = 7;
						  //console.log(this_.endTime);
						  var endDateVal = (Math.floor((this_.endTime / (this_.viz.zoom / numHrs))) * (this_.viz.zoom / numHrs)) + 1800000; 
						  
						  for (var hrCount = 0; hrCount < numHrs; hrCount++) {
							  var dayText = new Date(endDateVal +  86400000- fooHour);
							  var q = this_.windowWidth * ((endDateVal - fooHour - this_.startDate) / (this_.endDate - this_.startDate));
							  ctx.fillStyle = "#999999";
							  ctx.fillText(dayText.format('mmmm d'), q + 6, this_.windowHeight - this_.padding + 27);
							  ctx.beginPath();
							  ctx.fillStyle = "#333333";
							  ctx.arc(q,this_.windowHeight - this_.padding + 22,1.5,0,Math.PI*2,true);
							  ctx.fill();
							  ctx.closePath();
							  
							  fooHour += (this_.viz.zoom / numHrs);
						  }
						  ctx.closePath();

						  // lines for each 12 hrs
						  ctx.beginPath();
						  ctx.fillStyle = "#666666";
						  fooHour = 0;
						  numHrs = 14;
						  endDateVal = (Math.floor((this_.endTime / (this_.viz.zoom / numHrs))) * (this_.viz.zoom / numHrs)) + 1800000; 						  
						  // not sure why i have to subtract this but it ensures that the dates are on a 12 hr scale						  
						  for (hrCount = 0; hrCount < numHrs; hrCount++) {
							  var dayText = new Date(endDateVal - fooHour);
							  var q = this_.windowWidth * ((endDateVal - fooHour - this_.startDate) / (this_.endDate - this_.startDate));
							  ctx.fillStyle = "#000000";
							  ctx.fillRect(q, this_.windowHeight - this_.padding + 2, 1.5, 6);							  
							  fooHour += (this_.viz.zoom / numHrs);
						  }
						  ctx.closePath();


						  // lines for each hour
						  ctx.beginPath();
						  ctx.fillStyle = "#666666";
						  fooHour = 0;
						  numHrs = this_.viz.zoom/3600000;
						  endDateVal = (Math.floor((this_.endTime / (this_.viz.zoom / numHrs))) * (this_.viz.zoom / numHrs)) + 1800000; 						  
						  // not sure why i have to subtract this but it ensures that the dates are on a 12 hr scale
						  for (hrCount = 0; hrCount < numHrs + 24; hrCount++) {
							  var dayText = new Date(endDateVal - fooHour);
							  var q = this_.windowWidth * ((endDateVal - fooHour - this_.startDate) / (this_.endDate - this_.startDate));
							  ctx.fillRect(q, this_.windowHeight - this_.padding + 2, 0.5, 3);
							  fooHour += (this_.viz.zoom / numHrs);
						  }
						  ctx.closePath();

						  // lines for date nav min/max
						  ctx.beginPath();
						  ctx.lineWidth = 1;
						  ctx.strokeStyle = "#000000";
						  ctx.fillStyle = "#000000";
						  ctx.fillText(this_.startDate.format('dddd, mmmm d h:MM TT'), 10, this_.windowHeight - this_.padding + 50);
						  ctx.fillText(this_.endDate.format('dddd, mmmm d h:MM TT'), this_.windowWidth - 130, this_.windowHeight - this_.padding + 50);
						  ctx.closePath();

						  // line showing width
						  ctx.beginPath();						  
						  ctx.moveTo(0, this_.windowHeight - this_.padding - 2);
						  ctx.lineTo(this_.windowWidth, this_.windowHeight - this_.padding - 2);
						  ctx.lineWidth = 2.5;
						  ctx.stroke();
						  ctx.closePath();
					  },
					  mouseMove: function(params){
						  var this_ = this;

						  this_.rIH = isPointInPoly(this_.rSP, params.mouseVal);
						  this_.lIH = isPointInPoly(this_.lSP, params.mouseVal);

						  if (this_.rIS) {
							  this_.rightSlider = params.mouseVal.x;
						  }
						  if (this_.lIS) {
							  this_.leftSlider = params.mouseVal.x;
						  }
						  if (!(this_.lIH || this_.lIS) && !(this_.rIH || this_.rIH) && this_.trigger) {
							  this_.trigger = false;
						  }
					  },
					  mouseDown: function(params){
						  var this_ = this;

						  if (this_.rIH) {
							  this_.viz.drag = false;
							  this_.rIS = true;

						  }
						  if (this_.lIH) {
							  this_.viz.drag = false;
							  this_.lIS = true;
						  }
					  },
					  mouseUp: function(){
						  var this_ = this;

						  this_.lIS = false;
						  this_.rIS = false;
						  this_.lIH = false;
						  this_.rIH = false;
						  this_.trigger = false;
						  this_.barGraph = false;

						  jQuery("#fooTxt").html("");

						  this_.rSP = rectToPoly({
													 xPos: this_.rightSlider + this_.xOffset - this.sliderTriWidth,
													 yPos: this_.windowHeight - this_.padding + this_.sliderTriTop + this_.yOffset,
													 height: this_.sliderTriHeight,
													 width: this_.sliderTriWidth
												 });
						  this_.lSP = rectToPoly({
													 xPos: this_.leftSlider + this_.xOffset,
													 yPos: this_.windowHeight - this_.padding + this_.sliderTriTop + this_.yOffset,
													 height: this_.sliderTriHeight,
													 width: this_.sliderTriWidth
												 });

					  }
				  });


var lineGraphFactoryLite = ({
								initialize: function(params){
									this.canvas = params.canvas;
									this.startTime = params.startTime;
									this.endTime = params.endTime;
									this.startDate = new Date(this.startTime);
									this.endDate = new Date(this.endTime);
									this.zoom = this.endTime - this.startTime;
									this.windowHeight = params.windowHeight;
									this.windowWidth = params.windowWidth;
									this.interp = params.interp;
									this.margintop = params.margintop; 
									if (!this.margintop) {
										this.margintop = 0;
									}
									this.padding = this.windowHeight - 50 + this.margintop;
									this.topPadding = params.topPadding;
									if (!this.topPadding){
										this.topPadding = 10;
									}
									this.color = params.color;
									this.data = params.data;
									this.fillGraph = params.fillGraph;
									this.setXY();
								},
								draw: function(){
									var ctx = this.canvas.getContext('2d');
									var this_ = this;
									ctx.clearRect(0,0,this_.windowWidth,this_.windowHeight - this_.topPadding - 10);
									ctx.save();
									ctx.translate(0,0-10);
									ctx.beginPath();
									ctx.lineWidth = 2;
									ctx.strokeStyle = this_.color;
									ctx.moveTo(this_.xPoints[0], this_.yPoints[0]);
									for (var y = 1; y < this_.yPoints.length; y++) {
										ctx.lineTo(this_.xPoints[y], this_.yPoints[y]);
									}
									// the fill graph has no key 
									if (this_.fillGraph){
										ctx.fillStyle = this_.color;										
										//ctx.fill();
										ctx.stroke();
										ctx.closePath();
										ctx.restore();
									}
									else {
										ctx.stroke();
										ctx.closePath();
										ctx.restore();

										// draw the lines
										// lines for each 12 hrs
										ctx.beginPath();
										ctx.fillStyle = "#666666";
										var fooHour = 0;
										var numHrs = 7;
										var endDateVal = (Math.floor((this_.endTime / (this_.zoom / numHrs))) * (this_.zoom / numHrs)) + 1800000; 						  
										// not sure why i have to subtract this but it ensures that the dates are on a 12 hr scale						  
										for (var hrCount = 0; hrCount < numHrs; hrCount++) {
											var dayText = new Date(endDateVal - fooHour);
											var q = this_.windowWidth * ((endDateVal - fooHour - this_.startDate) / (this_.endDate - this_.startDate));
											ctx.fillStyle = "#000000";
											ctx.fillRect(q, this_.windowHeight - 50, 1, 6);							  
											fooHour += (this_.zoom / numHrs);
										}
										ctx.closePath();


										// lines for each hour
										ctx.beginPath();
										ctx.fillStyle = "#666666";
										fooHour = 0;
										numHrs = this_.zoom/3600000;
										endDateVal = (Math.floor((this_.endTime / (this_.zoom / numHrs))) * (this_.zoom / numHrs)) + 1800000; 						  
										// not sure why i have to subtract this but it ensures that the dates are on a 12 hr scale
										for (hrCount = 0; hrCount < numHrs + 24; hrCount++) {
											var dayText = new Date(endDateVal - fooHour);
											var q = this_.windowWidth * ((endDateVal - fooHour - this_.startDate) / (this_.endDate - this_.startDate));
											ctx.fillRect(q, this_.windowHeight - 50, 0.5, 3);
											fooHour += (this_.zoom / numHrs);
										}
										ctx.closePath();



										// draw the key
										ctx.beginPath();
										ctx.fillStyle = "#333333";
										ctx.fillRect(0, this_.padding, this_.windowWidth, 1);

										ctx.strokeStyle = "#666666";
										ctx.font = ".7pt helvetiker";
										ctx.fillStyle = "#666666";
										ctx.lineWidth = 0.5;
										if (this_.endTime - this_.startTime > 43200000){											
											ctx.fillText("" + this_.startDate.format('mmmm d'), 10, this_.padding + 20);
											ctx.fillText("" + this_.endDate.format('mmmm d'), this_.windowWidth - 50, this_.padding + 20); // need to make this x value dyanmic base dod on size of text using measureText(0
										}
										else {
											ctx.fillText("" + this_.startDate.format('hh:mm TT'), 10, this_.padding + 20);
											ctx.fillText("" + this_.endDate.format('hh:mm TT'), this_.windowWidth - 40, this_.padding + 20); // need to make this x value dyanmic base dod on size of text using measureText(0											
										}
										ctx.save();
										ctx.translate(0,0-10);
										ctx.fillText("" + timeCounterClock(this_.maxData/ 1000), 9, this_.topPadding + 10);
										ctx.fillText("" + 0, 9, this_.padding + 3);
										for (var i = 1; i < 3; i++) {
											ctx.fillText("" + timeCounterClock(Math.floor(((this_.maxData - this_.minData) / 3) * i) / 1000), 9, (this_.padding + 3 + -(((this_.padding + 3) - (this_.topPadding + 5)) / 3) * i));
										}
										ctx.restore();
										ctx.closePath();									
									}
								},
								setXY: function(){
									var this_ = this;

									var fooStartTime = Math.floor((this_.startTime / this_.interp)) * this_.interp;
									this_.count = (Math.floor((this_.endTime - this_.startTime) / this_.interp));

									this_.xPoints = [];
									this_.yPoints = [];
									this_.foo = [];

									var newWebViewed = this_.data;

									this_.minData = 0; // newWebViewed.min();
									this_.maxData =  newWebViewed.max(); // should find max of entire dataset
									var fooX = function(){
										var foo = fooStartTime;
										var webHrArray = [];
										for (var i = 0; i < this_.count; i++) {
											webHrArray[i] = foo;
											foo += this_.interp;
										}
										return webHrArray;
									}();

									for (var i = 1; i < this_.count; i++) { // why does this start at 1?
										this_.foo[i] = -(newWebViewed[i]);
										var wFoo = this_.windowWidth * ((fooX[i] - this_.startTime) / (this_.endTime - this_.startTime));
										var hFoo = ((this_.padding - this_.topPadding) * ((this_.foo[i] - this_.minData) / (this_.maxData - this_.minData)) + this_.padding);

										this_.xPoints.push(wFoo);
										this_.yPoints.push(hFoo);
									}
									this_.draw();
								},
								// these have to be here to be able to place this in the evtHandlers draw array
								mouseMove: function(params){
								},
								mouseDown: function(){
								},
								mouseUp: function(){									
								}
							});


var lineGraphFactory = ({
							initialize: function(viz, params){
								this.viz = viz;
								if (params.canvas) { this.canvas = params.canvas; }
								else { this.canvas = viz.canvas;}
								if (params.windowHeight){
									this.windowHeight = params.windowHeight;
								} else {
									this.windowHeight = viz.windowHeight;
								}
								if (params.windowWidth) {
									this.windowWidth = params.windowWidth;	 
								} else {
									this.windowWidth = viz.windowWidth;
								}
								this.startDate = viz.startDate;
								this.endDate = viz.endDate;
								this.startTime = viz.startTime;
								this.endTime = viz.endTime;
								this.OGstartTime = viz.startTime;
								this.OGendTime = viz.endTime;
								this.interp = viz.interp;
								this.padding = params.padding;
								this.topPadding = params.topPadding;
								this.dashed = params.dashed;
								this.color = params.color;
								this.key = params.key;
								this.label = params.label;
								this.data = [];
								for (var i = 0; i < params.data.length; i++) {
									this.data.push(params.data[i].start, params.data[i].end);
								}

								this.avg = params.avg; // boolean
								this.setXY();
							},
							draw: function(){
								var ctx = this.canvas.getContext('2d');
								var this_ = this;

								// check to see if there is a new value for max date time
								if ((this_.startTime !== this_.viz.startTime) || (this_.endTime !== this_.viz.endTime)) {
									this_.startTime = this_.viz.startTime;
									this_.endTime = this_.viz.endTime;
									this_.setXY();
								}

								ctx.beginPath();
								ctx.lineWidth = 2;
								ctx.strokeStyle = this_.color;
								ctx.moveTo(this_.xPoints[0], this_.yPoints[0]);
								for (var y = 1; y < this_.yPoints.length; y++) {
									ctx.lineTo(this_.xPoints[y], this_.yPoints[y]);
								}
								ctx.stroke();
								ctx.closePath();

								if (this_.key) {
									ctx.beginPath();
									ctx.strokeStyle = "#333333";
									ctx.font = ".7pt helvetiker";
									ctx.fillStyle = "#333333";
									ctx.lineWidth = 0.5;
									ctx.fillText("" + this_.maxData, 9, this_.topPadding + 5);
									ctx.fillText("" + this_.minData, 9, this_.padding + 3);
									ctx.fillText("" + this_.maxData, this_.windowWidth - 19, this_.topPadding + 5);
									ctx.fillText("" + this_.minData, this_.windowWidth - 19, this_.padding + 3);
									for (var i = 1; i < 7; i++) {
										ctx.fillText("" + Math.floor(((this_.maxData - this_.minData) / 7) * i), 9, (this_.padding + 3 + -(((this_.padding + 3) - (this_.topPadding + 5)) / 7) * i));
										ctx.fillText("" + Math.floor(((this_.maxData - this_.minData) / 7) * i), this_.windowWidth - 19, (this_.padding + 3 + -(((this_.padding + 3) - (this_.topPadding + 5)) / 7) * i));
									}
									// draw the label
									ctx.fillText(this_.label,33, this_.topPadding + 5);
									ctx.closePath();
								}
							},
							mouseMove: function(params){
								var this_ = this;
							},
							mouseDown: function(){
								var this_ = this;
							},
							mouseUp: function(params){
								var this_ = this;
								if (params.p > 0) {
									// remove old stuff
									for (var i = this_.data.length - 1; i > 0; i--) {
										if (this_.data[i] >= this_.endTime) {
											var foo = this_.data.length;
											this_.data = this_.data.slice(i, foo);
											break;
										}
									}
									for (var i = 0; i < params.newData.length; i++) {
										this_.data.push(params.newData[i].start, params.newData[i].end);
									}

								}
								else {
									// remove old stuff
									for (var i = 0; i < this_.data.length; i++) {
										if (this_.data[i] >= this_.endTime) {
											this_.data = this_.data.slice(0, i);
											break;
										}
									}
									for (var i = 0; i < params.newData.length; i++) {
										this_.data.unshift(params.newData[i].start, params.newData[i].end);
									}
								}

								this_.OGstartTime = this_.startTime;
								this_.OGendTime = this_.endTime;
								this_.setXY();
							},
							setXY: function(){
								var this_ = this;

								var fooStartTime = Math.floor((this_.startTime / this_.interp)) * this_.interp;
								this_.count = (Math.floor((this_.endTime - this_.startTime) / this_.interp));

								this_.xPoints = [];
								this_.yPoints = [];
								this_.foo = [];

								var newWebViewed = function(){
									var counts = new Array(this_.count);

									this_.data.map(function(record){
													   if (record > this_.endTime || record < this_.startTime) {
														   return;
													   }
													   var hour = Math.ceil((record - fooStartTime) / this_.interp);
													   counts[hour] = counts[hour] === undefined ? 1 : counts[hour] + 1;
												   });
									for (var i = 0; i < counts.length; i++) {
										if (counts[i] === undefined) {
											counts[i] = 0;
										}
									}
									return counts;
								}();

								this_.minData = 0;
								this_.maxData = newWebViewed.max();
								if (this_.maxData < 1) {this_.maxData = 10;} // cant be zero or the world will explode. i chose 10 for shits

								var fooX = function(){
									var foo = fooStartTime;
									var webHrArray = [];
									for (var i = 0; i < this_.count; i++) {
										webHrArray[i] = foo;
										foo += this_.interp;
									}
									return webHrArray;
								}();

								for (var i = 1; i < this_.count; i++) {
									this_.xPoints.push(this_.windowWidth * ((fooX[i] - this_.startTime) / (this_.endTime - this_.startTime)));
									this_.yPoints.push((this_.padding - this_.topPadding) * ((-(newWebViewed[i]) - this_.minData) / (this_.maxData - this_.minData)) + this_.padding);
								}

								if (this_.avg) {
									this_.yPoints = this_.avgCounts(this_.findStartIndex(this_.yPoints));
								}
								this_.draw();
							}
						});


var statusFactory = ({
						 initialize: function(viz, params){
							 this.viz = viz;
							 if (params.canvas) { this.canvas = params.canvas; }
							 else { this.canvas = viz.canvas;}
							 if (params.windowHeight){
								 this.windowHeight = params.windowHeight;
							 } else {
								 this.windowHeight = viz.windowHeight;
							 }
							 if (params.windowWidth) {
								 this.windowWidth = params.windowWidth;	 
							 } else {
								 this.windowWidth = viz.windowWidth;
							 }
							 this.startTime = params.startTime;
							 this.endTime = params.endTime;
							 this.OGstartTime = this.startTime;
							 this.OGendTime = this.endTime;
							 this.xOffset = params.xOffset;
							 this.yOffset = params.yOffset;
							 this.color = params.color;
							 this.marginTop = params.marginTop;
							 this.height = params.height;
							 this.data = params.data;
							 this.pIH = undefined;
							 this.staticStatic = params.staticStatic;
							 this.trigger = false;
							 this.setPos();
							 this.mouseVal = undefined;
							 this.fooTxtY = params.fooTxtY;
							 this.fooTxtX = params.fooTxtX;
							 if (!(this.fooTxtY)){
								 this.fooTxtY = 0;
							 }
							 if (!(this.fooTxtX)){
								 this.fooTxtX = 0;
							 }
							 if (params.noHover){
								 this.noHover = params.noHover;
							 }
							 
						 },
						 selectColorForDomain:function(domain) {
							 // now we need to turn this domain into a color.
							 if (this.__color_cache === undefined) { this.__color_cache = {}; }
							 if (this.__color_cache[domain] === undefined) {
								 var mystery_prime =  3021377; //13646456457645727890239087; //1283180923023829; //3021377;

								 // rgb generator
								 var rgb_generator = function(d) {
									 var biggest_color = parseInt("ffffff",16);
									 var code = d.length > 0 ?
										 d.split('').map(function(x) { return x.charCodeAt(0); }).reduce(function(x,y) { return x+y; }) * mystery_prime % biggest_color :
									 65535;
									 return "#"+code.toString(16);
								 };

								 // hsl generator
								 var hsl_generator = function(domain) {
									 var h = domain.length > 0 ?  domain.split('').map(function(x) { return x.charCodeAt(0); }).reduce(function(x,y) { return x+y; })  % 360 : 172;
									 var s = "100%";
									 var l = "50%";
									 return   "hsl("+[""+h,s,l].join(",")+")";
								 };

								 this.__color_cache[domain] = hsl_generator(domain); //rgb_generator(domain); //hsl_generator(domain);
							 }
							 return this.__color_cache[domain];
						 },
						 draw: function(){
							 var ctx = this.canvas.getContext('2d');
							 var this_ = this;

							 // check to see if there is a new value for max date time
							 if (((this_.startTime !== this_.viz.startTime) || (this_.endTime !== this_.viz.endTime)) && !this_.staticStatic) {
								 this_.startTime = this_.viz.startTime;
								 this_.endTime = this_.viz.endTime;
								 this_.movePos();
							 }

							 for (var i = 0; i < this_.startPointArray.length; i++) {
								 if (this_.pIH) {
									 if (isPointInPoly(this_.polyArray[i], this_.mouseVal)){
										 this_.viz.highlight = this_.domainArray[i];
										 this_.trigger = true;
										 if (this_.noHover){
										 } else {			
											 jQuery("#fooTxt").html("<a href=\"" + this_.urlArray[i] + "\">" + this_.titleArray[i] + "</a>");
											 jQuery("#fooTxt").css({"left" : this_.mouseVal.x + this_.fooTxtX + "px", "padding": "3px", "top" : this_.marginTop + 45 + this_.fooTxtY + "px" });
										 }
									 }
								 }
								 ctx.beginPath();
								 ctx.fillStyle = this_.selectColorForDomain(this_.domainArray[i]);
								 ctx.fillRect(this_.startPointArray[i], this_.marginTop, this_.widthArray[i], this_.height);
								 if (this_.viz.highlight == this_.domainArray[i]){
									 ctx.fillStyle = "rgba(255,255,255,0.85)"; //"#00ff00";
									 ctx.fillRect(this_.startPointArray[i], this_.marginTop, this_.widthArray[i], this_.height);
								 }
								 ctx.closePath();
							 }
							 
							 if (!(this_.pIH) && this_.trigger) {
								 this_.trigger = false;
								 this_.viz.highlight = "booo";
								 jQuery("#fooTxt").html("");
								 jQuery("#fooTxt").css({"padding" : "0px"});
							 }
						 },
						 mouseMove: function(params){
							 var this_ = this;
							 this_.mouseVal = params.mouseVal;
							 this_.pIH = isPointInPoly(this_.poly, params.mouseVal);
						 },
						 mouseDown: function(){
						 },
						 mouseUp: function(params){
							 var this_ = this;
							 if (params.p > 0) {
								 // remove old stuff
								 for (var i = this_.data.length - 1; i > 0; i--) {
									 if (this_.data[i].start >= this_.endTime) {
										 var foo = this_.data.length;
										 this_.data = this_.data.slice(i, foo);
										 this_.domainArray = this_.domainArray.slice(i, foo);
										 this_.urlArray = this_.urlArray.slice(i, foo);
										 this_.titleArray = this_.titleArray.slice(i, foo);	    
										 this_.startPointArray = this_.startPointArray.slice(i, foo);
										 this_.widthArray = this_.widthArray.slice(i, foo);
										 this_.polyArray = this_.polyArray.slice(i, foo);
										 break;
									 }
								 }

								 var newData = params.newData;
								 for (var i = 0; i < newData.length; i++) {
									 this_.data.push(newData[i]);
									 this_.domainArray.push(newData[i].entity.host);
									 this_.urlArray.push(newData[i].url);
									 this_.titleArray.push(newData[i].title);
									 this_.startPointArray.push(this_.windowWidth * ((newData[i].start - this_.startTime) / (this_.endTime - this_.startTime)));
									 this_.widthArray.push((this_.windowWidth * ((newData[i].end - this_.startTime) / (this_.endTime - this_.startTime))) - this_.startPointArray[i]);
									 this_.polyArray.push(rectToPoly({xPos: this_.startPointArray[i], yPos: this_.marginTop, width: this_.widthArray[i], height: this_.height}));
								 }

							 }
							 else {
								 // remove old stuff
								 for (var i = 0; i < this_.data.length; i++) {
									 if (this_.data[i].start >= this_.endTime) {
										 this_.data = this_.data.slice(0, i);
										 this_.domainArray = this_.domainArray.slice(0, i);
										 this_.titleArray = this_.titleArray.slice(0, i);
										 this_.urlArray = this_.urlArray.slice(0, i);
										 this_.startPointArray = this_.startPointArray.slice(0, i);
										 this_.widthArray = this_.widthArray.slice(0, i);
										 this_.polyArray = this_.polyArray.slice(0, i);
										 break;
									 }
								 }

								 var newData = params.newData;
								 for (var i = 0; i < newData.length; i++) {
									 this_.data.unshift(newData[i]);
									 this_.domainArray.unshift(newData[i].entity.host);
									 this_.urlArray.unshift(newData[i].url);
									 this_.titleArray.unshift(newData[i].title);
									 this_.startPointArray.unshift(this_.windowWidth * ((newData[i].start - this_.startTime) / (this_.endTime - this_.startTime)));
									 this_.widthArray.unshift((this_.windowWidth * ((newData[i].end - this_.startTime) / (this_.endTime - this_.startTime))) - this_.startPointArray[i]);
									 this_.polyArray.push(rectToPoly({xPos: this_.startPointArray[i], yPos: this_.marginTop, width: this_.widthArray[i], height: this_.height}));
								 }
							 }

							 this_.OGstartTime = this_.startTime;
							 this_.OGendTime = this_.endTime;
							 this_.movePos();
						 },
						 setPos: function(){
							 var this_ = this;

							 this_.domainArray = [];
							 this_.urlArray = [];
							 this_.startPointArray = [];
							 this_.widthArray = [];
							 this_.polyArray = [];
							 this_.titleArray = [];
							 for (var i = 0; i < this_.data.length; i++) {
								 this_.domainArray[i] = this_.data[i].entity.host;
								 this_.urlArray[i] = this_.data[i].url;
								 this_.titleArray[i] = this_.data[i].title;
								 this_.startPointArray[i] = this_.windowWidth * ((this_.data[i].start - this_.startTime) / (this_.endTime - this_.startTime));
								 this_.widthArray[i] = (this_.windowWidth * ((this_.data[i].end - this_.startTime) / (this_.endTime - this_.startTime))) - this_.startPointArray[i];
								 this_.polyArray[i] = rectToPoly({xPos: this_.startPointArray[i], yPos: this_.marginTop, width: this_.widthArray[i], height: this_.height});
							 }
							 this_.poly = rectToPoly({
														 xPos: this_.xOffset,
														 yPos: this_.marginTop - this_.yOffset,
														 height: this_.height,
														 width: this_.windowWidth - this_.yOffset
													 });
							 this_.draw();
						 },
						 movePos: function(){
							 var this_ = this;

							 for (var i = 0; i < this_.startPointArray.length; i++) {
								 this_.startPointArray[i] = this_.windowWidth * ((this_.data[i].start - this_.startTime) / (this_.endTime - this_.startTime));
								 this_.widthArray[i] = (this_.windowWidth * ((this_.data[i].end - this_.startTime) / (this_.endTime - this_.startTime))) - this_.startPointArray[i];
								 this_.polyArray[i] = rectToPoly({xPos: this_.startPointArray[i], yPos: this_.marginTop, width: this_.widthArray[i], height: this_.height});
							 }
							 this_.draw();

						 }

					 });

var compareFactory  = ({
						   initialize: function(viz, params){
							   this.viz = viz;
							   if (params.canvas) { this.canvas = params.canvas; }
							   else { this.canvas = viz.canvas;}
							   if (params.windowHeight){
								   this.windowHeight = params.windowHeight;
							   } else {
								   this.windowHeight = viz.windowHeight;
							   }
							   if (params.windowWidth) {
								   this.windowWidth = params.windowWidth;	 
							   } else {
								   this.windowWidth = viz.windowWidth;
							   }
							   this.xOffset = params.xOffset;
							   this.yOffset = params.yOffset;
							   this.lineWidth = params.lineWidth;
							   this.data = params.data;
							   this.minH = params.minH;
							   this.maxH = params.maxH;							   
							   this.draw();
						   },
						   draw: function(){
							   var ctx = this.canvas.getContext('2d');
							   var this_ = this;
							   
							   var maxLineWidth = this_.data.to.min(); 
							   var minLineWidth = this_.data.to.min();
							   var startY = 20;
							   for (var i = 0; i < this_.data.to.length; i++){
								   ctx.lineWidth = this_.lineWidth * ((this_.data.to.value - minLineWidth)/(maxLineWidth - minLineWidth));
								   ctx.strokeColor = "hsl(" + this_.maxH * ((this_.data.to.value - this_.minH)/(this_.maxH - this_.minH)) + this_.minH + ", 100%, 50%)";
								   ctx.beginPath();
								   ctx.moveTo(100, startY );
								   ctx.lineTo(this_.windowWidth/2, this_.windowHeight/2);
								   ctx.stroke();
								   ctx.closePath();								   
								   startY += this_.windowHeight / this_.data.to.length + 20;
							   }

							   startY = 20;
							   for (var i = 0; i < this_.data.from.length; i++){
								   ctx.lineWidth = this_.lineWidth * ((this_.data.from.value - minLineWidth)/(maxLineWidth - minLineWidth));
								   ctx.strokeColor = "hsl(" + this_.maxH * ((this_.data.from.value - this_.minH)/(this_.maxH - this_.minH)) + this_.minH + ", 100%, 50%)";
								   ctx.beginPath();
								   ctx.moveTo(this_.windowWidth - 100, startY );
								   ctx.lineTo(this_.windowWidth/2, this_.windowHeight/2);
								   ctx.stroke();
								   ctx.closePath();								   
								   startY += this_.windowHeight / this_.data.from.length + 20;
							   }
						   }
					   });
