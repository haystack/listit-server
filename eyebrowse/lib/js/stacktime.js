var stackTimeFactory = ({
		     initialize: function(viz, params){
			 this.viz = viz;
			 this.canvas = this.viz.canvas;
			 this.type = params.type;
			 this.mouseMargin = params.mouseMargin;
			 this.windowHeight = params.windowHeight;
			 this.windowWidth = params.windowWidth;	 
			 this.marginTop = 0;
			 this.marginLeft = 0;
			 this.sectionHeight = 50;
			 this.sectionTopPadding = 40;
			 this.rowHeight = 20;
			 this.rowTopPadding = 10;
			 this.setupData();
			 this.draw();
			 this.mouseVal = undefined;			 
		     },
		     draw: function(){
			 var ctx = this.canvas.getContext('2d');
			 var this_ = this;

			 this.sections.map(function(sect){
					       sect.rows.map(function(row){
								 row.map(function(item){
									     ctx.beginPath();
									     ctx.fillStyle = item.color;
									     ctx.fillRect(item.poly[0].x, item.poly[0].y, item.width, this_.rowHeight);
									     /*
									      if (this_.viz.highlight == this_.domainArray[i]){
									      ctx.fillStyle = "rgba(255,255,255,0.85)"; //"#00ff00";
									      ctx.fillRect(this_.startPointArray[i], this_.marginTop, this_.widthArray[i], this_.height);
									      }
									      */
									     ctx.closePath();
									 });
							     });
					   });

			 /*
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
			  if (!(this_.pIH) && this_.trigger) {
			  this_.trigger = false;
			  this_.viz.highlight = "booo";
			  jQuery("#fooTxt").html("");
			  jQuery("#fooTxt").css({"padding" : "0px"});
			  }
			  */
		     },
		     setupData: function(){
			 var this_ = this;
			 if (this.type == "timeline"){			     
			     var rowLabel = JV3.CMS.event_store.getEventTypes();			    
			     var rows = rowLabel.map(function(row){ return []; });
			     this.sections = function(){
				 var sect = [];
				 var today = new Date().valueOf();
				 for (var i = 0; i < 7; i++) {
				     sect.push({
						   label:new Date(today - (86400000 * i)).format('dddd'), 
						   start: today - (86400000 * (i + 1)),
						   end: today - (86400000 * i),
						   rows: rows,
						   sectionNumber: i
					       });				     
				 }
				 return sect;
			     }();	
			     var done = false;
			     this_.viz.data.map(function(dta){
						    done = false;
						    this_.sections.map(function(sect){									 
									  if (!done){
									      if (dta.end.valueOf() < sect.end && dta.end.valueOf() > sect.start) {
										  for (var i = 0; i < rowLabel.length; i++) {
										      if (dta.type == rowLabel[i]){
											  var xPos = this_.windowWidth * ((dta.start - sect.start) / (sect.end - sect.start)) + this_.marginLeft;
											  var yPos = (this_.sectionHeight * sect.sectionNumber) + this_.sectionTopPadding + (this_.rowHeight * i) + this_.rowTopPadding;
											  var width = this_.windowWidth * ((dta.end - sect.start) / (sect.end - sect.start)) - xPos;

											  sect.rows[i].push({
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
										  done = true;
									      }
									  }
								     });						       
					      });		
			 }
			 console.log(this.sections);
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
				     break;
				 }
			     }

			     var newData = params.newData;
			     for (var i = 0; i < newData.length; i++) {
				 this_.data.push(newData[i]);
				 this_.domainArray.push(newData[i].host);

				 this_.polyArray.push(rectToPoly({xPos: this_.startPointArray[i], yPos: this_.marginTop, width: this_.widthArray[i], height: this_.height}));
			     }

			 }
			 else {
			     // remove old stuff
			     for (var i = 0; i < this_.data.length; i++) {
				 if (this_.data[i].start >= this_.endTime) {
				     this_.data = this_.data.slice(0, i);
				     break;
				 }
			     }

			     var newData = params.newData;
			     for (var i = 0; i < newData.length; i++) {
				 this_.data.unshift(newData[i]);
				 this_.startPointArray.unshift(this_.windowWidth * ((newData[i].start - this_.startTime) / (this_.endTime - this_.startTime)));
				 this_.widthArray.unshift((this_.windowWidth * ((newData[i].end - this_.startTime) / (this_.endTime - this_.startTime))) - this_.startPointArray[i]);
				 this_.polyArray.push(rectToPoly({xPos: this_.startPointArray[i], yPos: this_.marginTop, width: this_.widthArray[i], height: this_.height}));
			     }
			 }

			 this_.OGstartTime = this_.startTime;
			 this_.OGendTime = this_.endTime;
			 this_.movePos();
		     }
		 });
