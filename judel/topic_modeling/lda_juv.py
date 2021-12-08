import logging
import gensim 
from gensim.models import  ldamulticore
from pprint import pprint
import os 
from gensim.corpora import MmCorpus
from nltk.corpus import stopwords
import re
from gensim.models import LdaModel
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

other_st = ['lt','gt','tbe']
def preprocess(article_text):
    stop_ = set(stopwords.words('english'))
    for w in other_st:
    	stop_.add(w)

    processed_article = article_text.lower()
    token_pattern = r"(?u)\b\w\w+\b"
    token_pattern = re.compile(token_pattern)
    processed_article = token_pattern.findall(processed_article)
    processed_article = [w for w in processed_article if w not in stop_]
    return processed_article


class MySentences(object):
	def __init__(self, fname):
		self.fname = fname

	def __iter__(self):
		with open(self.fname) as f2:
			data = f2.readlines()
			txt = []
			for doc in data:
				row = doc.strip('\n')
				tokens= preprocess(row)
				yield tokens

class MyCorpus(object):
	def __init__(self, fname,dict_):
		self.fname = fname
		self.dictionary = dict_

	def __iter__(self):
		with open(self.fname) as f2:
			data = f2.readlines()
			txt = []
			for doc in data:
				row = doc.strip('\n')
				tokens = preprocess(row)
				yield self.dictionary.doc2bow(tokens)


def main():
	model_file = '../data/judel_80.lda'
	'''
	fulltext and title of the articles from which we want to extract the topics, can be downloaded using /indexing/es_fetch_juv.py
	'''
	txt_file = '../data/proquest_juv.txt'   
	corpus_file = '../data/proquest_juv_title.txt'

	num_topics = 80
	# lda_model = LdaModel.load(model_file)
	# id2word = lda_model.id2word
	print("Creating dictionary")
	sentences = MySentences(txt_file)
	id2word = gensim.corpora.Dictionary(sentences)
	id2word.filter_extremes(no_below=3, no_above=0.99)
	#
	print("Dictionary Done")
	corpus = MyCorpus(txt_file,id2word)
	MmCorpus.serialize(corpus_file, corpus)
	print("Training")
	model = ldamulticore.LdaMulticore(corpus,num_topics=num_topics,workers=8,passes=40,iterations=3000,eval_every=5,random_state=42,id2word=id2word)
	model.save(model_file)
	print("Training Done")
	top_topics = model.top_topics(corpus,dictionary=id2word) #, num_words=20)

	# Average topic coherence is the sum of topic coherences of all topics, divided by the number of topics.
	avg_topic_coherence = sum([t[1] for t in top_topics]) / num_topics
	print('Average topic coherence: %.4f.' % avg_topic_coherence)
	pprint(top_topics)
if __name__ == '__main__':
	main()

