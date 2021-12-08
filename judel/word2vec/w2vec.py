import os
import sys
sys.path.append(f'{os.getcwd()}/..')
import common
import io
import argparse
import json
import datetime
import re
import logging
from nltk.corpus import stopwords
from gensim.models import Word2Vec
from gensim.models import KeyedVectors
from gensim.models.phrases import Phrases, ENGLISH_CONNECTOR_WORDS


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

terms = [" young offenders", " young offender", " youthful offenders", " youthful offender", " juvenile incorrigibles",
         " juvenile incorrigible", " young incorrigibles", " young incorrigible", " juvenile criminals",
         " juvenile criminal", " young criminals", " young criminal", " juvenile adults", " juvenile adult",
         " cosh boys", " cosh boy", " teddy boys", " teddy boy", " juvenile delinquents", " juvenile delinquent",
         " juvenile delinquency", " juvenile offenders", " juvenile offender"]
cstop = ['gt', 'lt', 'tbe']


class MySentences(object):
    def __init__(self, fname):
        self.fname = fname

    def __iter__(self):
        with open(self.fname) as f2:
            data = f2.readlines()
            txt = []
            for doc in data:
                yield doc.strip('\n').split()


def preprocess(article_text):
    stop_ = set(stopwords.words('english'))
    for w in cstop:
        stop_.add(w)
    processed_article = article_text.lower()

    token_pattern = r"(?u)\b\w\w+\b"
    token_pattern = re.compile(token_pattern)
    processed_article = ' '.join(token_pattern.findall(processed_article))

    '''
    For better training of judel related words, normalize them or consider all of them as a single term "JUDEL"
    '''
    for t in terms:
        processed_article = processed_article.replace(t, ' JUDEL')
        # Adam! she's just replacing all t in terms w "JUDEL" (todo: delete this comment)

    processed_article = ' '.join([w for w in processed_article.split() if w not in stop_])

    return processed_article


def w2v(sentences, model_path, window=5):
    print('Training...')
    word2vec = Word2Vec(sentences, window=window, min_count=3, epochs=20, workers=4, vector_size=300)
    word2vec = word2vec.wv
    print("training done")
    # try:
    #     print(word2vec.most_similar('juvenile_delinquence'))
    # except Exception as e:
    #     print(e)
    # try:
    #     print(word2vec.most_similar('juvenile'))
    # except Exception as e:
    #     print(e)
    word2vec.save(model_path)


def load_model(model_path):
    return KeyedVectors.load(model_path, mmap='r')


def find_sim(model_path, word):
    word2vec = load_model(model_path)
    sim_words = word2vec.most_similar(word, topn=100)
    print(sim_words)


def main(file=None, window=5):
    if file:
        if os.path.exists(f'{common.new_data_dir}/{file}'):
            files = [file]
        else:
            print(f'Error: {common.new_data_dir}/{file} does not exist')
            print(f'Note: must give the name of the file in {common.new_data_dir}, not '
                  f'the full path to the file.')
            sys.exit(1)
    else:
        files = sorted(os.listdir(common.new_data_dir))

    for f1 in files:
        print(f1)
        docs = []
        with open(f'{common.new_data_dir}/{f1}') as f2:
            for doc in f2.readlines():
                ndoc = preprocess(doc.strip('\n'))
                docs.append(ndoc)

        with open(f'{common.new_data_dir}/{f1}', 'w') as f2:
            for doc in docs:
                f2.write(doc)
                f2.write('\n')

        sentences = MySentences(f'{common.new_data_dir}/{f1}')

        # Adam! this is what does the bigram thing (todo: delete this comment)
        bigram_mdl = Phrases(sentences, connector_words=ENGLISH_CONNECTOR_WORDS, max_vocab_size=20000000, min_count=3)
        vocab_ = set(list(bigram_mdl.vocab))

        bigrams = bigram_mdl[sentences]

        count = 0
        with open(f'{common.new_data_dir}/{f1[:-4]}_bg.txt', 'w') as f3:
            for doc in bigrams:
                try:
                    fdoc = []
                    for w in doc:
                        if w in vocab_:
                            fdoc.append(w)
                    count += 1
                    f3.write(' '.join(fdoc))
                    f3.write('\n')
                except Exception as e:
                    print(e, count)
        del bigrams
        del bigram_mdl
        del sentences

        sentences = MySentences(f'{common.new_data_dir}/{f1[:-4]}_bg.txt')
        print("reading done")
        w2v(sentences, f'{common.new_model_dir}/{f1[:-3]}w2v', window=window)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', default=None)
    parser.add_argument('--window', default=5)
    args = parser.parse_args()
    main(file=args.file, window=args.window)
