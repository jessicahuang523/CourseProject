import os
import sys
sys.path.append(f'{os.getcwd()}/..')
import common
import numpy as np
from collections import defaultdict
from gensim.models import KeyedVectors


loaded_models = dict()  # key: model name -> val: loaded model


def clear_model_cache():
    global loaded_models
    del loaded_models
    loaded_models = dict()


def load_model(model_name, cache_models=False):
    """
    :param model_name: name of model (do not provide full path, just filename)
    :param cache_models: whether to keep model open (higher mem usage, but much faster if you're calling
        this function multiple times with the same model)
    :return: gensim.models.KeyedVectors model
    """
    model_name = model_name.split('.')[0]
    if model_name in loaded_models:
        return loaded_models[model_name]

    if cache_models:
        if model_name not in loaded_models:
            if os.path.exists(f'{common.new_model_dir}/{model_name}.w2v'):
                loaded_models[model_name] = KeyedVectors.load(f'{common.new_model_dir}/{model_name}.w2v', mmap='r')
            elif os.path.exists(f'{common.old_model_dir}/{model_name}.w2v'):
                loaded_models[model_name] = KeyedVectors.load(f'{common.old_model_dir}/{model_name}.w2v', mmap='r')
            else:
                raise Exception(f"There is no model named {model_name}. Be sure to pass only a filename, "
                                f"not a full filepath.")
        return loaded_models[model_name]

    else:
        if os.path.exists(f'{common.new_model_dir}/{model_name}.w2v'):
            return KeyedVectors.load(f'{common.new_model_dir}/{model_name}.w2v', mmap='r')
        elif os.path.exists(f'{common.old_model_dir}/{model_name}.w2v'):
            return KeyedVectors.load(f'{common.old_model_dir}/{model_name}.w2v', mmap='r')
        else:
            raise Exception(f"There is no model named {model_name}. Be sure to pass only a filename, "
                            f"not a full filepath.")


def get_knn_ddicts(word, model_names, k, cache_models=False):
    """
    compute kNN word similarities by decade
    :param word: the word we're examining over time
    :param model_names: list of model names, in order (do not provide full path, just filename)
    :param k: the number of neighbors to look at
    :param cache_models: whether to keep model(s) open (higher mem usage, but much faster if you're calling
        this function multiple times with the same model(s))
    :return: kNN defaultdicts for use in knn_ccla()
    """
    knn_ddicts = dict()
    for model_name in model_names:
        model = load_model(model_name, cache_models)
        model_ddict = defaultdict(float)

        model_word = None
        if model.has_index_for(word.upper()):
            model_word = word.upper()
        elif model.has_index_for(word.lower()):
            model_word = word.lower()

        if model_word:
            for neighbor, similarity in model.most_similar(model_word, topn=k):
                model_ddict[neighbor] = similarity
        knn_ddicts[model_name] = model_ddict
    return knn_ddicts


def knn_ccla(knn_ddict_c1, knn_ddict_c2):
    """
    compute CCLA score with respect to the k nearest neighbors between contexts C1, C2
    :param knn_ddict_c1: a defaultdict(float) of k nearest neighbors in C1,
        with key: word -> val: cosine similarity
    :param knn_ddict_c2: same as knn_ddict_c1, but for C2
    :return: CCLA score
    """
    numerator = 0
    for word, similarity in knn_ddict_c1.items():
        if word in knn_ddict_c2:
            numerator += similarity * knn_ddict_c2[word]
        # (else, don't add anything, because it'd just be 0)
        # (keep it this way to avoid adding to knn_ddict_c2 and screwing up knn_ddict_c2.values() below)
    denominator = np.linalg.norm(list(knn_ddict_c1.values())) * np.linalg.norm(list(knn_ddict_c2.values()))
    if denominator > 0:
        return numerator / denominator
    else:
        return 0
