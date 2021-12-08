import os
import sys
sys.path.append(f'{os.getcwd()}/..')
import common
import argparse
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

def main(start, end):
    for decade in range(start, end+1, 10):
        es = Elasticsearch(['192.17.58.175'], timeout=120)
        # query = {'query':{'match_phrase':{"fulltext":"juvenile delinquency"}}}
        query = {'query': {
            "bool": {
                "should": []
                ,
                "filter":
                    {"range": {"date": {"gte": f"{decade}-01-01T00:00:00",

                                        "lte": f"{decade+10}-01-01T00:00:00"

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
                print(f'{decade}s: {count}')

                with open(f'{common.new_data_dir}/{decade}.txt', 'a') as f:
                    for idx, doc in enumerate(txt):
                        f.write(title[idx] + ' ' + doc)
                        f.write('\n')

                with open(f'{common.new_data_dir}/{decade}_title.txt', 'a') as f:
                    for doc in title:
                        f.write(doc)
                        f.write('\n')

                with open(f'{common.new_data_dir}/{decade}_date.txt', 'a') as f:
                    for doc in date:
                        f.write(doc)
                        f.write('\n')

                with open(f'{common.new_data_dir}/{decade}_ids.txt', 'a') as f:
                    for doc in ids:
                        f.write(doc)
                        f.write('\n')
                txt = []
                title = []
                date = []
                ids = []

        if txt:
            with open(f'{common.new_data_dir}/{decade}.txt', 'a') as f:
                for idx, doc in enumerate(txt):
                    f.write(title[idx] + ' ' + doc)
                    f.write('\n')

            with open(f'{common.new_data_dir}/{decade}_title.txt', 'a') as f:
                for doc in title:
                    f.write(doc)
                    f.write('\n')

            with open(f'{common.new_data_dir}/{decade}_date.txt', 'a') as f:
                for doc in date:
                    f.write(doc)
                    f.write('\n')

            with open(f'{common.new_data_dir}/{decade}_ids.txt', 'a') as f:
                for doc in ids:
                    f.write(doc)
                    f.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', default=1790)
    parser.add_argument('--end', default=2000)
    args = parser.parse_args()
    main(start=args.start, end=args.end)
