
var call_prefix = "/listit/jv3";

var log = function() {
    try {
	console.log.apply(console,arguments);
    } catch (x) { }
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
			error:function(x) { log(x); document.write(x.responseText);}			
			});
};



jQuery(document).ready(function() {
			   reload_history();			   
	jQuery.ajax({
			url:call_prefix + "/karger_email_gu",
			type:"GET",
			success:function(data) {
			    log('all users',data);
			    jQuery("#all_users").val(data.join(","));
			},
			error:function(x) { log(x); document.write(x.responseText); }
		    });
	jQuery.ajax({
			url:call_prefix + "/karger_email_gcu",
			type:"GET",
			success:function(data) {
			    log('consenting users',data);
			    jQuery("#consenting_users").val(data.join(","));
			},
			error:function(x) { log(x); document.write(x.responseText); }
		    });

	jQuery("#send").click(function(bb) {
			  jQuery("#send").attr("disabled",true);
			  jQuery("#to").attr("disabled", true);
			  jQuery("#body").attr("disabled", true);
			  jQuery("#subject").attr("disabled",true);
			  jQuery.ajax({url:call_prefix + "/karger_send_email",
				       type:"POST",
				       data:JSON.stringify({
					       to:jQuery("#to").val(),
					       body:jQuery("#body").val(),
					       subject:jQuery("#subject").val()
					   }),
				       success:function(id) {
					   log(id, typeof(id));
					   _start_status_poller(id.id);
					   reload_history();
					   //jQuery("#to").val('');
					   //jQuery("#body").val('');
					   //jQuery("#subject").val('');
					   // jQuery("#send").attr("disabled",false);
				       },
				       error:function(x) {
					   log(x);
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
				      jQuery("#status .area").html("sent email to : <br>" + datas.join("<br>"));
				  },
				  error:function(x) {
				      document.write(x.responseText);
				  }
				});		    
		},1000);
};

var cancel_send = function() {
    jQuery("#cancel").fadeOut();
    jQuery.ajax({ url: "/listit/jv3/karger_cancel_send",
				  type:"GET",
				  success:function(datas) {
				      jQuery("#status .area").append("sucesfully cancelled");
				      clearInterval(window.status_timer);
				  },
				  error:function(x) {
				      document.write(x.responseText);
				  }
				});		    
};
