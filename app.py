from flask import Flask, render_template,request
from googletrans import Translator
import spacy
import re
from googleapiclient.discovery import build
my_api_key = "AIzaSyBc40wiCnh5Wk3e8jGoeHW3DJUWzYQp4cw"
my_cse_id = "015972826494497401252:if2nuu7ieqt"

app = Flask(__name__)

def Translate_the_query(name):
    translator=Translator()
    a=translator.detect(name).lang
    b=translator.translate(name).text
    return(a,b)

def processquestion(qwords): 
    # Find "question word" (what, who, where, etc.)
    yesnowords = ["can", "could", "would", "is", "does", "has", "was", "were", "had", "have", "did", "are", "will"]
    #commonwords = ["the", "a", "an", "is", "are", "were", "."]
    questionwords = ["who", "what", "where", "when", "why", "how", "whose", "which", "whom"]
    questionword = ""
    qidx = -1
    for (idx, word) in enumerate(qwords):
        if word.lower() in questionwords:
            questionword = word.lower()
            qidx = idx
            break
        elif word.lower() in yesnowords:
            return ('YESNO', qwords)
    if qidx < 0:
        return ('MISC', qwords)
    if qidx > len(qwords) - 3:
        target = qwords[:qidx]
    else:
        target = qwords[qidx+1:]
    type = 'MISC'
    # Determine question type
    if questionword in ["who", "whose", "whom"]:
        type = 'PERSON'
    elif questionword == "where":
        type = 'PLACE'
    elif questionword == "when":
        type = 'TIME'
    elif questionword == "how":
        if target[0] in ["few", "little", "much", "many"]:
            type = 'QUANTITY'
            target = target[1:]
        elif target[0] in ["young", "old", "long"]:
            type = 'TIME'
            target = target[1:]
            
    if questionword == "which":
        target = target[1:]
    if target[0] in yesnowords:
        target = target[1:]
    
    # Return question data
    return (type, target)



def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return(res['items'])


def combine_title_snippet(a,b):
    return(a+b)


@app.route('/', methods=['GET', 'POST'])
def index():
    output=[]
    if request.method == 'POST':
        user = request.form['enter_a_question']
        (language_code,user) = Translate_the_query(user)
        qwords =(user.replace('?', ''))
        words=re.split('\s|@|,|.\|!|%|$',qwords)
        qwords=[]
        for i in words:
            if i!='':
                qwords.append(i.lower())
        print(qwords)
        a=''
        a="The question is "+ user
        output.append(a)
        (question_type, target) = processquestion(qwords)
        a="     The answer_type is " +question_type
        output.append(a)
        results = google_search(user, my_api_key, my_cse_id, num=1)
        li3=[]
        li2=[]
        for j in range(0,len(results)):     
            li3.append(results[j]['title'])    
        for i in range(0,len(results)):
            li3.append(results[i]['snippet'])
        li2.append(li3)
        final_answer=combine_title_snippet(li2[0][0],li2[0][1])
        #output=output+" " +final_answer
        model="en_core_web_sm"
        nlp = spacy.load(model)
        #nlp = en_core_web_sm.load()
        doc = nlp(final_answer)
        li5=[]
        li4=([(X.text, X.label_) for X in doc.ents])
        print(li4)
        for (a,b) in li4:
            if(question_type=='PERSON' or question_type=='MISC'):
                if(b=='PERSON'):
                    if a in li5:
                        continue
                    else:
                        li5.append(a)
            if(question_type=='PLACE' or question_type=='MISC'):
                if(b=='LOC' or b=='GPE'):
                    if a in li5:
                        continue
                    else:
                        li5.append(a)
            if(question_type=='QUANTITY' or question_type=='MISC'):
                if(b=='CARDINAL' or b=='ORDINAL' or b=='NUMBER'):
                    if a in li5:
                        continue
                    else:
                        li5.append(a)
            if(question_type=='TIME' or question_type=='MISC'):
                if(b=='TIME' or b=='CARDINAL' or b=='ORDINAL' or b=='NUMBER'):
                    if a in li5:
                        continue
                    else:
                        li5.append(a)
        if(question_type=='YESNO'):
            li5.append('belongs to either YES or NO')
        if (len(li5) != 0):
            output.append("The predicted answer is:")
        a=''
        for i in li5:
            a=a+i
        output.append(a)
    return render_template('index.html',output=output)

if __name__ == '__main__':
    app.run()
