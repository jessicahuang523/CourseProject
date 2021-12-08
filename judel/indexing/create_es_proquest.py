from elasticsearch import Elasticsearch
from elasticsearch import helpers
import io
import os
import datetime 
import zipfile
import bs4 as bs
import re
import sys

def gendata(idx_tup):

    for i,(ids,dt,abstract,fulltext,title,subtitle,url,publisher) in enumerate(idx_tup):
        yield {
            "_index": "proquest",
            "_id": ids,
            "_source": {"date": dt,"abstract":abstract,"fulltext":fulltext,"title":title,"url":url,"publisher":publisher,"subtitle":subtitle},
        }


def main():
    es = Elasticsearch(['192.17.58.175'])
    # es.indices.delete(index='proquest', ignore=[400, 404])
    base_dir = '/srv/data/judel/proquest_historical_newspapers'
    dt = []
    abstract = []
    fulltext = []
    title = []
    url = []
    publisher = []
    subtitle = []
    ids = []
    rec_id = set()
    batch_size = 10000
    total_cnt = 58230724

    es.indices.create(
    index="proquest",

    body={
    "mappings": {

    "properties": {  

    "abstract": {"type":"text","analyzer": "english","fielddata":True},
    "fulltext": {"type": "text","analyzer": "english","fielddata":True},
    "articles": {"type": "date"},
    "title": {"type":"text","analyzer":"english","fielddata":True},
    "subtitle": {"type":"text","analyzer":"english","fielddata":True},
    "url": {"type":"keyword"},
    "publisher": {"type": "text","analyzer": "english","fielddata":True}

    }
    }
    }
    )

    for (idx1,file1) in enumerate(os.listdir(base_dir)):
            new_path = os.path.join(base_dir,file1.strip('.zip'))
            try:
                zip_ = zipfile.ZipFile(os.path.join(base_dir,file1))
                
                os.mkdir(new_path)
                zip_.extractall(new_path)
               
            except Exception as e:
                print("Error extracting {} {}".format(file1,e))
                continue 
         

            for (idx2,file2) in enumerate(os.listdir(new_path)):
                cnt_dir = os.path.join(new_path,file2,'content')
                for (idx3,file3) in enumerate(os.listdir(cnt_dir)):
                    path = os.path.join(cnt_dir,file3)
                    soup = bs.BeautifulSoup(open(path,'r'),'xml')
                    # print(soup,path)
                    rid = soup.find("RecordID").getText()
                    if rid not in rec_id:
                        try:
                            ft = re.sub(r'&lt;.*?&gt;', '',soup.find("FullText").getText()) #no text
                        except:
                            continue
                        rec_id.add(rid)
                        

                        date = datetime.datetime.strptime(soup.find("AlphaPubDate").getText().split(';')[0],'%b %d, %Y').isoformat().split('T')[0]

                        dt.append(date)
                        ids.append(total_cnt)
                        total_cnt += 1

                        ft = re.sub(r'&quot', '\"',ft)
                        ft = re.sub(r'&apos', '\'',ft)
                        ft = re.sub(r'&amp', '&',ft)
                        ft = re.sub(r'\.+', ".", ft)
                        ft = re.sub(r'\t+', "\t", ft)
                        ft = re.sub(r'\t', " ", ft)
                        ft = ' '.join(ft.split())
                        # print(rec['RecordID'])
                        try:
                            abstract.append(soup.find("Abstract").getText())
                        except:
                            abstract.append("")
                        fulltext.append(ft)
                        title.append(soup.find("RecordTitle").getText())
                        try:
                            url.append(soup.find("URLDocView").getText())
                        except:
                            url.append("")
                        try:
                            subtitle.append(soup.find("RecordSubtitle").getText())
                        except:
                            subtitle.append("")
                        try:
                            publisher.append(soup.find("Publisher").getText())
                        except:
                            publisher.append(soup.find("PubTitle").getText())

                    if len(dt)>=batch_size:
                        print (idx2,idx3,file2,file3,total_cnt)
                        sys.stdout.flush()
                        for success, info in helpers.parallel_bulk(es, gendata((zip(ids,dt,abstract,fulltext,title,subtitle,url,publisher)))):
                            if not success:
                                print(success,info)
                        dt = []
                        abstract = []
                        fulltext = []
                        title = []
                        url = []
                        publisher = []
                        subtitle = []
                        ids = []
    for success, info in helpers.parallel_bulk(es, gendata((zip(ids,dt,abstract,fulltext,title,subtitle,url,publisher)))):
        if not success:
            print(success,info)
    


if __name__ == '__main__':
	main()
