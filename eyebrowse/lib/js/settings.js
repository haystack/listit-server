var Settings = ({
		    initialize:function(){
			this.addWhitelist('#urladdul');
			jQuery('#whitelist').show();
		    },
		    // run when the get whitelist function returns
		    initMenu: function(whitelist){
			var this_ = this;
			jQuery('#popularsites ul').hide();
			jQuery('#popularsites li a').click(
			    function() {
				jQuery(this).next().slideToggle('normal');
			    }
			);
			
			["news","blogs","media","shopping","social","reference"]
			    .map(function(item){											 
				     var html = "<a href=\"javascript:addAllPrivacyURLS(\'" +  pageList[item] + "\');\" style=\"font-weight:bold;\"> share all</a>";
				     var items = pageList[item].sort(function(x, y){ return String.toLowerCase(x) > String.toLowerCase(y); });
				     items.map(function(domain){
						   if (whitelist.indexOf(domain) < 0) {
						       html += this_.drawShareableSite(domain); 
						   } 
					       });				    
				     jQuery("#add_sites #" + item).html(html);				     
				 });
		    },		    
		    setupNewTabPrefs:function(){
			this.pref = JV3.prefs.getCharPref('which');			
			if (this.pref == 'personal'){
			    var mode = JV3.prefs.getCharPref('personalGraphType');
			    jQuery('#' + mode).addClass('sel');
			}
			else {
			    jQuery('#' + this.pref).addClass('sel');
			}			
		    },
		    addWhitelist:function(div){
			var this_ = this;
			jQuery.get("/get_privacy_urls/", {}, function(data){
				       if (data.code == 200) {
					       this_.whitelist = data.results.sort(function(x, y){ return String.toLowerCase(x) > String.toLowerCase(y); });
					       this_.initMenu(this_.whitelist);
					       this_.addMostSharedSites("#top_logged", this_.whitelist);
					       jQuery(div).html(this_.whitelist.map(function(item){
											return this_.drawSharedSite(item);
										    }).join(''));					       
				       }  }, "json");
		    },
		    addMostSharedSites:function(div, whitelist){
			var this_ = this;
			jQuery.get("/get_most_shared_hosts/25/", {}, 
				   function(data){
				       if (data.code == 200) {
					   jQuery(div).html(data.results.map(function(item){ 
										 if (whitelist.indexOf(item[0]) < 0) {
										     return this_.drawShareableSite(item[0]);
										 } 
									     }).join(''));
				       }
				   }, "json");	
		    },
		    drawSharedSite:function(domain){
			return "<li>"
			    + domain
			    + "<a onclick=\"deleteSharedSite(\'" + domain + "\'); jQuery(this).parent().hide('slow');\"><img src=\"../../skin/cancel_16.png\"/></a>"
			    + "</li>";
		    },
		    drawShareableSite: function(domain){
			return "<li>"
			    + "<a onclick=\"JV3.add_to_whitelist(\'" + domain + "\'); addPrivacyURL(\'" + domain + "\'); jQuery(this).parent().hide('slow');\"><b>share</b></a>&nbsp;&nbsp;&nbsp;"
			    + domain
			    +"</li>";			
		    }
		});
jQuery(document).ready(function(){  Settings.initialize();   });