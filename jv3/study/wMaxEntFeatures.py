## Features for max_ent model
import math
import nltk
from  nltk.corpus import stopwords
import jv3.study.content_analysis as ca
import re

def makeLambda(f,i):
    return lambda x,y:f(x,y,i)

stopWords = set(stopwords.words('english'))
actionWords = ['todo','ToDo','TODO', 'See', 'see', 'send', 'get', 'call', 'email', 'read', 'Call', 'Set', 'ask', 'Do','do','contact','print','use']

pos_word     = lambda word: nltk.pos_tag([word])[0][1]
word_is_verb = lambda word: pos_word(word) in ["VB","VBD","VBG","VBN","VBP","VBZ"]
word_is_noun = lambda word: pos_word(word) in ["NN","NNS","NNP","NNPS"]
word_is_det  = lambda word: pos_word(word) == "DT"
count_re     = lambda regexp, txt: len(re.findall(regexp, txt))
count_pos    = lambda words, pos: sum([1 for pair in nltk.pos_tag(words) if pair[1] in pos])
count_array  = lambda words, array: sum([1 for word in words if word in array])
get_posArray = lambda words: [pair[1] for pair in pos_word(words)] ## Returns array of pos tags for each word in wods

## RE_Features
re_capword = lambda notevals, words: ("5+_allcaps", count_re('[A-Z]+',notevals['contents']) >4)
re_num = lambda notevals, words: ("no_numsbers", count_re('[0-9.,/:]+', notevals['contents']) == 0)
re_numA = lambda notevals, words: ("1_numbers", count_re('[0-9.,/:]+', notevals['contents']) == 1)
re_numB = lambda notevals, words: ("2_numbers", count_re('[0-9.,/:]+', notevals['contents']) == 2)
re_numC = lambda notevals, words: ("3_numbers", count_re('[0-9.,/:]+', notevals['contents']) == 3)
re_numD = lambda notevals, words: ("4+numbers", count_re('[0-9.,/:]+', notevals['contents']) > 3)
lb_numword = lambda notevals, words: ("2+_numwords", ca.numword_mix(notevals)['numword_mix'] > 1)

#k_test = lambda notevals, words, k: ("%s_numwords"%(k), ca.urls_over_length(notevals)[''] == k)
#   k_test = lambda notevals, words, k: ("%s_numwords"%(k), count_re( , notevals['contents']) == k)
#re_name_len = lambda notevals, words: ("names/length", ca.(notevals)[''] > .005)

re_features=[re_num, re_numA,re_numB,re_numC,re_numD,lb_numword]

## Features
first_word_noun = lambda notevals, words: ("first_word_noun", word_is_noun(words[0]))
first_word_verb = lambda notevals, words: ("first_word_verb", word_is_verb(words[0]))
second_word_verb  = lambda notevals, words: ("second_word_verb", word_is_verb(words[1]) if len(words) > 1 else False)
verb_in_two = lambda notevals, words: ("verb_in_first_two_words", count_pos(words[:min(2,len(words))], ["VB","VBD","VBG","VBN","VBP","VBZ"]))
first_word_det  = lambda notevals, words: ("first_word_det", word_is_det(words[0]))
first_word = lambda notevals, words: ("first_word_is", words[0]) 
second_word = lambda notevals, words: ("second_word_is", words[1] if len(words) > 1 else '')
#first_word_symb = lambda notevals, words: ("first_word_symb", count_pos(words[:min(2,len(words))], ["SYM"]))
first_word_stop = lambda notevals, words: ("first_word_stop", words[0] in stopWords or (len(words) > 1 and words[1] in stopWords) or  (len(words) > 2 and words[2] in stopWords))
first_word_action = lambda notevals, words: ("first_word_symb", words[0] in actionWords)
first_words_action = lambda notevals, words: ("first_2words_action", words[0] in actionWords or (len(words) > 1 and words[1] in actionWords))#['WDT','WP','WRB','WDT','VBZ'])
first_3words_action = lambda notevals, words: ("first_3words_action", words[0] in actionWords or (len(words) > 1 and words[1] in actionWords) or  (len(words) > 2 and words[2] in actionWords))

word_features = [first_word_det, first_word_verb,second_word_verb, first_word_action, first_words_action, first_word_stop, first_3words_action]
## trying to add things here!

count_verbs = lambda notevals, words: ("count_verbs", ca.note_verbs(notevals)['note_verbs'])
count_urls = lambda notevals, words: ("count_urls", ca.note_urls(notevals)['note_urls'])
count_numbers = lambda notevals, words: ("count_numbers", ca.numbers(notevals)['numbers'])
count_todos = lambda notevals, words: ("count_todos", ca.note_todos(notevals)['note_todos'])
count_names = lambda notevals, words: ("count_names",  ca.note_names(notevals)["names"])

# Counts seem to be overfitting majorly, but also increasing overall accuracy...
#count_features = []  ## Not using counts does better!
#count_features = [count_verbs,count_urls,count_numbers,count_todos,count_names]

contains_url = lambda notevals, words: ("contains_url", ca.note_urls(notevals)['note_urls'] > 0)
contains_verbs = lambda notevals, words: ("contains_3+_verbs", ca.note_verbs(notevals)['note_verbs'] >= 3)
contains_dets  = lambda notevals, words: ("contains_det", count_pos(words, ['DT']) > 0)
contains_3_dets  = lambda notevals, words: ("contains_3+_det", count_pos(words, ['DT']) >=3)
contains_adj = lambda notevals, words: ("contains_adj", count_pos(words, ['JJ', 'JJR', 'JJS']) > 0)
contains_adv = lambda notevals, words: ("contains_adv", count_pos(words, ['RB','RBR','RBS']) > 0)
#contains_linesZ = lambda notevals, words: ("contains_1_line", notevals['contents'].count('\n') == 0)
#contains_linesA = lambda notevals, words: ("contains_2+_lines", notevals['contents'].count('\n') >= 1)
contains_linesB = lambda notevals, words: ("contains_3+_lines", notevals['contents'].count('\n') >= 2)
contains_pronoun = lambda notevals, words: ("contains_1+_pronouns", count_pos(words, ['PRP', 'PRP$']) >= 1)
#0.001 weight - contains_participle =  lambda notevals, words: ("contains_1+_participle", count_pos(words, ['RP']) >= 1)

# contains_verbs .28 # contains_dets .5 # contains_3_dets .2187 # contains_adj .52 # contains_adv .49 # contains_linesB .35
contains_features = [contains_verbs, contains_dets, contains_3_dets, contains_adj, contains_adv,contains_linesB]#,contains_linesZ,contains_linesA,contains_linesB]#, contains_tabs]#, contains_stopwds]
#contains_features.extend([contains_url])
#contains_features = [contains_dow, contains_nouns, contains_verbs, contains_dets, contains_3_dets, contains_adj, contains_adv, contains_symb]#, contains_predet]

# Testing below features
DOWS=["mon","monday","tue","tuesday","wed","wedmesday","thu","thurs","thursday","fri","friday","sat","saturday","su\
n","sunday"]
contains_dow = lambda notevals, words: ("contains_day_of_week", sum([word.lower() in DOWS for word in words]) > 0) #ca.daysofweek(notevals)['daysofweek'] > 0)
#contains_nouns = lambda notevals, words: ("contains_nouns", count_pos(words, ['NN, NNS, NNP, NNPS']) > 0)
contains_VBZ = lambda notevals, words: ("contains_VBZ", count_pos(words, ['VBZ']) > 0)
contains_stopwds = lambda notevals, words: ("contains_5+_stopwords", count_array(words, stopWords) > 4)
#contains_tabs    = lambda notevals, words: ("contains_tabs", notevals['contents'].find('\t') != -1)
#contains_symb = lambda notevals, words: ("contains_symbols", count_pos(words, ['SYM']) > 0)

contains_midpunct = lambda notevals, words: ("POS_:", count_pos(words, [':']) > 0)
contains_ending = lambda notevals, words: ("POS_.", count_pos(words, ['.']) > 0)
contains_TO = lambda notevals, words: ("POS_TO", count_pos(words, ['TO']) > 0)
contains_PRP = lambda notevals, words: ("POS_PRP", count_pos(words, ['PRP']) > 0)
contains_MD = lambda notevals, words: ("POS_MD", count_pos(words, ['MD']) > 0) 
contains_INA = lambda notevals, words: ("POS_IN", count_pos(words, ['IN']) == 1)
contains_INB = lambda notevals, words: ("POS_IN_2+", count_pos(words, ['IN']) > 2)
contains_WDT = lambda notevals, words: ("POS_WDT-WP", count_pos(words, ['WDT','WP','WP$','WRB']) > 0) ## 13/23 split
contains_CD = lambda notevals, words: ("POS_cardinal_number", count_pos(words, ['CD']) > 0)
contains_CC = lambda notevals, words: ("POS_coord_conjunction", count_pos(words, ['CC']) > 0)
contains_todos = lambda notevals, words: ("contains_todos", ca.note_todos(notevals)['note_todos'] > 0)
#contains_names = lambda notevals, words: ("contains_names", ca.note_names(notevals)["names"] > 0)

# .5  # .48  # .42
## UNCOMMENT BELOW NOW !!!
#testing_features = []
testing_features = [contains_pronoun,contains_VBZ,contains_stopwds, contains_CC,contains_CD,contains_INA, contains_INB,contains_WDT, contains_PRP, contains_ending, contains_midpunct]
testing_features.extend([contains_dow,contains_todos])

contains_period = lambda notevals, words: ("contains_1+_period", count_re('[\.]', notevals['contents']) > 0)
contains_periodA = lambda notevals, words: ("contains_2+_periods", count_re('[\.]', notevals['contents']) > 1)
contains_comma = lambda notevals, words: ("contains_comma", count_re('[\,]', notevals['contents']) > 0)
contains_qmark = lambda notevals, words: ("contains_qmark", count_re('[\?]', notevals['contents']) > 0)
contains_exmark = lambda notevals, words: ("contains_exmark",  count_re('[\!]', notevals['contents']) > 0)
contains_semicolon = lambda notevals, words: ("contains_semicolon", count_re('[\;]', notevals['contents']) > 0)
contains_colon = lambda notevals, words: ("contains_colon", count_re('[\:]', notevals['contents']) > 0)
contains_and = lambda notevals, words: ("contains_&", count_re('[\&]', notevals['contents']) > 0 )
contains_atsymb = lambda notevals, words: ("contains_@", count_re('[\@]', notevals['contents']) > 0)
contains_hash = lambda notevals, words: ("contains_#", count_re('[\#]', notevals['contents']) > 0)
contains_dollarsign = lambda notevals, words: ("contains_$", count_re('[\$]', notevals['contents']) > 0)

contains_perc = lambda notevals, words: ("contains_%", count_re('[\%]', notevals['contents']) > 0)
contains_caret = lambda notevals, words: ("contains_^", count_re('[\^]', notevals['contents']) > 0)
contains_star = lambda notevals, words: ("contains_*", count_re('[\*]', notevals['contents']) > 0)
contains_plus =  lambda notevals, words: ("contains_+", count_re('[\+]', notevals['contents']) > 0)

contains_dash =  lambda notevals, words: ("contains_-", count_re('[\-]', notevals['contents']) > 0)
contains_quotes = lambda notevals, words: ("contains_quotes", count_re('[\'\"]', notevals['contents']) > 0)
contains_parens =  lambda notevals, words: ("contains_parens", count_re('[\(\)]', notevals['contents']) > 0)
contains_brackets = lambda notevals, words: ("contains_brackets", count_re('[\[\]]', notevals['contents']) > 0)

#punct_features = [contains_period,contains_comma,contains_qmark,contains_exmark,contains_semicolon,contains_colon,contains_quotes]
# contains_period .38 # contains_comma .32  # contains_qmark .23  # contains_semicolon .235   # contains_colon .329
punct_features = [contains_and,  contains_period, contains_periodA,contains_comma,contains_qmark,contains_semicolon,contains_colon,contains_brackets]#contains_quotes,contains_parens,contains_brackets]

threshold_features = []
def thresholdMaker(funcs, a,b,interval=1):
    global threshold_features
    for i in range(a,b,interval):
        for f in funcs:
            threshold_features.append(makeLambda(f,i))

## Threshold Functions ##
lb_actwds = lambda notevals, words: ("contains_>=1_actwords", count_array(words, actionWords) >= 1)
basic_threshold = [lb_actwds]

## Upper bound
ub_characters = lambda notevals, words, k: ("contains_<=%s_chars"%(k),  len(notevals['contents']) <= k)
lb_characters = lambda notevals, words, k: ("contains_>=%s_chars"%(k),  len(notevals['contents']) >= k)
## Really low weights - too sparse it seems
#thresholdMaker([ub_characters],0,81,5)
#thresholdMaker([lb_characters],80,160,10)

ub_words = lambda notevals, words, k: ("contains_<=%s_words"%(k), len(words) >= k)
#testing removal 2:24am Sat morn
#thresholdMaker([ub_words],1,6)

#threshold_lines = lambda notevals, words, k: ("contains_<=%s_lines"%(k), notevals['contents'].count('\n') <= k)
#threshold_stpwds = lambda notevals, words, k: ("contains_<=%s_stopwords"%(k), count_array(words, stopWords) <= k)

## Lower bound
## Testing 4:32pm
lb_characters = lambda notevals, words, k: ("contains_>=%s_chars"%(k),  len(notevals['contents']) >= k)
thresholdMaker([lb_characters],100,141,40) #-- low weights :(  DONT USE!
lb_words = lambda notevals, words, k: ("contains_>=%s_words"%(k), len(words) >= k)
thresholdMaker([ub_words],30,41,5) ## okay
lb_lines = lambda notevals, words, k: ("contains_>=%s_lines"%(k), notevals['contents'].count('\n') >= k)
#?? ?? ?? ?? ?? NO NO NO ?? ?? ?? ?? ??thresholdMaker([lb_lines],2,11)#was 1,11 BAD
#lb_stpwds = lambda notevals, words, k: ("contains_>=%s_stopwords"%(k), count_array(words, stopWords) >= k)

## Fewer than k words per line on average
ub_linelength = lambda notevals, words, k: ("linelength_<=%s"%(k), len(words) <= k*(1+notevals['contents'].count('\n')))
lb_linelength = lambda notevals, words, k: ("linelength_>=%s"%(k), len(words) >= k*(1+notevals['contents'].count('\n')))


k_characters = lambda notevals, words, k: ("%s_chars"%(int(4*math.floor(k/4.0))), len(notevals['contents']) == int(4*math.floor(k/4.0)))
################### thresholdMaker([k_characters],0,41,4) #2:24am sat -testing change 100 to 30

k_words = lambda notevals, words, k: ("contains_==%s_words"%(k),  len(words) == k)
thresholdMaker([k_words], 1,10)
k_lines = lambda notevals, words, k: ("contains_==%s_lines"%(k), notevals['contents'].count('\n')+1 == k)
thresholdMaker([k_lines],1,8) ## 2,7
## Removed 4:29pm
k_linelength = lambda notevals, words, k: ("linelength_==%s"%(k), len(words) == k*(1+notevals['contents'].count('\n')))
thresholdMaker([k_linelength], 1,11) ## 10 seems to identify mem trigger, not right seeming...

k_wdlen = lambda notevals, words, k:("first-word-len:%s"%(k), len(words[0]) == k)


## neat idea but doesn't show any particular gain for (1,13) or (1,6)
char_a = lambda notevals,words,k:("Contains_%s+_a"%(k),count_re('[a]', notevals['contents']) >= k)
char_e = lambda notevals,words,k:("Contains_%s+_e"%(k),count_re('[e]', notevals['contents']) >= k)
char_i = lambda notevals,words,k:("Contains_%s+_i"%(k),count_re('[i]', notevals['contents']) >= k)
char_o = lambda notevals,words,k:("Contains_%s+_o"%(k),count_re('[o]', notevals['contents']) >= k)
char_u = lambda notevals,words,k:("Contains_%s+_u"%(k),count_re('[u]', notevals['contents']) >= k)
#thresholdMaker([char_a],1,6) ## Overall these lower accuracy a lot
#thresholdMaker([char_e],1,6)     # Useless: 9
#thresholdMaker([char_i],1,6)     # Useless:      #Helpful: 11
#thresholdMaker([char_o],1,6)     # Useless: 2, 
#thresholdMaker([char_u],1,6)    # Useless: 

## Newest additions!
k_punct = lambda notevals, words, k: ("%s_note_punct"%(k), count_re('[\.\,\'\:\;\?]',notevals['contents']) == k)
thresholdMaker([k_punct], 0,5)
k_numword = lambda notevals, words, k: ("%s_numwords"%(k), count_re("(^|\s+)(.*\d.*)($|\s+)",notevals['contents']) == k)
thresholdMaker([k_numword],0,2) ## For only 1

arraySW = [wd for wd in stopWords]

features = word_features
features.extend(re_features)
features.extend(count_features)
features.extend(contains_features)
features.extend(punct_features)
features.extend(testing_features)
features.extend(basic_threshold)
features.extend(threshold_features)
