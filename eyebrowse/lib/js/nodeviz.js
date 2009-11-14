var nodeFactory = ({
                       initialize: function(viz, params){
			   this.viz = viz;
			   this.canvas = this.viz.canvas;
			   this.type = params.type;
			   this.windowHeight = params.windowHeight;
			   this.windowWidth = params.windowWidth;	 
			   this.maxR = 60; 
			   this.minR = 10;
			   this.setPosition('grid');
			   this.setupData();
			   this.draw();
                       },
                       draw: function(){
			   var ctx = this.canvas.getContext('2d');
			   var this_ = this;

			   // draw node lines
			   ctx.lineWidth = 0.5;
			   ctx.strokeStyle = "#333333";
			   this.data.map(function(dta){
					     ctx.fillStyle = dta.color;
					     ctx.beginPath();
					     ctx.arc(dta.xPos, dta.yPos, dta.size, 0, Math.PI * 2, true);
					     ctx.fill();					     
					     ctx.stroke();
					     ctx.closePath();
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
			   this.viz.data.filter(
			       function(vizData){ if (vizData.type == this_.type) { return vizData; }; }).map(
				   function(dta){
				       if (!data[dta.entity.id]) { 
					   data[dta.entity.id] = {
					       id: dta.entity.id,
					       ent: dta.entity,
					       total: 0,
					       time: [
						   {hrPts: JV3.plumutil.intRange(0,24).map(function(){return {};})},
						   {weekPts: JV3.plumutil.intRange(0,7).map(function(){return {};})}
					       ]
					   };
				       }
				       hour = dta.end.getHours();	
				       weekday = dta.end.getDay();	   

				       index = hour;
				       timeSpent = dta.end - dta.start; // this needs to do quite a bit more filtering
				       data[dta.entity.id].total += timeSpent;
				       data[dta.entity.id].time.map(function(time){
									      if (time[index]) {
										  time[index] += timeSpent;
									      } else { 
										  time[index] = timeSpent;					
									      }
									      index = weekday;
				       					  });
				   });
			   data = JV3.plumutil.unzipdict(data);
			   data.sort(function(a,b){ return b[1].total - a[1].total; });
			   data = data.slice(0,5);
			   
			   index = 0;
			   this.data = data.map(function(dta){
						    size = this_.maxR * ((dta[1].total - data[4][1].total) / (data[0][1].total - data[4][1].total)) + this_.minR;
						    obj = { 
							x: this_.pos.x[index],
							y: this_.pos.y[index],
							size: size
						    };
						    index += 1;
						    return {	
							name: dta[1].ent.id,
							entity: dta[1].ent,
							duration: dta[1].total,
							xPos: obj.x,
							yPos: obj.y,
							size: size,
							time: dta[1].time,
							color: selectColorForDomain(dta[1].ent.id),
							poly: circleToPoly(obj)
						    };
						});
			   console.log(this.data);
		       },
		       setPosition: function(posType){
			   var this_ = this;
			   var foo = 0;
			   var bar = 0;
			   this.pos = {};

			   if (posType == "grid"){
			       this_.pos.x = function(){
				   foo = this_.windowWidth/3;
				   bar = this_.windowWidth/4;
				   return [bar,bar*2,bar*3,foo,foo*2];			       
			       }();
			       
			       this_.pos.y = function(){
				   foo = this_.windowHeight/3;
				   return [foo,foo,foo,foo*2,foo*2];
			       }();
			   }
		       },
		       drawNodeConnections: function(params){
			   this.canvas = canvas;
			   var ctx = this.canvas.getContext('2d');
			   this.nodeName = params.name;
		       },
		       mouseMove: function(params){
			   this.pIH = isPointInPoly(this.poly, params.mouseVal);
		       },
		       mouseDown: function(params){			  
			   if (this.pIH) {
			       // might not be the fastest solution
			       for (var j = 0; j < nodeNameArray.length; j++) {
				   mapNav.tabIS[j] = false;
			       }
			       mapNav.tabIS[this.i] = true;
			       swopHTML(this.i);
			   }			  
		       },
		       mouseUp: function(){
			   this.draw();		      
                       }
		   });
