var stackTimeFactory = ({
			    initialize: function(viz, params){
				this.viz = viz;
				this.canvas = this.viz.canvas;
				this.type = params.type;
				this.windowHeight = params.windowHeight;
				this.windowWidth = params.windowWidth;	 
				this.marginTop = 20;
				this.marginLeft = 110;
				this.marginRight = 100;
				this.sectionHeight = 70;
				this.sectionTopPadding = 20;
				this.rowHeight = 20;
				this.rowTopPadding = 10;
				this.setupData();
				this.draw();
			    },
			    draw: function(){
				var ctx = this.canvas.getContext('2d');
				var this_ = this;
				var text = "";
				this.sections.map(function(sect){
						      ctx.fillStyle = "#333333";
						      ctx.font = "11pt Arial";
						      ctx.fillText(sect.label, 0, sect.poly[0].y);  	
						      for (var i = 0; i < this_.rowLabel.length; i++) {
							  ctx.fillStyle = "#333333";
							  ctx.font = "9pt Arial";
							  ctx.fillText(this_.rowLabel[i], this_.marginLeft - ctx.mozMeasureText(this_.rowLabel[i]) - 5, sect.poly[0].y + this_.rowTopPadding + (this_.rowHeight * i) + 13);  			
							  ctx.fillText(timeCounterClock(sect.rowsDuration[i]/1000), this_.windowWidth - this_.marginRight + 5, sect.poly[0].y + this_.rowTopPadding + (this_.rowHeight * i) + 13); 
							  sect.rows[i].map(function(item){
									       ctx.beginPath();
									       ctx.fillStyle = item.color;
									       ctx.fillRect(item.poly[0].x, item.poly[0].y, item.width, this_.rowHeight);
									       
									       if (item.entity.id == this_.hoverID){
										   ctx.fillStyle = "#00ff00";
										   ctx.fillRect(item.poly[0].x, item.poly[0].y, item.width, this_.rowHeight);
									       }
									       ctx.closePath();
									   });
						      };
						  });
			    },
			    setupData: function(){
				var this_ = this;
				var day = 86400000;
				if (this.type == "timeline"){			     
				    this_.rowLabel = JV3.CMS.event_store.getEventTypes();			    
				    this.sections = function(){
					var sect = [];
					var today = new Date().valueOf();
					for (var i = 0; i < 7; i++) {
					    sect.push({
							  label:new Date(today - (day * i)).format('dddd, mmmm dd'), 
							  start: today - (day * i) - day,
							  end: today - (day * i),
							  rows: this_.rowLabel.map(function(row){ return []; }),
							  rowsDuration: this_.rowLabel.map(function(row){ return 0; }),
							  hover: false,
							  sectionNumber: i,
							  poly: rectToPoly({
									       xPos: 0, 
									       yPos: (this_.sectionHeight * i) + this_.sectionTopPadding,
									       width: this_.windowWidth, 
									       height: this_.sectionHeight
									   })
						      });	
					}
					return sect;
				    }();	
				    var sect = undefined;
				    var minWinWidth = this_.windowWidth - this_.marginLeft - this_.marginRight;
				    this_.viz.data.map(function(dta){
							   for (var i = 0; i < this_.sections.length; i++){
							       if ((dta.end.valueOf() < this_.sections[i].end) && (dta.end.valueOf() > this_.sections[i].start)) {
								   for (var j = 0; j < this_.rowLabel.length;j++) {
								       if (dta.type == this_.rowLabel[j]){
									   sect = this_.sections[i];
									   var xPos = this_.marginLeft + (minWinWidth * ((dta.start - sect.start) / (sect.end - sect.start)));
									   if (xPos < this_.marginLeft){ xPos = this_.marginLeft;}
									   var yPos = (this_.sectionHeight * sect.sectionNumber) + this_.sectionTopPadding + (this_.rowHeight * j) + this_.rowTopPadding;
									   var width = this_.marginLeft + minWinWidth * ((dta.end - sect.start) / (sect.end - sect.start)) - xPos;								
									   
									   sect.rowsDuration[j] += (dta.end - dta.start);
									   sect.rows[j].push({
												    entity: dta.entity,
												    width: width,
												    color: selectColorForDomain(dta.entity.id),
												    poly: rectToPoly({
															 xPos: xPos, 
															 yPos: yPos,
															 width: width, 
															 height: this_.rowHeight
														     })
												    
												});										 
								       }
								   }	
								   break;				   
							       }							       
							   }
						       });		
				}
			    },
			    mouseMove: function(mousePos){
				var this_ = this;
				for (var i = 0; i < this.sections.length; i++){			     
				    if (isPointInPoly(this.sections[i].poly, mousePos)){
					this.sections[i].rows.map(function(row){
								      row.map(function(item){
										  if (isPointInPoly(item.poly, mousePos)){
										      this_.hoverID = item.entity.id;
										      this_.viz.drawHoverTxt(item.entity, mousePos);							      
										      return;
										  };							  
									      });
								  });
					return;  
				    }				    
				};			    
			    },
			    mouseDown: function(){
			    },
			    mouseUp: function(params){
			    }
			});
