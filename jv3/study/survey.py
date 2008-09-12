
import jv3.utils
import jv3.study.exporter

TXT = "textfield"
FR = "textarea"
MC = "radio"
MS = "checkbox"


def show_probe_note(email,jid):
    n = jv3.utils.get_note_by_email_and_jid(email,jid)
    if not n:return "No such note/user"
    responseid = jv3.study.exporter.note_is_probe_response(n)
    return { "text" : """
On note %d, you took down the following information:
<div class=\"note\">%s</div>
""" % (responseid, n.contents) }

def make_header(s):
    return { "text" : "<h3>%s</h3>" % s }

def make_question(id,question,type,choices=None,default_val="",choice_other=False):
    templ = {"qid" : id,
             "type": type,
             "text": question}
    if (choices) : templ["values"] = choices;
    if (default_val) : templ["response"] = default_val
    if (choice_other) : templ["other"] = True
    return templ

common_questions = [
    make_header("Background"),
    make_question("b0", "Your gender", MC, ["Male","Female","N/A"]),
    make_question("b1", "Your age", MC, ["<18","18-25","25-30", "30-35", "35-40", "40-50", "50-65", "65+"]),
    make_question("b2", "Your occuptation/role", MC,
                 ["Student","Engineer","Manager (Product/Sales/Services)", "Advertising", "Artist/Writer", "Journalist", "Musician"], choice_other=True),
    make_question("b3", "Your computers", MS,["Home PC","Work PC", "Laptop", "Cell"], choice_other=True),
    make_question("b4", "Your favorite color", FR),    
    make_header("Personal"),
]

questions_by_user = {}

for u in ['emax@csail.mit.edu']:
    qs = [];
    for q in common_questions: qs.append(q);
    questions_by_user[u] = qs;
                               
