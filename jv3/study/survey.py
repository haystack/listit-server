
import jv3.utils
import jv3.study.exporter
import django.contrib.auth.models as authmodels
import re
import base64

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

def make_text(s):
    return { "text" : "<p>%s</p>" % s }

def make_question(id,question,type,choices=None,default_val="",choice_other=False):
    templ = {"qid" : id,
             "type": type,
             "text": question}
    if (choices) : templ["values"] = choices;
    if (default_val) : templ["response"] = default_val
    if (choice_other) : templ["other"] = True
    return templ

common_questions = [
    make_header("Section 1. Background information"),
    make_question("b0", "Your gender", MC, ["Male","Female","N/A"]),
    make_question("b1", "Your age", MC, ["<18","18-25","25-30", "30-35", "35-40", "40-50", "50-65", "65+"]),
    make_question("b2", "Your occupation", FR),
    make_question("b3", "Approximately how much time per day do you spend at a computer?", MC, ["< 1hr", "1-5 hrs", "5-10hrs", "> 10hrs"]),
    make_question("b4", "Approximately how many computers do you use during the course of your typical day?", MC, ["0", "1", "2", "3", "4+"]),
    make_question("b6", "Are you fast a typist are you (compared to others) ?", MC, ["1 (Not very)", "2", "3", "4", "5", "6", "7 (Very)"]),
    make_header("Section 2. About your personal information practice"),
    make_text("What are the 2 or 3 most important tools you use to manage your personal information?  This includes items like to-do lists, shopping lists, notes, and e-mail."),
    make_question("pip1", "Paper (i.e., sticky notes, sketchbooks, calendars:  ", TXT),
    make_question("pip2", "Digital (i.e., iCal, Outlook, web tools):  ", TXT),
    make_question("pip3", "What tools do you use to manage your to-do lists?  Why?", FR),
    make_question("pip4", "Did you use list.it to manage your to-dos?  Why or why not?", FR),
    make_question("pip5", "What extra features would list.it need to support you in keeping your to-dos?", FR),
    make_question("pip6", "Do you use any personal organizational strategies or systems (such as Getting Things Done) to manage your personal information?", FR),
    make_question("pip7", "Which of the following types of electronic devices do you use to record your personal information?", MS,
                  ["Laptop", "Desktop", "PDA", "Tablet PC", "Mobile Phone"], choice_other=True),
    make_question("pip8", "What sorts of things do you commonly store in these tools?", FR),    
    make_header("Section 3. About your notes"),
]

questions_by_user = {}

def get_non_probe_notes(user):
    print "get non probe notes %d " % len(jv3.models.Note.objects.filter(owner=user))
    return [ n for n in jv3.models.Note.objects.filter(owner=user) if not jv3.study.exporter.note_is_probe_response(n)]

def generate_non_probe_note_questions(n) :
    probe_header = """
    <p>
    In the remainder of this section, we are going to ask you some specific questions about the notes you took with list.it during the study.
    <p>
    You wrote the following note:
    <div class=\"note\" id=\"%(note_div_id)s\">%(note)s</div>
    </p>
    <!--<script type=\"text/javascript\">$(\"#%(note_div_id)s\").html(Wiky.toHtml(plumutil.Base64.decode(\"%(note)s\")));</script>-->
    """
    make_qid = lambda note,qnum: "probe_%d_%d" % (n.jid,qnum)
    print probe_header % {"note":base64.b64encode(n.contents), "note_div_id" : "probe_note_text_%d"%n. jid}
    qs = [
        make_text(probe_header % {"note":re.escape(n.contents), "note_div_id" : "probe_note_text_%d"%n.jid}),
        make_question(make_qid(n,0), "What is this note? (e.g., a to-do, reminder, information for later rerference, draft e-mail, etc?)", FR),
        make_question(make_qid(n,1), "What does this note mean?", FR),
        make_question(make_qid(n,2), "Why did you write this note, i.e., what is its purpose?", FR),
        make_question(make_qid(n,3), "Before installing list.it, would you have put this note in a different tool? If so, what tool?", FR),
        make_question(make_qid(n,4), "Was list.it/would list.it have been a better place for this note that your previous tool? Why or why not?", FR),
        make_question(make_qid(n,5), "If you had taken the note using that different tool,  would it look any different?  Would it contain more information or less?", FR),
        make_question(make_qid(n,6), "How far in the future do you imagine this note will still be relevant?", FR),
        make_question(make_qid(n,7), "How often do you think this note will be referenced before it becomes irrelevant?", FR),
        make_question(make_qid(n,8), "Did you ever look for this note during the course of the study?  Why?  If so, how did you find it?", FR),
        make_question(make_qid(n,9), "Do you think in three months this note would still make sense?" , FR),
        make_question(make_qid(n,10), "Do you think you could relocate this note in three months' time?", FR),        
    ]
    if n.deleted:  qs += make_question(make_qid(n,10), "Why did you delete this note? Did it serve its purpose before you removed it?" , FR),
    qs += [
        # fill me in
    ]
    return qs

for u in ['msbernst@mit.edu']:
    user_obj = authmodels.User.objects.filter(email=u)[0]
    qs = [];
    print "foo"
    for q in common_questions: qs.append(q);
    for n in get_non_probe_notes(user_obj):
        qs = qs + generate_non_probe_note_questions(n)
    questions_by_user[u] = qs;
                               
