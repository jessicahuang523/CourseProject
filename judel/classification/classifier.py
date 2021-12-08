import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn import svm
from sklearn.model_selection import GridSearchCV , StratifiedKFold
from sklearn.dummy import DummyClassifier
from sklearn import metrics
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
import numpy as np 
from numpy import mean
import joblib 
from numpy import std

def preprocess(rel_df,nonrel_df):
	X = []
	y = []
	for idx,row in rel_df.iterrows():
		X.append(row['fulltext'])
		y.append(1)

	for idx,row in nonrel_df.iterrows():
		X.append(row['fulltext'])
		y.append(0)

	X = np.array(X)
	y = np.array(y)
	return X,y

def preprocess_p(df):
	X = []
	for idx,row in df.iterrows():
		X.append(row['fulltext'])
	return X 

def classify_cross_val(rel_df,nonrel_df,clf,tuned_parameters):
	X,y = preprocess(rel_df,nonrel_df)

	# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=30,stratify=y)
	kf = StratifiedKFold(n_splits=5,random_state=1,shuffle=True)
	

	i = 0
	fs = []
	ps  = []
	rs = []
	accs = []
	for train_index,test_index in kf.split(X,y):
		i+=1
		print('\n{} of kfold {}'.format(i,kf.n_splits))
		vectorizer = TfidfVectorizer(ngram_range=(1,2),max_df=0.95, min_df=1)
		my_pipeline = Pipeline([('vectorizer', vectorizer),('clf', clf)])
		xtr,xvl = X[train_index],X[test_index]

		ytr,yvl = y[train_index],y[test_index]
		print("Train",ytr.shape,np.count_nonzero(ytr))
		print("Test",yvl.shape,np.count_nonzero(yvl))
		model = GridSearchCV(my_pipeline, param_grid=tuned_parameters,cv=3, n_jobs=-1, scoring='f1',refit=True)
		# model = my_pipeline
		model.fit(xtr,ytr)
		pred=model.predict(xvl)
		f1 = metrics.f1_score(yvl,pred)
		fs.append(f1)
		p = metrics.precision_score(yvl,pred)
		ps.append(p)
		r = metrics.recall_score(yvl,pred)
		rs.append(r)
		acc = metrics.accuracy_score(yvl,pred)
		accs.append(acc)
		print("F1:",f1)
		print (model.best_params_)
		print("Acc:",acc)
		print("Recall:",r)
		print("Precision:",p)
	print("Acc",mean(np.array(accs)),std(np.array(accs)))
	print("F1",mean(np.array(fs)),std(np.array(fs)))
	print("P",mean(np.array(ps)),std(np.array(ps)))
	print("R",mean(np.array(rs)),std(np.array(rs)))

	# X_train_vec = vectorizer.fit_transform(X_train).toarray()
	# X_test_vec = vectorizer.transform(X_test).toarray()

	# if tuning:
	# 	best_clf = gcv.best_estimator_
	# 	print(gcv.best_params_)
	# else:
	# 	best_clf = clf 

	
	# y_train_p = best_clf.predict(X_train_vec)
	# # print(train_y_p)

	# train_rep = classification_report(y_train,y_train_p,target_names=['NonRel','Rel'],output_dict=True)
	# print('Train performance:')
	# print(train_rep)
	# y_test_p = best_clf.predict(X_test_vec)
	# test_rep = classification_report(y_test,y_test_p,target_names=['NonRel','Rel'],output_dict=True)
	# print('Test performance:')
	# print(test_rep)
	# 

	# 
def train(rel_df,nonrel_df,clf,model_file):
	X,y = preprocess(rel_df,nonrel_df)
	vectorizer = TfidfVectorizer(ngram_range=(1,2),max_df=0.95, min_df=1)
	my_pipeline = Pipeline([('vectorizer', vectorizer),('clf', clf)])
	model = my_pipeline
	model.fit(X,y)
	print(classification_report(y,model.predict(X),target_names=['NonRel','Rel'],output_dict=True))
	joblib.dump(model,model_file,compress=1)

def predict(df):
	X = df['fulltext'].to_list()
	model = joblib.load(model_file)
	y = model.predict_proba(X)
	return y 
	
def get_train_dfs(csv1,csv2,csv3,csv4):
	df = pd.read_csv(csv1)
	df1 = pd.read_csv(csv1)
	df2 = pd.read_excel(csv2)
	df3 = df1.join(df2)
	df4 = pd.read_csv(csv4)
	# df3.to_excel(csv3)
	rel_df = df3[df3['Label']=='Relevant'][['_id','fulltext']]
	nonrel_df = df3[df3['Label']=='Not Relevant'][['_id','fulltext']]
	# print(rel_df.merge(df4,how='inner'))
	rel_df = df4.append(rel_df)[['_id','fulltext']].drop_duplicates()
	return rel_df,nonrel_df

def main(csv1,csv2,csv3,csv4,model_file):
	rel_df,nonrel_df = get_train_dfs
	print(rel_df.shape)
	'''Uncomment/modify classifier and tuning parameters for 5-fold cross validation and/or training'''
	# clf = RandomForestClassifier(class_weight='balanced',random_state=10)
	# clf = LogisticRegression(max_iter=5000,class_weight='balanced',random_state=10)
	# clf = svm.SVC(class_weight='balanced')
	# tuned_parameters = [{'clf__n_estimators':[10,100],'clf__max_features':["auto","log2"],'clf__criterion':['entropy','gini']}]
	# tuned_parameters = [{'clf__C': [0.1,0.01, 1, 10, 100]}]
	# tuned_parameters = [{'clf__C': [0.1,0.01, 1, 10, 100, 1000],'clf__kernel':['linear', 'poly', 'rbf', 'sigmoid']}]
	clf = XGBClassifier(use_label_encoder=False,random_state=10,min_child_weight=0.1,max_depth=7,n_estimators=100)
	# tuned_parameters = [{'clf__min_child_weight': np.arange(0.1, 4.1, 1),'clf__max_depth':[3,5,7],'clf__n_estimators':[10,100]}] 
	

	# tuned_parameters = []
	# clf = DummyClassifier(strategy="constant",constant=1)
	# classify_cross_val(rel_df,nonrel_df,clf,tuned_parameters)		#For 5-fold cross validation
	train(rel_df,nonrel_df,clf,model_file)	# For final training and saving model

def readf(file_):
	with open(file_,'r') as f:
		data = f.readlines()
	lst = []
	for r in data:
		lst.append(r.strip('\n'))
	return lst 

def get_train_label(x,rel_df,nonrel_df):
	for idx,r in rel_df.iterrows():
		if r['_id'] == x:
			return 'Train Rel'

	for idx,r in nonrel_df.iterrows():
		if r['_id'] == x:
			return 'Train Non Rel'
	return 'Not in train'


def predict_main(title_file, txt_file, date_file,id_file,ofile,model_file,rel_df=None,nonrel_df=None):
	titles = readf(title_file)
	ft = readf(txt_file)
	dt = readf(date_file)
	ids = readf(id_file)
	df = pd.DataFrame([ft,dt,titles,ids]).transpose()
	df.columns=['fulltext','date','title','id']
	print(df.shape)
	df['pred_proba'] = predict(df)[:,1]
	if rel_df is not None:
		df['in_train'] = df['id'].apply(get_train_label,args=(rel_df,nonrel_df))

	df.to_excel(ofile)

	
if __name__ == '__main__':
	csv1 = '../data/judel_young.csv' #downloaded kibana search results (unannotated data)
	csv2 = '../data/judel_results.xlsx' #annotated data fetched from the database using get_ann_res.py
	csv3 = '../data/judel_results_merged.xlsx' #output file
	'''for juvenile delinquecy, the articles containing the following terms are known JUDEL articles: 
	young offender" OR "youthful offender" OR  "juvenile incorrigible" OR "young incorrigible" OR "juvenile criminal" OR "young criminal"  OR  "juvenile adult" OR "cosh boy"  OR "teddy boy" OR "juvenile delinquent" OR "juvenile offender”
	These are not manually annotated and directly used as relevant articles for training after downloading from kibana search (csv4)
	'''
	csv4 = '../data/orig_res.csv'  
	model_file = '../data/xgboost.mdl' #trained model saved here
	'''
	The following files are all proquest articles until 1830 downloaded using  /indexing/es_fetch_juv.py. We want to run the trained model on all the articles and predict relevant JUDEL articles
	'''
	title_file = '../data/all_1830_title.txt'
	txt_file = '../data/all_1830.txt'
	date_file = '../data/all_1830_date.txt'
	id_file = '../data/all_1830_ids.txt'
	ofile = '../data/all_1830_op.xlsx'
	# main(csv1,csv2,csv3,csv4) #Uncomment for training
	rel_df,nonrel_df = get_train_dfs(csv1,csv2,csv3,csv4)
	predict_main(title_file,txt_file,date_file,id_file,ofile,model_file,rel_df,nonrel_df
		)