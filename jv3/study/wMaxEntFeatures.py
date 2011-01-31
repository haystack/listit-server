## Features for max_ent model
import math
import nltk
from  nltk.corpus import stopwords
import jv3.study.content_analysis as ca
import re

def makeLambda(f,i):
    return lambda x,y:f(x,y,i)

stopWords = set(stopwords.words('english'))
actionWords = ['todo','ToDo','TODO','To-do', 'See', 'see', 'send', 'get', 'call', 'email', 'read', 'Call', 'Set', 'ask', 'Do','do','contact','print','use']

## Helper functions
pos_word     = lambda word: nltk.pos_tag([word])[0][1]
word_is_verb = lambda word: pos_word(word) in ["VB","VBD","VBG","VBN","VBP","VBZ"]
word_is_noun = lambda word: pos_word(word) in ["NN","NNS","NNP","NNPS"]
word_is_det  = lambda word: pos_word(word) == "DT"
count_re     = lambda regexp, txt: len(re.findall(regexp, txt))
count_pos    = lambda words, pos: sum([1 for pair in nltk.pos_tag(words) if pair[1] in pos])
count_array  = lambda words, array: sum([1 for word in words if word in array])
get_posArray = lambda words: [pair[1] for pair in pos_word(words)] ## Returns array of pos tags for each word in wods

## RE_Features
#re_capword = lambda notevals, words: ("5+_allcaps", count_re('[A-Z]+',notevals['contents']) >4)
re_num = lambda notevals, words: ("no_numsbers", count_re('[0-9\-]+', notevals['contents']) == 0)
re_numA = lambda notevals, words: ("1_numbers", count_re('[0-9]+', notevals['contents']) == 1)
re_numB = lambda notevals, words: ("2_numbers", count_re('[0-9:]+', notevals['contents']) == 2)
re_numD = lambda notevals, words: ("4+_numbers", count_re('[0-9\-]+', notevals['contents']) > 2)
no_numword = lambda notevals, words: ("2+_numwords", ca.numword_mix(notevals)['numword_mix'] == 0)

# Revision 1
#re_features=[re_num, re_numA,re_numB,re_numC,re_numD,lb_numword]
re_features=[re_num, re_numD, no_numword] ## HIGH INFORMATION (~3)

## Features
first_word_noun = lambda notevals, words: ("first_word_noun", word_is_noun(words[0]))
first_word_verb = lambda notevals, words: ("first_word_verb", word_is_verb(words[0]))
second_word_verb  = lambda notevals, words: ("second_word_verb", word_is_verb(words[1]) if len(words) > 1 else False)
verb_in_two = lambda notevals, words: ("verb_in_first_two_words", count_pos(words[:min(2,len(words))], ["VB","VBD","VBG","VBN","VBP","VBZ"]))
first_word_det  = lambda notevals, words: ("first_word_det", word_is_det(words[0]))
#first_word = lambda notevals, words: ("first_word_is", words[0]) 
#second_word = lambda notevals, words: ("second_word_is", words[1] if len(words) > 1 else '')
#first_word_symb = lambda notevals, words: ("first_word_symb", count_pos(words[:min(2,len(words))], ["SYM"]))
first_word_stop = lambda notevals, words: ("first_word_stopword", words[0] in stopWords or (len(words) > 1 and words[1] in stopWords) or  (len(words) > 2 and words[2] in stopWords))
first_word_action = lambda notevals, words: ("first_word_symbol", words[0] in actionWords)
first_words_action = lambda notevals, words: ("first_2words_action", words[0] in actionWords or (len(words) > 1 and words[1] in actionWords))#['WDT','WP','WRB','WDT','VBZ'])
first_3words_action = lambda notevals, words: ("first_3words_action", words[0] in actionWords or (len(words) > 1 and words[1] in actionWords) or  (len(words) > 2 and words[2] in actionWords))

word_features = [first_word_action, first_words_action, first_word_stop, first_3words_action]

#count_verbs = lambda notevals, words: ("count_verbs", ca.note_verbs(notevals)['note_verbs'])
#count_urls = lambda notevals, words: ("count_urls", ca.note_urls(notevals)['note_urls'])
#count_numbers = lambda notevals, words: ("count_numbers", ca.numbers(notevals)['numbers'])
#count_todos = lambda notevals, words: ("count_todos", ca.note_todos(notevals)['note_todos'])
#count_names = lambda notevals, words: ("count_names",  ca.note_names(notevals)["names"])
# Counts seem to be overfitting majorly, but also increasing overall accuracy...
count_features = []  ## Not using counts does better!
#count_features = [count_verbs,count_urls,count_numbers,count_todos,count_names]

contains_url = lambda notevals, words: ("contains_url", ca.note_urls(notevals)['note_urls'] > 0)

contains_verbs = lambda notevals, words: ("3+_verbs", ca.note_verbs(notevals)['note_verbs'] >= 3)
contains_dets  = lambda notevals, words: ("1+_det", count_pos(words, ['DT']) > 0)

contains_3_dets  = lambda notevals, words: ("3+_det", count_pos(words, ['DT']) >=3) ## 6 / 17 split
contains_adj = lambda notevals, words: ("1+_adj", count_pos(words, ['JJ', 'JJR', 'JJS']) > 0)
contains_adv = lambda notevals, words: ("1+_adv", count_pos(words, ['RB','RBR','RBS']) > 0)
#contains_linesZ = lambda notevals, words: ("contains_1_line", notevals['contents'].count('\n') == 0)
contains_linesA = lambda notevals, words: ("contains_2+_lines", notevals['contents'].count('\n') >= 1)
contains_linesB = lambda notevals, words: ("3+_lines", notevals['contents'].count('\n') >= 2)
#contains_pronoun = lambda notevals, words: ("1+_pronouns", count_pos(words, ['PRP', 'PRP$']) >= 1)

# contains_verbs .28 # contains_dets .5 # contains_3_dets .2187 # contains_adj .52 # contains_adv .49 # contains_linesB .35

# Revision 1
#contains_features = [contains_verbs, contains_dets, contains_3_dets, contains_adj, contains_adv]#,contains_linesB]#,contains_linesZ,contains_linesA,contains_linesB]#, contains_tabs]
contains_features = [contains_verbs,contains_adj]#, contains_url] ## 

# Testing below features
DOWS=["mon","monday","tue","tuesday","wed","wedmesday","thu","thurs","thursday","fri","friday","sat","saturday","su\
n","sunday"]
contains_dow = lambda notevals, words: ("1+_day_of_week", sum([word.lower() in DOWS for word in words]) > 0) #ca.daysofweek(notevals)['daysofweek'] > 0)
contains_VBZ = lambda notevals, words: ("1+_VBZ", count_pos(words, ['VBZ']) > 0)
contains_stopwds = lambda notevals, words: ("5+_stopwords", count_array(words, stopWords) > 0)
contains_midpunct = lambda notevals, words: ("POS_:", count_pos(words, [':']) > 0)
contains_ending = lambda notevals, words: ("noPOS_.", count_pos(words, ['.']) == 0)
contains_TO = lambda notevals, words: ("POS_TO", count_pos(words, ['TO']) > 0)
contains_MD = lambda notevals, words: ("POS_MD", count_pos(words, ['MD']) > 0) 
contains_INA = lambda notevals, words: ("POS_IN", count_pos(words, ['IN']) == 1)
contains_WDT = lambda notevals, words: ("POS_WDT-WP", count_pos(words, ['WDT','WP','WP$','WRB']) > 0) ## 13/23 split
contains_CD = lambda notevals, words: ("POS_cardinal_number", count_pos(words, ['CD']) > 0)
contains_CC = lambda notevals, words: ("POS_coord_conjunction", count_pos(words, ['CC']) > 0)
contains_todos = lambda notevals, words: ("1+_todos", ca.note_todos(notevals)['note_todos'] > 0)

#contains_nouns = lambda notevals, words: ("contains_nouns", count_pos(words, ['NN, NNS, NNP, NNPS']) > 0)
#contains_PRP = lambda notevals, words: ("POS_PRP", count_pos(words, ['PRP']) > 0)
#contains_INB = lambda notevals, words: ("2+_POS_IN", count_pos(words, ['IN']) > 2)
#contains_names = lambda notevals, words: ("contains_names", ca.note_names(notevals)["names"] > 0)

## UNCOMMENT BELOW NOW !!!
#testing_features = []

# Revision 1
#testing_features = [contains_pronoun,contains_VBZ,contains_stopwds, contains_CC,contains_CD,contains_INA, contains_INB,contains_WDT, contains_PRP, contains_ending, contains_midpunct]
#testing_features.extend([contains_dow,contains_todos])
#testing_features = [contains_stopwds,contains_CC,contains_CD,contains_todos,contains_INA,contains_INB,contains_PRP, contains_ending, contains_midpunct]
testing_features = [contains_stopwds,contains_todos,contains_INA, contains_ending, contains_midpunct]


contains_noperiod = lambda notevals, words: ("0_period", count_re('[\.]', notevals['contents']) == 0)
contains_period = lambda notevals, words: ("1+_period", count_re('[\.]', notevals['contents']) > 0)
contains_periodA = lambda notevals, words: ("2+_periods", count_re('[\.]', notevals['contents']) > 1)
contains_comma = lambda notevals, words: ("1+_comma", count_re('[\,]', notevals['contents']) > 0)
contains_qmark = lambda notevals, words: ("1+_qmark", count_re('[\?]', notevals['contents']) > 0)
contains_qmarkA = lambda notevals, words: ("1+_qmark", count_re('[\?]', notevals['contents']) == 0)
contains_semicolon = lambda notevals, words: ("1+_semicolon", count_re('[\;]', notevals['contents']) > 0)
contains_colon = lambda notevals, words: ("1+_colon", count_re('[\:]', notevals['contents']) > 0)
contains_and = lambda notevals, words: ("1+_&", count_re('\&+', notevals['contents']) > 0 )
contains_hash = lambda notevals, words: ("1+_#", count_re('[\#]', notevals['contents']) > 0)
contains_dash =  lambda notevals, words: ("1+_-", count_re('[\-]', notevals['contents']) > 0)

#contains_exmark = lambda notevals, words: ("1+_exmark",  count_re('[\!]', notevals['contents']) > 0)
#contains_atsymb = lambda notevals, words: ("1+_@", count_re('[\@]', notevals['contents']) > 0)
#contains_dollarsign = lambda notevals, words: ("1+_$", count_re('[\$]', notevals['contents']) > 0)
#contains_perc = lambda notevals, words: ("1+_%", count_re('[\%]', notevals['contents']) > 0)
#contains_caret = lambda notevals, words: ("1+_^", count_re('[\^]', notevals['contents']) > 0)
#contains_star = lambda notevals, words: ("1+_*", count_re('[\*]', notevals['contents']) > 0)
#contains_plus =  lambda notevals, words: ("1+_+", count_re('[\+]', notevals['contents']) > 0)
#contains_quotes = lambda notevals, words: ("1+_quotes", count_re('[\'\"]', notevals['contents']) > 0)
#contains_parens =  lambda notevals, words: ("1+_parens", count_re('[\(\)]', notevals['contents']) > 0)
#contains_brackets = lambda notevals, words: ("1+_brackets", count_re('[\[\]]', notevals['contents']) > 0)

#punct_features = [contains_period,contains_comma,contains_qmark,contains_exmark,contains_semicolon,contains_colon,contains_quotes]
# contains_period .38 # contains_comma .32  # contains_qmark .23  # contains_semicolon .235   # contains_colon .329

# Revision 1
#punct_features = [contains_and,  contains_period, contains_periodA,contains_comma,contains_qmark,contains_semicolon,contains_colon,contains_brackets]#contains_quotes,contains_parens,contains_brackets]
#punct_features = [contains_noperiod,contains_period,contains_periodA,contains_qmark,contains_semicolon,contains_colon,contains_hash,contains_dash]
punct_features = [contains_noperiod,contains_period,contains_periodA,contains_qmarkA,contains_colon,contains_hash,contains_dash,contains_qmarkA]


threshold_features = []
def thresholdMaker(funcs, a,b,interval=1):
    global threshold_features
    for i in range(a,b,interval):
        for f in funcs:
            threshold_features.append(makeLambda(f,i))

## Threshold Functions ##
lb_actwds = lambda notevals, words: ("1+_actwords", count_array(words, actionWords) >= 1)
basic_threshold = [lb_actwds]

## Upper bound
ub_characters = lambda notevals, words, k: ("%s-_chars"%(k),  len(notevals['contents']) <= k)
lb_characters = lambda notevals, words, k: ("%s+_chars"%(k),  len(notevals['contents']) >= k)
## Really low weights - too sparse it seems
## Addition #2
thresholdMaker([ub_characters],4,44,4)    ## -- high information feature
thresholdMaker([lb_characters],80,120,10) ## no noticable change on F1

#threshold_lines = lambda notevals, words, k: ("contains_<=%s_lines"%(k), notevals['contents'].count('\n') <= k)
##threshold_stpwds = lambda notevals, words, k: ("contains_<=%s_stopwords"%(k), count_array(words, stopWords) <= k)

## Lower bound
## Testing 4:32pm
lb_words = lambda notevals, words, k: ("%s+_words"%(k), len(words) >= k)
#thresholdMaker([ub_words],30,41,5) ## okay
lb_lines = lambda notevals, words, k: ("%s+_lines"%(k), notevals['contents'].count('\n') >= k)
#?? ?? ?? ?? ?? NO NO NO ?? ?? ?? ?? ??thresholdMaker([lb_lines],2,11)#was 1,11 BAD
#lb_stpwds = lambda notevals, words, k: ("contains_>=%s_stopwords"%(k), count_array(words, stopWords) >= k)

## Fewer than k words per line on average
ub_linelength = lambda notevals, words, k: ("s-_words/line"%(k), len(words) <= k*(1+notevals['contents'].count('\n')))
lb_linelength = lambda notevals, words, k: ("%s+_words/line"%(k), len(words) >= k*(1+notevals['contents'].count('\n')))



charB = 10.0
k_chars = lambda notevals, words, k: ("[%s-%s]_chars"%(charB*int(math.floor(k/charB)), charB*int(math.floor(k/charB))+charB-1), charB*int(math.floor(len(notevals['contents'])/charB)) == charB*int(math.floor(k/charB)))
#thresholdMaker([k_chars],10,30,10) #2:24am sat -testing change 100 to 30  ?? ARGH? -- too imprecise / messy


## ADD BELOW BACK IN UNLESS STELLAR IMPROVEMENTS -- got slightly higher F2 without these, but also got one lower... seems one of these may be troublesome!
k_words = lambda notevals, words, k: ("%s_words"%(k),  len(words) == k)
#thresholdMaker([k_words], 1,10)
k_lines = lambda notevals, words, k: ("%s_lines"%(k), notevals['contents'].count('\n')+1 == k)
#thresholdMaker([k_lines],1,8) 
k_linelength = lambda notevals, words, k: ("%s_words/line"%(k), len(words) in range((k-1)*(1+notevals['contents'].count('\n')),k*(1+notevals['contents'].count('\n'))))
#thresholdMaker([k_linelength], 1,11) ## 10 seems to identify mem trigger, not right seeming...


#thresholdMaker([ub_characters],15,60,5)


# Addition 
###thresholdMaker([lb_characters],60,120,10)
#thresholdMaker([ub_words],30,41,5) ## okay
# third worst?
#thresholdMaker([k_chars],10,30,10) #2:24am sat -testing change 100 to 30  ?? ARGH? -- too imprecise / messy
#thresholdMaker([k_words], 1,10)
#thresholdMaker([k_lines],1,2)
#thresholdMaker([k_linelength],1, 12) ## 10 seems to identify mem trigger, not right seeming...

k_wdlen = lambda notevals, words, k:("first-word-len:%s"%(k), len(words[0]) == k)


## Addition Group 1: +1.35% F1 score
## Newest additions!
k_punct = lambda notevals, words, k: ("%s_note_punct"%(k), count_re('[\.\,\'\:\;\?]',notevals['contents']) == k)
thresholdMaker([k_punct], 0,2)
thresholdMaker([k_punct], 3,5)
lb_punct =  lambda notevals, words, k: ("%s+_note_punct"%(k), count_re('[\.\,\'\:\;\?]',notevals['contents']) >= k)
thresholdMaker([lb_punct], 2,6)
k_numword = lambda notevals, words, k: ("%s_numwords"%(k), count_re("(^|\s+)(.*\d.*)($|\s+)",notevals['contents']) == k)
thresholdMaker([k_numword],0,2) 
k_stpwds = lambda notevals, words, k: ("%s_stopwords"%(k), count_array(words, stopWords) == k)
thresholdMaker([k_stpwds],1,2)

arraySW = [wd for wd in stopWords]

features = []
features.extend(word_features)
features.extend(re_features)
features.extend(count_features)
features.extend(contains_features)
features.extend(punct_features)
features.extend(testing_features)
features.extend(basic_threshold)
features.extend(threshold_features)
