import sys
import os
import time
import json
sys.path.insert(0, os.path.dirname(__file__))
from io import BytesIO
from flask import Flask,jsonify,send_file
from flask import make_response, request, current_app
from flask import render_template, flash,redirect
from gensim.models import KeyedVectors
import gensim.downloader as api
from werkzeug.utils import secure_filename
import sqlite3
from flask import Flask,jsonify,url_for
from flask import make_response, request, current_app
from flask import render_template
import pandas as pd
from flask_session import Session
from flask import session
import sqlite3
from datetime import datetime
from topic_modeler  import TopicModeler
from flask import render_template_string
from flask import send_from_directory
#from gevent.pywsgi import WSGIServer
#from gevent import monkey

# need to patch sockets to make requests async
# you may also need to call this before importing other packages that setup ssl
#monkey.patch_all()


UPLOAD_FOLDER = './tmp/'
model_base = './srv/data/judel/models/'

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Session(app)

topic_modeler = TopicModeler(20)



ALLOWED_EXTENSIONS = set(['csv','xlsx','txt'])

db_name = 'TMS'




@app.route('/save_rel',methods=['POST'])
def save_rel():

    try:
        json_data = request.get_json()
        id_ = json_data['id']
        ts = json_data['ts']
        rel = json_data['rel']
        print(id_,ts,rel,flush=True)
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("INSERT INTO RELEVANCE VALUES (?,?,?)",[id_,ts,rel])
        con.commit()
        con.close()
        session['rel'][id_] = rel

        return jsonify(msg="success",code=0)
    except Exception as e:
        print("exception",e)
        return jsonify(msg = str(e),code=1)

@app.route('/save_note',methods=['POST'])
def save_note():

    try:
        json_data = request.get_json()
        id_ = json_data['id']
        ts = json_data['ts']
        note = json_data['note']
        print(id_,ts,note,flush=True)
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("INSERT INTO NOTE VALUES (?,?,?)",[id_,ts,note])
        con.commit()
        con.close()
        session['note'][id_] = note

        return jsonify(msg="success",code=0)
    except Exception as e:
        print("exception",e)
        return jsonify(msg = str(e),code=1)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[-1] in ALLOWED_EXTENSIONS


def load_model(model_path):
    return KeyedVectors.load(model_path, mmap='r')


def find_sim(word, model_path=None, topn=100):
    if model_path is None:
        word2vec = api.load('word2vec-google-news-300')
    else:
        word2vec = load_model(model_path)
    try:
        sim_words = word2vec.most_similar(word, topn=topn)
    except Exception as e:
        print(e)
        sim_words = []
    format_sim_words = []
    for w,s in sim_words:
        format_sim_words.append((w,f'{s:.2f}'))
    return format_sim_words


def modelList():
    models = []
    for f in sorted(os.listdir(model_base),reverse=True):
        if f.endswith('.w2v'):
            models.append(f)
    models.append('google_news.w2v')
    return models

def read_file(filename):

    if filename.rsplit('.', 1)[1] == 'csv':
        df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    elif filename.rsplit('.', 1)[1] == 'xlsx':
        df = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    fts = []
    titles = []
    ids = []

    try:
        nfts = df['fulltext'].to_list()
        for ft in nfts:
            fts.append(ft.replace('\n','.<br>'))
        titles = df['title'].to_list()
        try:
            ids = df['_id'].to_list()
        except:
            ids = list(range(len(fts)))
        for x,i in enumerate(ids):
            ids[x] = '.'.join(filename.split('.')[:-1]).replace('.','dot')+str(i)

        # print(fts,titles)
    except Exception as e:
        #print(e,flush=True)
        return 1,str(e),0,fts,titles,ids
    return 0,"",len(fts),titles,fts,ids


@app.route('/select/<filename>', methods=['GET','POST'])
def select(filename):
    totResults = 0
    numResults = 0
    curStart = 0
    alltitles = []
    allfts = []
    allids = []

    status, msg, totResults, alltitles, allfts, allids = read_file(filename)
    numResults = min(10,totResults-curStart)
    #print(numResults,status,allids,flush=True)
    if status==1:
        flash(msg,'error')
    session['file'] = filename
    session['note'] = read_sql('.'.join(filename.split('.')[:-1]).replace('.','dot'),'NOTE','note')
    session['rel'] = read_sql('.'.join(filename.split('.')[:-1]).replace('.','dot'),'RELEVANCE','rel')
    session['curStart'] = curStart
    session['allids'] = allids
    session['allfts'] = allfts
    session['alltitles'] = alltitles
    session['numResults'] = numResults
    session['totResults'] = totResults

    return redirect('https://127.0.0.1:6600/tms/annotate')


def read_sql(doc_name,tbl_name,col_name):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    cmd = "SELECT * from " +  tbl_name
    cur.execute(cmd+" where docid LIKE (?) order by CAST(ts as REAL) asc",[doc_name+'%'])
    results = {}
    desc = cur.description
    column_names = [col[0] for col in desc]

    for row in cur.fetchall():
            id_ = ''
            val = ''
            for idx,c in enumerate(row):
                if column_names[idx] == 'docid':
                    id_ = c


                elif column_names[idx] == col_name:

                    val = c


            results[id_] = val
    # print(results)
    con.commit()
    con.close()
    return results




@app.route('/upload', methods=['GET','POST'])
def upload():
    totResults = 0
    numResults = 0
    curStart = 0
    alltitles = []
    allfts = []
    allids = []

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part','error')
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file','error')

        if file:
            if not allowed_file(file.filename):
                flash('Please upload a csv or excel','error')

            else:
                filename = secure_filename(file.filename)
                if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                    now = datetime.now()

                    dt_string = now.strftime("%d%m%Y_%H:%M:%S")

                    filename = '.'.join(filename.split('.')[:-1]) + dt_string + '.' + filename.split('.')[-1]
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                status, msg, totResults, alltitles, allfts, allids = read_file(filename)
                numResults = min(10,totResults-curStart)
                if status==1:
                    flash(msg,'error')
                session['file'] = filename
                session['curStart'] = curStart
                session['allids'] = allids
                session['allfts'] = allfts
                session['alltitles'] = alltitles
                session['numResults'] = numResults
                session['totResults'] = totResults
                session['note'] = read_sql('.'.join(filename.split('.')[:-1]).replace('.','dot'),'NOTE','note')
                session['rel'] = read_sql('.'.join(filename.split('.')[:-1]).replace('.','dot'),'RELEVANCE','rel')

        return redirect('https://127.0.0.1:6600/tms/annotate')

@app.route('/tms/upload_topic', methods=['GET','POST'])
def upload_topic():
    totResults = 0
    numResults = 0
    curStart = 0
    alltitles = []
    allfts = []
    allids = []
    topic_modeler.temp_dir_

    if request.method == 'POST':
        # check if the post request has the file part
        if 'files[]' not in request.files:
            flash('No file part','error')
        #file = request.files['file']
        files = request.files.getlist('files[]')
        print('-------')
        for file in files:
          print(file)
          upload_file_for_topic_model(file)
        print('-------')
        return redirect('http://127.0.0.1:6600/tms/topicmodeling')
        # if user does not select file, browser also
        # submit a empty part without filename

def upload_file_for_topic_model(file):
        if file.filename == '':
            flash('No selected file','error')
        if file:
            if not allowed_file(file.filename):
                flash('Please upload a csv or excel or txt','error')
            else:
                filename = secure_filename(file.filename)
                print(filename)
                if os.path.exists(os.path.join(topic_modeler.temp_dir_, filename)):
                    now = datetime.now()

                    dt_string = now.strftime("%d%m%Y_%H:%M:%S")

                    filename = '.'.join(filename.split('.')[:-1]) + dt_string + '.' + filename.split('.')[-1]
                file.save(os.path.join(topic_modeler.temp_dir_, filename))
                topic_modeler.add_file(topic_modeler.temp_dir_+filename)

        return redirect('http://127.0.0.1:6600/tms/topicmodeling')

def read_session():
    curStart = 0
    allids = []
    allfts = []
    alltitles = []
    numResults = 0
    totResults = 0
    note = {}
    rel = {}
    try:
        curStart = session['curStart']
        allids = session['allids']
        allfts = session['allfts']
        alltitles = session['alltitles']
        numResults = session['numResults']
        totResults = session['totResults']
        note = session['note']
        rel = session['rel']
    except:
        pass
    return curStart,numResults,totResults,alltitles,allfts,allids,note,rel

@app.route('/annotate', methods=['GET'])
def annotate():
    collections = list(os.listdir(UPLOAD_FOLDER))
    try:
        collections.remove('.DS_Store')
    except:
        pass
    curStart,numResults,totResults,alltitles,allfts,allids,note,rel = read_session()

    filtered_notes = []
    filtered_rel = []
    for id_ in allids[curStart:curStart+numResults]:
        try:
            filtered_notes.append(note[id_])
        except:
            filtered_notes.append('')
        try:
            filtered_rel.append(rel[id_])
        except:
            filtered_rel.append('')
    #print(filtered_rel,filtered_notes)


    return render_template('annotate.html',totResults=totResults,numResults=numResults,titles=alltitles[curStart:curStart+numResults],fts=allfts[curStart:curStart+numResults],ids=allids[curStart:curStart+numResults],curStart=curStart,collections=collections,note=filtered_notes,rel=filtered_rel)


@app.route('/export', methods=['POST','GET'])
def export():
    try:
        doc_name = session['file']
    except:
        flash('No selected file','error')
        return redirect('https://127.0.0.1:6600/tms/annotate')

    notes = read_sql('.'.join(doc_name.split('.')[:-1]).replace('.','dot'),'NOTE','note')
    rel = read_sql('.'.join(doc_name.split('.')[:-1]).replace('.','dot'),'RELEVANCE','rel')
    lst = []
    for k,v in rel.items():

        try:
           n = notes[k]
        except:
            n = ''
        lst.append([k,v,n])
    df1 = pd.DataFrame(lst)
    #print(session['file'],flush=True)
    df1.columns = ['_id','Relevance','Notes']
    id_start = '.'.join(doc_name.split('.')[:-1]).replace('.','dot')
    df1['_id'] = df1['_id'].apply(lambda x:str(x.split(id_start)[1]))

    if doc_name.rsplit('.', 1)[1] == 'csv':
        df2 = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], doc_name))
    elif doc_name.rsplit('.', 1)[1] == 'xlsx':
        df2 = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], doc_name))


    try:
        df2['_id'] = df2['_id'].astype(str)
    except Exception as e:
        print(e)
        df2['_id']  = list(range(df2.shape[0]))
        df2['_id'] = df2['_id'].astype(str)
    df = df1.merge(df2,how='inner',on='_id')
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer,index=False)
    #the writer has done its job
    writer.close()
    #go back to the beginning of the stream
    output.seek(0)
    #finally return the file
    return send_file(output, attachment_filename='.'.join(doc_name.split('.')[:-1])+"_annotated.xlsx", as_attachment=True)


@app.route('/next', methods=['POST'])
def next():
    curStart,numResults,totResults,alltitles,allfts,allids,note,rel = read_session()
    curStart += numResults
    numResults = min(10,totResults-curStart)
    session['curStart'] = curStart
    session['numResults'] = numResults
    print(curStart,numResults)
    return jsonify(msg='success')

@app.route('/prev', methods=['POST'])
def prev():
    curStart,numResults,totResults,alltitles,allfts,allids,note,rel = read_session()
    curStart -= 10
    numResults = min(10,totResults-curStart)
    session['curStart'] = curStart
    session['numResults'] = numResults
    print(curStart,numResults)
    return jsonify(msg='success')


@app.route('/', methods=['GET','POST'])
def hello():
    if request.method == 'GET':
        return render_template('index.html', models=modelList())
    else:
        num = request.form['num']

        word1 = request.form['word1']
        word2 = request.form['word2']
        model = request.form['model']
        slop = request.form['slop']
        if model == 'google_news.w2v':

            wordRes1 = find_sim(word1, topn=int(num))
            wordRes2 = find_sim(word2, topn=int(num))
        else:

            wordRes1 = find_sim(word1, model_path=model_base+model, topn=int(num))
            wordRes2 = find_sim(word2, model_path=model_base+model, topn=int(num))
        #print(wordRes1,wordRes2)
        for idx, w in enumerate(wordRes1):
            x = list(w)
            x[0] = x[0].replace("_", " ")
            wordRes1[idx] = tuple(x)
        for idx, w in enumerate(wordRes2):
            x = list(w)
            x[0] = x[0].replace("_", " ")
            wordRes2[idx] = tuple(x)
        return render_template('index.html', slop=slop,wordRes1=wordRes1,wordRes2=wordRes2, word1=word1, word2=word2, models=modelList(), model=model)

@app.route('/tms/topicmodeling', methods=['GET','POST'])
def topicmodinghandler():
#num_topics = from_html_page
    collections = list(os.listdir(topic_modeler.temp_dir_))
    print(topic_modeler.temp_dir_)
    try:
        collections.remove('.DS_Store')
    except:
        pass
    curStart,numResults,totResults,alltitles,allfts,allids,note,rel = read_session()

    filtered_notes = []
    filtered_rel = []
    for id_ in allids[curStart:curStart+numResults]:
        try:
            filtered_notes.append(note[id_])
        except:
            filtered_notes.append('')
        try:
            filtered_rel.append(rel[id_])
        except:
            filtered_rel.append('')
    #print(filtered_rel,filtered_notes)
    return render_template('topic_mining.html',totResults=totResults,numResults=numResults,titles=alltitles[curStart:curStart+numResults],fts=allfts[curStart:curStart+numResults],ids=allids[curStart:curStart+numResults],curStart=curStart,collections=collections,note=filtered_notes,rel=filtered_rel)

@app.route('/tms/topics', methods=['GET','POST'])
def view_topics():
  print("handling /tms/topics")
  if request.method == 'POST':
    print('---topic count--->',request.form['count'])
    if len(request.form['count']) == 0 :
      topic_modeler.num_topics_ = 10
    else :
      topic_modeler.num_topics_ = request.form['count']

  topic_modeler.create_corpus()
  topic_modeler.apply_model()
  #topic_modeler.print_top_topics()
  topic_modeler.generate_visualization()
  with open(topic_modeler.visualize_html_, "r") as f:
    content_vis = f.read()
    return content_vis
    #return render_template('topic_vis.html', predict_content=content_vis )
    #return render_template('topic_vis.html', content=content_vis)
    #return render_template_string('<html> {{ what }}</html>', what=content)
 # return render_template(topic_modeler.visualize_html_)
 #return render_template('topic_vis.html')

@app.route('/tms/topics/download', methods=['GET'])
def download_topic_vis():
  return send_file(topic_modeler.visualize_html_, as_attachment=True, attachment_filename="topic_vis.html")
if __name__ == '__main__':
    #con = sqlite3.connect(db_name)
    #cur = con.cursor()

    # # # Create table
    #cur.execute('''CREATE TABLE 'NOTE' ( docid text, ts text, note text)''')
    #cur.execute('''CREATE TABLE 'RELEVANCE' ( docid text, ts text, rel text)''')
    #cur.execute("SELECT * from NOTE")
    #for row in cur.fetchall():
    #     print(row)
    #con.commit()
    #con.close()
    #http = WSGIServer(('', 6600), app.wsgi_app)
    #http.serve_forever()
    app.run(host='localhost', port=6600, threaded=True,debug=True)





