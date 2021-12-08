import logging
import gensim
from gensim.models import  ldamulticore
from pprint import pprint
import os
from gensim.corpora import MmCorpus
from nltk.corpus import stopwords
import re
from gensim.models import LdaModel
import pyLDAvis
import pyLDAvis.gensim_models as gensimvis
import tempfile
import os


def preprocess(article_text):
  other_st = ['lt','gt','tbe']
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
    def __init__(self, fname=None):
      self.tokens=[]
      self.fname = fname
      if(fname is not None):
        with open(self.fname) as f2:
          data = f2.readlines()
          txt = []
          for doc in data:
            row = doc.strip('\n')
            self.tokens.append(preprocess(row))

    def add_file(self, fname):
      with open(fname) as f2:
        data = f2.readlines()
        txt = []
        for doc in data:
          row = doc.strip('\n')
          self.tokens.append(preprocess(row))

    def __iter__(self):
      for x in self.tokens:
        yield x

class MyCorpus(object):
    def __init__(self,dict_,tokens):
      self.dictionary_ = dict_
      self.tokens_ = tokens

    def __iter__(self):
      for x in self.tokens_:
        yield self.dictionary_.doc2bow(x)
      #yield self.dictionary_.doc2bow(self.tokens_)

class TopicModeler(object):
    def __init__(self,num_topics):
      #TODO remove hardcoding and use temp directory and temp files
      self.temp_dir_ = tempfile.mkdtemp() + '/'
      #print(type(self.temp_dir_))
      self.model_file_ = self.temp_dir_ + 'model.lda'
      self.mysentenses_ = MySentences()
      self.mycorpus_ = None
      '''
	fulltext and title of the articles from which we want to extract the topics, can be downloaded using /indexing/es_fetch_juv.py
      '''
      self.corpus_file_ = self.temp_dir_ + 'corpus.txt'
      self.corpus_mm_file_ = self.temp_dir_ + 'corpus.mm'
      self.visualize_html_ = self.temp_dir_ + 'topic_vis.html'
      self.files_ = []
      self.num_topics_ = num_topics
      self.tokens_ = []
      self.id2word_=gensim.corpora.Dictionary()
      self.model_=None

    def add_file(self,file_path):
      self.files_.append(file_path)
      self.mysentenses_.add_file(file_path)

    def create_corpus(self):
      self.id2word_ = gensim.corpora.Dictionary(self.mysentenses_)
      self.id2word_.filter_extremes(no_below=3, no_above=0.99)
      self.id2word_.compactify()
      self.mycorpus_ = MyCorpus(self.id2word_,self.mysentenses_.tokens)
      MmCorpus.serialize(self.corpus_file_, self.mycorpus_)

    #def create_corpus(self):
    #  self.mycorpus_ = MyCorpus(self.id2word_)

    #Token − A token means a ‘word’.
    #Document − A document refers to a sentence or paragraph.
    def apply_model(self):
      self.model_ = ldamulticore.LdaMulticore(self.mycorpus_,num_topics=self.num_topics_,workers=8,passes=40,iterations=3000,eval_every=5,random_state=42,id2word=self.id2word_)
      self.model_.save(self.model_file_)

    def print_top_topics(self):
      top_topics = self.model_.top_topics(self.mycorpus_,dictionary=self.id2word_) #, num_words=20)
	# Average topic coherence is the sum of topic coherences of all topics, divided by the number of topics.
      avg_topic_coherence = sum([t[1] for t in top_topics]) / self.num_topics_
      print('Average topic coherence: %.4f.' % avg_topic_coherence)
      pprint(top_topics)

    def generate_visualization(self,path=None):
      doc_term_matrix = [self.id2word_.doc2bow(doc) for doc in self.mysentenses_]
      MmCorpus.serialize(self.corpus_mm_file_, doc_term_matrix)
      c_t = gensim.corpora.MmCorpus(self.corpus_mm_file_)
      lda_t = gensim.models.LdaModel.load(self.model_file_)
      #https://stackoverflow.com/questions/46379763/typeerror-object-of-type-complex-is-not-json-serializable-while-using-pyldavi
      data = gensimvis.prepare(lda_t, c_t, self.id2word_,mds='tsne')
      if path is None:
        pyLDAvis.save_html(data,self.visualize_html_)
      else :
        pyLDAvis.save_html(data,path)


#    def upload(self):

#def main():
#	logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
#	num_topics = 20
#	topic_generator = TopicModeler(num_topics)
#	'''
#	fulltext and title of the articles from which we want to extract the topics, can be downloaded using /indexing/es_fetch_juv.py
#	'''
#	txt_file = '../data/nyt_sub.txt'
#	txt_file_1 = '../data/proquest_juv.txt'
#
#	topic_generator.add_file(txt_file)
#	topic_generator.add_file(txt_file_1)
#
#	topic_generator.create_corpus()
#	topic_generator.apply_model()
#	topic_generator.print_top_topics()
#	topic_generator.generate_visualization()
#	print(topic_generator.temp_dir_)
#
#if __name__ == '__main__':
#	main()
#
