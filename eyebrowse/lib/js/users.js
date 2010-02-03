var WatchmeVisualisation = {
    initialize: function(canvas, zoom){
        this.canvas = canvas;
	this.now = new Date().valueOf();
        this.endDate = new Date();
        this.startDate = new Date(this.endDate.valueOf() - zoom);
        this.endTime = this.endDate.valueOf();
        this.startTime = this.startDate.valueOf();
	this.endTimeRecent = this.endTime;
        this.interp = zoom / 192;
        this.zoom = zoom;
	this.drawUsers();
	this.getProfile(this.startTime, this.endTime);
    },
    drawUsers: function(){
	var letters = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'];
	var html = "";
	for (var i = 0; i < letters.length - 1; i++){
	    html += "<a href=\"/users?letter=" + letters[i] + "\">" + letters[i] + "</a>&nbsp;&nbsp;";
	}
	html += "<a href=\"/users?letter=" + letters[letters.length - 1] + "\">" + letters[letters.length - 1]+ "</a>";
	jQuery("#letters").html(html);
    },
    getProfile: function(startTime, endTime){
	var this_ = this;
	jQuery("#loadimg").show();
        try {
            jQuery.get("/get_users_page", {
			   interp: this_.zoom
		       }, function(data){
			   if (data.code == 200) {								   
			       this_.drawTopUsers(data.results[0]);
			       this_.drawProfile(data.results[1]);
                               jQuery("#loadimg").hide();
			   }
			   else {
			       console.log("yaaaa!!!H!H!H!" + data.code + " ");
			   }
		       }, "json");
        } 
        catch (e) {
            console.log(e);
        }
    },
    drawProfile:function(data){
	var newData = data;
	jQuery("#totalTime").html("<b>total time spent: </b> " + timeCounterLongAbv(newData.totalTime));
	jQuery("#num").html("<b>total visits: </b>" + newData.number);
	jQuery("#avgTime").html("<b>average time spent: </b>" + timeCounterLongAbv(newData.average));					
    },
    drawTopUsers: function(data){
	var newData = data;
	jQuery("#topusers").html("");
	for (var i = 0; i < newData.length; i++) {
	    if (newData[i].number > 0){
		var html = "";
		html += "<li style=\"width:170px; padding:6px\">";
		html += "<h6><b><a href=\"/profile/" + newData[i].user +  "/\">" + newData[i].user + "</a></b></h6>";
		html += "<br /><h7>" + newData[i].number + " webpages viewed</h7>";
		html += "</li>";
		jQuery("#topusers").append(html);
		jQuery(".listItemSmall:first").slideDown("slow");
	    }
	}
    }
};
jQuery(document).ready(function(){
			   jQuery(".imgborder").corner();
			   self.viz = newify(WatchmeVisualisation, document.getElementById("main"), 2629743000*6);// 1 month * 6
		       });
