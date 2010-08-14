
var call_prefix = "/listit/jv3";
window.user_counts = { "" : 0 , "(select set of users from above)" : 0 };

var log = function() {
    try {console.log.apply(console,arguments); } catch (x) { }
};

var check_ready = function() {
    if (window.gu_load && window.gcu_load && window.l2m_load) {
	jQuery("#spinner").fadeOut();
    }
};

var reload_history = function() {
    jQuery("#history").fadeOut();
    jQuery.ajax({		    
		    url:call_prefix + "/karger_email_hi",
			type:"GET",
			success:function(data) {
			    jQuery("#history").fadeIn();			    
                            jQuery("#history").html(data.map(function(row) {
								 log(row.when, typeof(row.when));								 
								  return "<tr>"+[new Date(parseInt(row.when)).toString(),"<textarea>"+row.to+"</textarea>",row.subject,row.body.slice(0,40)].map(
								      function(x) {
									  return "<td>"+x+"</td>";
								      }).join("")+"</tr>";
							      }).join("\n"));

			},
			error:function(x) {
			    if (x.status == 403) { return document.location = '/admin/';   }
			    log(x); document.write(x.responseText);
			}			
		});
};

var xfer_to_from_html = function(jq) {
    try {  jQuery("#to").html(jq);    } catch (x) { log(x);    }
};



jQuery(document).ready(function() {
			   reload_history();			   
	jQuery.ajax({
			url:call_prefix + "/karger_email_gu",
			type:"GET",
			success:function(data) {
			    user_counts['all'] = data;
			    window.gu_load = true; 
			    check_ready();
			    log('all users',data);
			    jQuery("#all_count").html("("+data+")");			    
			},
			error:function(xmlresp) {
			    log(xmlresp.status);
			    if (xmlresp.status == 403) { return document.location = '/admin/';   }
			    log(x); document.write(x.responseText);
			}
		    });
	jQuery.ajax({
			url:call_prefix + "/karger_email_gcu",
			type:"GET",
			success:function(data) {
			    user_counts['consenting'] = data;
			    window.gcu_load = true; 
			    check_ready();
			    jQuery("#consenting_count").html("("+data+")");
			},
			error:function(x) { log(x); document.write(x.responseText); }
		    });
	jQuery.ajax({
			url:call_prefix + "/karger_email_l2m",
			type:"GET",
			success:function(data) {
			    user_counts['recent'] = data;
			    window.l2m_load = true; 
			    check_ready();			    
			    jQuery("#last2months_count").html("("+data+")");
			},
			error:function(x) { log(x); /*document.write(x.responseText);*/ }
		    });			   

	jQuery("#send").click(function(bb) {
				  if (!confirm("Are sure you want to send message" + jQuery("#subject").val() + " to " + user_counts[jQuery("#to").html().trim()] + " users? " )) {  return; }
				  jQuery("#send").attr("disabled",true);
				  jQuery("#body").attr("disabled", true);
				  jQuery("#subject").attr("disabled",true);
				  jQuery.ajax({url:call_prefix + "/karger_send_email",
					       type:"POST",
					       data:JSON.stringify({
								       to:jQuery("#to").html().trim(),
								       body:jQuery("#body").val(),
								       subject:jQuery("#subject").val()
								   }),
					       success:function(id) {
						   log(id, typeof(id));
						   _start_status_poller(id.id);
						   reload_history();
					       },
					       error:function(x) {
						   //log(x);
						   document.write(x.responseText);
					       }});
			      });			   
			   });

var _start_status_poller = function(id) {
    jQuery("#status").fadeIn();
    window.status_timer = setInterval(function() {
		    jQuery.ajax({ url: "/listit/jv3/karger_check_status",
				  type:"GET",
				  data:{ id:id },
				  success:function(datas) {
				      log(datas);
				      jQuery("#status .emaillist").html("sent email to : <br>" + datas.join("<br>"));
				  },
				  error:function(x) {
				      log(x);
				      // document.write(x.responseText);
				  }
				});		    
		},1000);
};

var cancel_send = function() {
    jQuery("#cancel").fadeOut();
    jQuery.ajax({ url: "/listit/jv3/karger_cancel_send",
				  type:"GET",
				  success:function(datas) {
				      jQuery("#status .area").append("cancelled!");
				      clearInterval(window.status_timer);
				  },
				  error:function(x) {
				      log(x);
				      //document.write(x.responseText);
				  }
				});		    
};
