
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
    make_question("b0", "Your gender:", MC, ["Male","Female","Other"]),
    make_question("b1", "Your age:", MC, ["<18","18-25","25-30", "30-35", "35-40", "40-50", "50-65", "65+"]),
    make_question("b2", "Your occupation:", TXT),
    make_question("b3", "Approximately how much time per day do you spend at a computer?", MC, ["< 1hr", "1-5 hrs", "5-10hrs", "> 10hrs"]),
    make_question("b4", "Approximately how many computers do you use during the course of your typical day?", MC, ["0", "1", "2", "3", "4+"]),
    make_text("Please rate how strongly you agree with the following statement:"),
    make_question("b6", "I am a fast typist.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
    make_header("Section 2. About your personal information practice"),
    make_text("What tools or devices do you use to manage..."),
    make_question("pip1", "to-do lists", TXT),
    make_question("pip2", "meeting notes", TXT),
    make_question("pip3", "name or contact information", TXT),
    make_question("pip4", "how-tos", TXT),
    make_question("pip5", "works in progress", TXT),
    make_question("pip6", "references to documents and websites (URLs, file paths, etc)", TXT),
    make_question("pip7", "desired items or wish lists", TXT),
    make_question("pip8", "login/password data", TXT),    
    make_text("Please rate how strongly you agree with the folowing statements:"),
    make_question("pip9", "My to-do lists tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
    make_question("pip10", "My meeting notes tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
    make_question("pip11", "My contact information tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
    make_question("pip12", "My how-tos tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
    make_question("pip13", "My works in progress tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
    make_question("pip14", "My references to documents and websites (URLs, file paths, etc) tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
    make_question("pip15", "My desired items and wish lists tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
    make_question("pip16", "My logins and password data tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
    make_question("pip17", "My personal information is stored primarily in digital tools rather than paper tools.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
    make_question("pip18", "I am most interested in a tool to help me manage:", MC, ["to-dos", "meeting notes", "name or contact information", "how-tos", "works in progress", "references to documents and websites (URLs, file paths, etc)", "desired items or wish lists", "login/password data"],choice_other=True),
    make_question("pip19", "What strategies do you employ to manage the types of personal information above?", FR),
    make_question("pip20", "What portable electronic devices do you use to capture or record personal information, if any?", MS, ["cell phone", "laptop", "pda", "tablet PC"], choice_other=True),
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
    <div class=\"note\" id=\"%(note_div_id)s\"></div>
    </p>
    <script type=\"text/javascript\">$(\"#%(note_div_id)s\").html(toWiky(plumutil.Base64.decode(\"%(note)s\")));</script>
    """
    make_qid = lambda note,qnum: "probe_%d_%d" % (n.jid,qnum)
    qs = [
        make_text(probe_header % {"note":base64.b64encode(n.contents), "note_div_id" : "probe_note_text_%d"%n.jid}),
        make_question(make_qid(n,0), "What is this note?", MS, ["to-do item", "meeting notes", "name or contact information", "instructions or a how-to", "work in progress", "file path or URL", "wishlist of desired items", "login information or password"], choice_other=True),
        make_question(make_qid(n,1), "What purpose did this note serve?", MS, ["Archiving: to hold on to the information for some later time", "Temporary Storage: I needed a place to hold onto the information for just a moment", "Cognitive Support: I was brainstorming or thinking through something 'on paper'", "Reminding: I wanted this note to remind me to do something later", "Unusual Information: I couldn't fit this into any other applications I have"], choice_other=True),
        make_question(make_qid(n,2), "What is the single most important reason you chose list.it for this note rather than another tool?", MC, ["quick input", "note visibility", "quick searchability", "in the browser", "nowhere else to put it"], choice_other=True),
        make_question(make_qid(n,3), "I referenced the information in this note at some point after capturing it.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_question(make_qid(n,4), "I expect that I will need the information in this note some time in the future.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),        
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
                               
