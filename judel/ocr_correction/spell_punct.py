#from deepsegment import DeepSegment
from neuspell import BertChecker
import neuspell
import pandas as pd
from punctuator import Punctuator
import re
import nltk
from nltk.corpus import stopwords

stopwords_ = set(stopwords.words('english'))
stopwords_.add('also')


def read_file(filename):

    df = pd.read_excel(filename)

    fts = []


    try:
        fts = df['fulltext'].to_list()
        
        # print(fts,titles)
    except Exception as e:
        return 1,str(e),0,fts,df
    return 0,"",len(fts),fts,df 

def main(filename,of):
	#segmenter = DeepSegment('en')
	'''
	Downloaded from https://drive.google.com/drive/folders/0B7BsN5f2F1fZQnFsbzJ3TWxxMms?resourcekey=0-6yhuY9FOeITBBWWNdyG2aw
	'''
	p = Punctuator('/home/bhavya2/.punctuator/Demo-Europarl-EN.pcl') 
	checker = BertChecker()
	checker.from_pretrained()
	_,_,_,fts,df = read_file(filename)

	cor_ft = []
	for idx,ft in enumerate(fts):
	

		ft = ft.replace("';","'").replace('";'," ").replace('*&;amp;',' ').replace('lt;*',' ').replace('gt;*',' ').replace('gt;?',' ').replace('lt;?',' ').replace('gt;!',' ').replace('lt;!',' ').replace('&;amp;','&').replace('lt;',' ').replace('gt;',' ').replace('lt',' ').replace('gt',' ') #removing some noise, HTML characters
		seg_ft = re.split(r"[.?]",p.punctuate(ft)) #sentences are tokenized on period and question mark 
		sents = []
	
		for seg in seg_ft:
			
			if seg.strip()!='':

				sw = [w for w in re.split(r"( |-|,|;|\\|!|&|:|\"|\^|\*|'|\)|\()",' '.join(seg.split())) if w.strip()!=''] #tokenizing words on space and punctuation
				
				st = 0
				cw = []
				while st<len(sw):
					sw_seg = sw[st:st+80]			#neuspell truncates long text, so we segment it into several short text chunks as use those as inputs for neuspell
					st += 80
					cw_seg = checker.correct(' '.join(sw_seg))
					cw_seg_fil = []
					
					for idx,w in enumerate(cw_seg.split()):
						
						if sw_seg[idx].lower()=='tiie':		#hardcoding known error correction
							cw_seg_fil.append('the')
						'''
						We perform only light error correction to be safe. If neuspell predicts a stopword or a word with minor spelling change (1 character substitution), we keep the predicted word, else keep the original word.
						'''
						elif w.lower()!=sw_seg[idx].lower():
							if w.lower() in stopwords_:		
								cw_seg_fil.append(w)
								
							else:
								accept = False
								if len(w)==len(sw_seg[idx]):
									cnt = 0
									for idx2,c1 in enumerate(w):
										
											if c1!=sw_seg[idx][idx2]:
												cnt+=1
									if cnt<2:
										accept=True
										print(3,w,sw_seg[idx],sw_seg[max(idx-3,0):idx+3],flush=True)
										cw_seg_fil.append(w)



								if not accept:	
									
									cw_seg_fil.append(sw_seg[idx])
						else:
							
							cw_seg_fil.append(w)
					cw.append(' '.join(cw_seg_fil))

				sents.append(' '.join(cw))
		cor_ft.append('\n'.join(sents))
				
		
		if idx%10==0:
			print(idx,cor_ft[-1],flush=True)


if __name__ == '__main__':
	filename = '../data/predicted_judel.xlsx'  #input articles to be corrected
	of = '../data/predicted_judel_punct.csv'
	main(filename,of)
