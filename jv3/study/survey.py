
import jv3.utils
import jv3.study.exporter

def make_header(s):
    return { "text" : "<h3>%s</h3>" % s }

def show_probe_note(email,jid):
    n = jv3.utils.get_note_by_email_and_jid(email,jid)
    if not n:return "No such note/user"
    responseid = jv3.study.exporter.note_is_probe_response(n)
    return { "text" : """
On note %d, you took down the following information:
<div class=\"note\">%s</div>
""" % (responseid, n.contents) }

common_questions = {
    "gen": make_header("General"),
    "per": make_header("Personal"),
}
questions_by_user = {
    "emax@csail.mit.edu": [  common_questions["gen"],
                               show_probe_note('emax@csail.mit.edu', '924659'),
                               common_questions["per"],                               
                               { "qid" : "q1",
                                 "type" : "freeresponse",
                                 "text" : "How did you like list.it" },
                               { "qid" : "q2",
                                 "type" : "freeresponse",
                                 "text" : "What did you do today?" },
                               { "qid" : "q3",
                                 "type" : "multiplechoice",
                                 "text" : "What is your favorite variety of coffee",
                                 "values" : ["drip", "espresso", "turkish/greek", "dry grounds"] },
                               { "qid" : "q4",
                                 "type" : "multipleselect",
                                 "text" : "What do you do every day",
                                 "values" : ["Sleep", "eat", "attend seminars", "write chi papers"] },
                               ],
}
    
      
      
