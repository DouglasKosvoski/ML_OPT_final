# -*- coding: utf-8 -*-
"""TF_ml.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lh9XCswYq1jC1C5ykyKOAp5ByIw2b4xi

Douglas Kosvoski
    1911100022

## Loading Libraries
"""

!pip install tomotopy spacy > /dev/null

# Commented out IPython magic to ensure Python compatibility.
import sys
import spacy
import gensim

import pandas as pd
import tomotopy as tp
import numpy as np
import pandas as pd
import re

import matplotlib.pyplot as plt
# %matplotlib inline

from gensim.models.phrases import Phrases, Phraser
from bs4 import BeautifulSoup

spacy.cli.download("en_core_web_md")
nlp = spacy.load('en_core_web_md')

import warnings
warnings.filterwarnings('ignore')

"""## Loading dataset"""

""" The dataset is avaiable through google sheets api """
# https://docs.google.com/spreadsheets/d/1xdU55aEjDM-gdVWOm1UcSPmE0KcMFG5XHzs-9nyBTEA

sheet_id = "1xdU55aEjDM-gdVWOm1UcSPmE0KcMFG5XHzs-9nyBTEA"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="

df = pd.concat([
  pd.read_csv(url + 'train').drop(['Id', 'CreationDate', 'Y'], axis=1),
  pd.read_csv(url + 'valid').drop(['Id', 'CreationDate', 'Y'], axis=1)
])

df.info()

def get_average_feature_length(docs, feature):
  total_size = 0
  max_size = 0
  min_size = 999

  for i in docs:
    length = len(i)
    total_size += length
  
    if length > max_size:
      max_size = length

    if length < min_size:
      min_size = length
    
  print(f"\n{'-'*10} {feature} {'-'*10}")
  print(f"Average # of {feature}: {int(total_size / len(docs))}")
  print(f"Max # of {feature}: {max_size}")
  print(f"Min # of {feature}: {min_size}")
  return int(total_size / len(docs))

avg_title_size = get_average_feature_length(df['Title'], 'Title')
avg_body_size  = get_average_feature_length(df['Body'], 'Body')
avg_tag_size   = get_average_feature_length(df['Tags'], 'Tags')

number_of_docs = 100
feature = df.Body

docs = list(feature)[:number_of_docs]
print(len(docs))

"""## Remove HTML tags"""

def remove_special_characters(character):
  if character.isalnum() or character in [' ', '.', '\n']:
    return True
  return False

def remove_tags(docs):
  cleaned_docs = []
  tags = r"<pre>|</pre>|<a|</a>|<img>|</img>|href|http"

  count = 0
  for doc in docs:
    print(f"{count} out of {len(docs)}", end="\r")
    split_string = re.split(tags, doc.strip().replace('\n', ''))
    clean_doc = ''

    for i in split_string:
      i = i.strip()
      if not (i.startswith('<code>') or i.startswith('=')):
        text = BeautifulSoup(i.strip(), "lxml").text
        asd = "".join(filter(remove_special_characters, text))
        clean_doc += asd

    cleaned_docs.append(clean_doc.strip())
    count += 1
  return cleaned_docs

docs_without_tags = remove_tags(docs)

for i, t in enumerate(zip(docs_without_tags[:10])):
  print(i, t)

"""## Lematization"""

def lematize(docs):
  dlemma, total_size = [], len(docs)

  for i, d in enumerate(docs):
    print(f"{i} out of {total_size}", end='')
    lm = " ".join([token.lemma_ for token in nlp(d) if not (token.is_stop == True or token.is_digit == True or token.is_punct == True)])
    dlemma.append(lm.lower())
    print('\r\r\r\r\r\r\r\r', end='')
  return dlemma

dlemma = lematize(docs_without_tags)

for i in dlemma[:10]:
  print(i)

"""## Tokenization"""

min_length = 4
dtoken = [gensim.utils.simple_preprocess(d, deacc=True, min_len=min_length) for d in dlemma]

for i in dtoken[:10]:
  print(i)

"""## N-grams"""

bigram  = Phraser(Phrases(dtoken, min_count=2, threshold=10))
bdocs   = [bigram[d] for d in dtoken]

def get_bigrams(docs):
  bigrams = []
  for doc in bdocs:
    for j in doc:
      if '_' in j and j not in bigrams:
        bigrams.append(j)

  return bigrams

print(get_bigrams(bdocs)[:10])

"""## Statistical"""

from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.models import LdaModel

dictionary = Dictionary(bdocs)
print(dictionary)

dictionary.filter_extremes(keep_n=10000, no_above=0.9, no_below=len(bdocs)*0.01) # no_below 1%
print(dictionary)

corpus_bof   = [dictionary.doc2bow(d) for d in bdocs]
tfidf        = TfidfModel(corpus_bof)
corpus_tfidf = tfidf[corpus_bof]

K = [10, 20, 30, 40]
passes = [50, 100, 200]

alpha, eta = ['symmetric', 'asymmetric', 'auto'], ['symmetric', 'auto']
vocab = list(dictionary.values())

print(f'# of docs: {dictionary.num_docs} \n# of words: {len(vocab)}')
cv = []

"""### Bag of words"""

def bow():
  for k in K:
    for a in alpha:
      for b in eta:
        for p in passes:
          lda = LdaModel(
            corpus          = corpus_bof,
            num_topics      = k,
            random_state    = 777,
            id2word         = dictionary,
            alpha           = a,
            eta             = b,
            per_word_topics = True,
            passes          = p
          )

          lda_cv  = CoherenceModel(
            model      = lda,
            texts      = bdocs,
            dictionary = dictionary,
            coherence  = 'c_v'
          )

          cv_cohe = lda_cv.get_coherence()

          print('K: %2d alfa: %10s beta: %10s passes: %3d coherence: %.3f'%(k, a, b, p, cv_cohe))
          cv.append(cv_cohe)

bow()

"""### TF-IDF"""

def tfidf():
  for k in K:
    for a in alpha:
      for b in eta:
        for p in passes:
          lda = LdaModel(
            corpus          = corpus_tfidf,
            num_topics      = k,
            random_state    = 777,
            id2word         = dictionary,
            alpha           = a,
            eta             = b,
            per_word_topics = True,
            passes          = p
          )

          lda_cv  = CoherenceModel(
            model      = lda,
            texts      = bdocs,
            dictionary = dictionary,
            coherence  = 'c_v'
          )

          cv_cohe = lda_cv.get_coherence()

          print('K: %2d alfa: %10s beta: %10s passes: %3d coherence: %.3f'%(k, a, b, p, cv_cohe))
          cv.append(cv_cohe)

tfidf()

print('# of docs: %5d # of words: %6d'%(dictionary.num_docs, len(list(dictionary.values()))))
print(list(dictionary.values()))

"""## Metrics"""

def stats_about_the_docs(docs, feature):
  total_size = 0
  max_size = 0
  min_size = 999

  for i in docs:
    length = len(i)
    total_size += length
  
    if length > max_size:
      max_size = length

    if length < min_size and length != 0:
      min_size = length
    
  print(f"{'-'*10} {feature} {'-'*10}")
  print(f"Average # of {feature}: {int(total_size / len(docs))}")
  print(f"Max # of {feature}: {max_size}")
  print(f"Min # of {feature}: {min_size}")

stats_about_the_docs(bdocs, 'Words')

"""## Wordcloud"""

def create_single_string(tokens):
  output = ''
  for i in tokens:
    for j in i:
      output += j + " "

  return output

output = create_single_string(bdocs)
output

import wordcloud as wc
import matplotlib.pyplot as plt

mycloud = wc.WordCloud().generate(output)
plt.figure(figsize=(20,10))
plt.imshow(mycloud)

"""## Feature Extraction"""

def join_docs(docs):
  docs = []

  for i in bdocs:
    for j in i:
      docs.append(j)

  return docs

joined_docs = join_docs(bdocs)

from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(joined_docs)

features  = vectorizer.get_feature_names_out()
dense     = X.todense()
denseList = dense.tolist()

df = pd.DataFrame(denseList, columns=set(features))
for feature in df.columns:
  print(feature, df[feature].unique())

"""## Model"""

def get_coherence(mdl):
	average_coherence = 0
	for preset in ['c_v']:
		coh = tp.coherence.Coherence(mdl, coherence=preset)
		average_coherence = coh.get_score()
	return average_coherence

def runModel(mdl, docs):
	for i, d in enumerate(docs):
		mdl.add_doc(d)
	
	mdl.burn_in = 100
	mdl.train(0)
 
	for i in range(0, 100, 2):
		mdl.train(10)
	# mdl.save('test.lda.bin', True)

def printTopics(mdl, p=False, top_n=10):
	for k in range(mdl.k):
		print(f" -> Topic #{k}")

		for word, prob in mdl.get_topic_words(topic_id=k, top_n=top_n):
			if p:
				print(f"{'%20s' % word} ({'%.2f' % prob})", end=" ")
			else:
	 			print(f"{word.strip()}", end=" ")
		print()

mdl, best_model = None, None
cv_scores = []
step = 2

for i in range(1, len(bdocs)+1, step):
  mdl = tp.LDAModel(tw=tp.TermWeight.IDF, min_cf=3, rm_top=5, k=i, seed=777)
  print(f"{i} out of {len(bdocs)}")

  runModel(mdl, bdocs)

  current_coherence = get_coherence(mdl)
  cv_scores.append(current_coherence)

  if current_coherence >= max(cv_scores):
    best_model = mdl

print(cv_scores)

plt.grid()
x = range(1, len(bdocs)+1, step)
plt.plot(x, cv_scores, marker='o')
plt.figure(figsize=(15, 10))
plt.show()

print(f"\nHighest coherence is doc #{max(zip(cv_scores, x))[1]} with {'%.4f' % max(zip(cv_scores, x))[0]}")

printTopics(best_model, p=True, top_n=10)

