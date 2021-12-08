import os
import sys

sys.path.append(f'{os.getcwd()}/..')
import common
from elasticsearch import Elasticsearch, helpers

# terms = ["young offender" , "youthful offender" , "juvenile incorrigible" , "young incorrigible" ,
# "juvenile criminal" , "young criminal"  ,  "juvenile adult" , "cosh boy" ,"teddy boy" , "juvenile delinquent"]
# #JUDEL terms terms= ["juvenile" , "child" , "teenage" , "little folks" , "lassies" , "lads" , "kid" , "young" ,
# "underage" , "pubescent" , "prepubescent" , "adolescent" , "schoolgirl" , "schoolboy" , "youth" , "tender age"]
# #juvenile terms
terms = ["juvenile"]


# terms= ["crime","offence","prison","police","punishment","illegal","misdemeanor","felony","murder","atrocity",
# "wickedness","perpetration","turpitude","depravity","profligacy","delinquency","theft","treason","grand larceny"]
# #crime terms

def main():
    es = Elasticsearch(['192.17.58.175'], timeout=120)
    # query = {'query':{'match_phrase':{"fulltext":"juvenile delinquency"}}}
    query = {'query': {
        "bool": {
            "should": []
            ,
            "filter":
                {"range": {"date": {"gte": "1830-01-01T00:00:00",

                                    "lte": "1910-01-01T00:00:00"

                                    }}},
            # "minimum_should_match" : 1,
        }}}

    # for t in terms:
    # 	query['query']['bool']['should'].append({'match_phrase':{'fulltext':t}})

    # print(query)
    count = 0
    txt = []
    title = []
    date = []
    ids = []
    for doc in helpers.scan(client=es, query=query, index='proquest', size=10000):
        count += 1
        txt.append(doc['_source']['fulltext'])
        title.append(doc['_source']['title'])
        date.append(doc['_source']['date'])
        ids.append(doc['_id'])
        if count % 10000 == 0:
            print(count)

            with open(f'{common.new_data_dir}/1900.txt', 'a') as f:
                for idx, doc in enumerate(txt):
                    f.write(title[idx] + ' ' + doc)
                    f.write('\n')

            with open(f'{common.new_data_dir}/1900_title.txt', 'a') as f:
                for doc in title:
                    f.write(doc)
                    f.write('\n')

            with open(f'{common.new_data_dir}/1900_date.txt', 'a') as f:
                for doc in date:
                    f.write(doc)
                    f.write('\n')

            with open(f'{common.new_data_dir}/1900_ids.txt', 'a') as f:
                for doc in ids:
                    f.write(doc)
                    f.write('\n')
            txt = []
            title = []
            date = []
            ids = []

    if txt:
        with open(f'{common.new_data_dir}/1900.txt', 'a') as f:
            for idx, doc in enumerate(txt):
                f.write(title[idx] + ' ' + doc)
                f.write('\n')

        with open(f'{common.new_data_dir}/1900_title.txt', 'a') as f:
            for doc in title:
                f.write(doc)
                f.write('\n')

        with open(f'{common.new_data_dir}/1900_date.txt', 'a') as f:
            for doc in date:
                f.write(doc)
                f.write('\n')

        with open(f'{common.new_data_dir}/1900_ids.txt', 'a') as f:
            for doc in ids:
                f.write(doc)
                f.write('\n')


if __name__ == '__main__':
    main()
