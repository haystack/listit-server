atomate_inits = [];

// designed to be run within a _web page_ not the plugin, so window == "self"
function atomate_initialize(init_cont) {
    try {	
	//console.log("Running full");
	var VERSION = 3;	

    } catch (x) { console.log(x);   }
}

function load_actions() {    
    JV3.xuloadCB("chrome://listit/content/atomate/atomate-growl.js", function(init_fn){ try {  JV3.log("loading growl "); init_fn.apply(JV3,[JV3,JV3.ContextMaiden]); } catch (x) { JV3.log(x); }   });
}
function add_data_sources() {
    saveEntity({ id:"gmail",  type:"schemas.AtomateDatasource",  url:"https://mail.google.com/mail/feed/atom",  username_property:"gmail id", property_to_set:"inbox"  });
    saveEntity({ id:"twitter",  type:"schemas.AtomateDatasource",  url:"http://twitter.com/statuses/user_timeline/%twitterid%.rss", username_property:"twitterid", property_to_set:"tweetbox"  });    
}


// function _augment_entity_DS(entity) {
//     try {
// 	if (entity.statemodel === undefined) return entity;
// 	var edb = JV3.CMS.entity_store;
// 	return entity;
// 	/*
// 	JV3.plumutil.objKeys(entity.statemodel).map(function(smkey) {
// 							JV3.log(smkey);
// 							netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect UniversalBrowserRead");
// 							entity.__defineGetter__(smkey, function() {
// 										    try {
// 											JV3.log(JV3.plumutil.toJSON(entity.statemodel));
// 											var sma = entity.statemodel[smkey];
// 											if (sma && sma.length > 0) {
// 											    JV3.log(sma[sma.length-1][0]);
// 											    return sma[sma.length-1][0];
// 											}
// 											return undefined;
// 										    } catch (x) {
// 											JV3.log(x);
// 										    }
// 										    return undefined;
// 										});
// 							entity.__defineSetter__(smkey, function(val) {
// 										    if (entity.statemodel[smkey] === undefined) {
// 											entity.statemodel[smkey] = [];
// 										    }
// 										    entity.statemodel[smkey].push([val,new Date().valueOf(),-1]);
// 										    return val;
// 										});
// 						    });
// 	 */
//     } catch (x) { JV3.log(x);  }
//     return entity;
// };
// function setDynamicState(entity,prop,val) {
//     try {
// 	//JV3.log("setting dynamic state " + prop + ">> " + JV3.plumutil.toJSON(val));
// 	if (entity.statemodel === undefined) { entity.statemodel = {};}
// 	var proprow  = entity.statemodel[prop] ? entity.statemodel[prop] : [];
// 	proprow.push([val,new Date().valueOf(),-1]);
// 	entity.statemodel[prop] = proprow;
// 	_augment_entity_DS(entity);
// 	JV3.log(entity);
// 	JV3.CMS.entity_store.save(entity);
// 	return entity;	
//     } catch (x) { 
// 	JV3.log(x);
//     }
// };
    
