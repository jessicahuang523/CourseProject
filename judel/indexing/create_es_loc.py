from elasticsearch import Elasticsearch
from elasticsearch import helpers
import io
import os
import datetime 
import zipfile
import bs4 as bs
import re
import sys
import json

def gendata(idx_tup):

    for i,(ids,dt,fulltext,url,publisher) in enumerate(idx_tup):
        yield {
            "_index": "ploc",
            "_id": ids,
            "_source": {"date": dt,"fulltext":fulltext,"url":url,"publisher":publisher},
        }


def main():
    es = Elasticsearch(['192.17.58.175'],timeout=120)
    es.indices.delete(index='ploc', ignore=[400, 404])
    base_dir = '/srv/data/judel/loc_chronicling_america/'
    dt = []
    fulltext = []
    url = []
    publisher = []
    ids = []
    rec_id = set()
    batch_size = 10000
    total_cnt = 0

    es.indices.create(
    index="ploc",

    body={
    "mappings": {

    "properties": {  

   
    "fulltext": {"type": "text","analyzer": "english","fielddata":True},
    "url":{"type":"keyword"},
    "date": {"type": "date"},
    "publisher": {"type": "text","analyzer": "english","fielddata":True}

    }
    }
    }
    )

    for (idx1,file1) in enumerate(os.listdir(base_dir)):
        path1 = os.path.join(base_dir, file1)
        for (idx2,file2) in enumerate(os.listdir(path1)):
            path2 = os.path.join(path1, file2)
            for (idx3,file3) in enumerate(os.listdir(path2)):
                path3 = os.path.join(path2, file3)
                for (idx4,file4) in enumerate(os.listdir(path3)):
                    cnt_dir = os.path.join(path3,file4)
                    meta_path = os.path.join(cnt_dir,'metadata.json')
                    try:
                        with open(meta_path,'r') as f:
                           dict_ = json.load(f)
                    except:
                        continue
                    date = datetime.datetime.strptime(dict_["issue"]["date_issued"],'%Y-%m-%d').isoformat().split('T')[0]
                    
                    txt_path = os.path.join(cnt_dir,'ocr.txt')
                    try:
                        with open(txt_path,'r') as f:
                           ft = ' '.join(f.readlines())
                    except:
                        continue
                    
                    
                    ft = ' '.join(ft.split())
                    dt.append(date)
                    ids.append(total_cnt)
                    publisher.append(dict_["title"]["name"])
                    url.append(dict_["pdf"])
                    fulltext.append(ft)
                    total_cnt += 1

                    if len(dt)>=batch_size:
                        print (idx1,idx2,idx3,idx4,total_cnt)
                        sys.stdout.flush()
                        for success, info in helpers.parallel_bulk(es, gendata((zip(ids,dt,fulltext,url,publisher)))):
                            if not success:
                                print(success,info)
                        dt = []
                        fulltext = []
                        url = []
                        publisher = []
                        ids = []
    for success, info in helpers.parallel_bulk(es, gendata((zip(ids,dt,fulltext,url,publisher)))):
        if not success:
            print(success,info)
    


if __name__ == '__main__':
	main()
