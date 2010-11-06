
var cats = ["-no idea-","memory trigger","reference","external cognition", "journal/activity log", "posterity"];

function cat_to_id(cat) { return "category_"+cats.indexOf(cat); }

var degrees = ["1- no","2- unlikely","3- could be","4- likely","5- definitely"];

function make_note(n){
  var s = "<tr class='note'><td class='notecol'>"+n.contents.replace("\n","<br>").slice(0,100)+"</td>";
  s += "<td class='pricatcol'><SELECT class='primary'><OPTION>"+cats.join("</OPTION><OPTION>")+"</OPTION></SELECT></td>";
  s += "</tr>";
  var sq = jQuery(s);
  cats.slice(1).map(function(x) {
	     var secondary = jQuery("<td class='seccatcol'><SELECT class='secondary "+cat_to_id(x)+"' foo='"+x+"'></SELECT></td>");
	     degrees.map(function(d) {
			   secondary.find("select").append("<OPTION>"+d+"</OPTION>");
			 });
	     sq.append( secondary ) ;
	   });
  sq.data("contents",n.contents);
  return sq.attr("owner",n.owner_id).attr("jid",n.jid);
}

function send(start,end,success_cont) {
  console.log("SEND >> ",start," - ", end);
  var rows = jQuery("tr").filter(".note");
  if (start !== undefined && end !== undefined) {
    rows = rows.slice(start,end);
  }

  var results = [];
  rows.each(function() {
		      var row = jQuery(this);
		      var ownerid = row.attr("owner");
		      var coder = jQuery("#coder").val();
		      var jid = row.attr("jid");
		      if (ownerid === null || jid === null || ownerid == undefined || jid == undefined) { return;   }
		      var pricat = row.children(".pricatcol").children("select").val();
		      var result = { coder:coder, owner_id: ownerid, jid: jid, primary: pricat, contents:row.data("contents") };
		      var sec = row.children(".seccatcol").children('select').each(function(i) {  result[cats[i+1]] = jQuery(this).val();   });
		      results.push(result);
		    });

  console.log(results);
  jQuery.ajax({ url: "/listit/jv3/post_intention/",
		type:"POST",
		data:JSON.stringify({results:results}),
		success:function() {
		  console.log(success_cont);
		  success_cont();
		},
		error: function(e){
		  jQuery("fail",e);
		}});
}

jQuery(document).ready(function() {
			 var f = jQuery("#tomark");
			 jQuery.ajax({
			   url:"/listit/jv3/intention_notes",
			   type:"GET",
			   dataType:"json",
			   success:function(notes) {
			     var nn = notes.map(function(n) {  return make_note(n);  });
			     nn.map(function(nq) {
				      if (nn.indexOf(nq) % 10 == 0) {
				          var title = jQuery("<p> <span class='set_title'>set "+ (nn.indexOf(nq) + 1) +' to ' + (nn.indexOf(nq) + 10) + ' </span>').appendTo(f);
					  var titletable = jQuery(jQuery(".title")[0]).clone().appendTo(jQuery(f));
					  var thistable = jQuery("<table></table>").appendTo(f);
				        jQuery("<button>submit these 10</button>").click(function(t,ht,tt) {
											     return function() {
											        send(nn.indexOf(nq),(nn.indexOf(nq)+10),  function() {
												       jQuery(t).slideUp();
												       jQuery(ht).slideUp();
												       jQuery(tt).slideUp();
												     });
											        jQuery(this).slideUp(); /* button */
											     };
											   }(thistable,titletable,title)).appendTo(f);
				      }
					jQuery(f.children("table")[jQuery(f).children("table").length - 1]).append(nq);
				      });
			   },error:function(e,v) {
			       console.log("--------------- error", e,v);
			     document.write(e.responseText);
			  }});
			 jQuery(".pricatcol").find("select").live("change", function(evt) {
									     var selected_primary_category = jQuery(this).val();
								    console.log('select',degrees);
								    self.SELECTS = jQuery(jQuery(this).parent().parent()[0]).find(".seccatcol").children("select");

									     jQuery(jQuery(this).parent().parent()[0]).find(".seccatcol").children("select").attr("disabled",false);
								             jQuery(jQuery(this).parent().parent()[0]).find(".seccatcol").children("select").val(degrees[0]);
								             jQuery(jQuery(this).parent().parent()[0]).find(".seccatcol").children("select").filter("."+cat_to_id(selected_primary_category)).val(degrees[4]);
									     jQuery(jQuery(this).parent().parent()[0]).find(".seccatcol").children("select").filter("."+cat_to_id(selected_primary_category)).attr("disabled",true);
									  });
 		       });

function declare_victory() {
  jQuery("#done").fadeIn();
};