import numpy as np
import csv
import codecs
import hw1.morph as morph
import hw2.refer as refer
from scipy.sparse import csr_matrix
from sklearn import svm
import gensim
import gensim.downloader as api

def read_annotated_dict():
    annot_dict = {}
    f_annot_dict = 'annot_dict.csv'
    with codecs.open(f_annot_dict, 'r', encoding='cp1251') as fin:
        fin.readline()
        n = 0
        for line in fin:
            cells = line.strip().replace("\"", "").split(';')
            word = cells[0]
            lab = int(cells[3])
            if lab != 0:
                annot_dict[word] = (abs(lab), n)
                n += 1
    return annot_dict


def read_dict(file):
    dict = {}
    n = 0
    fin = open(file, 'r')
    for sent in fin:
        line = sent.strip().lower().translate(refer.middle_punctuation_remover)
        line = line.translate(refer.end_punctuation_remover)
        words = line.split(' ')
        for word in words:
            word, pos = morph.choose_lemma(word, -1)
            if pos in ["S", "A", "V", "NI"] and not (word in refer.silly_words):
                if dict.get(word) is None:
                    dict[word] = (1., pos)
                    n += 1
                else:
                    old_f, pos = dict[word]
                    dict[word] = (old_f + 1., pos)
    fin.close()
    n = 0
    res = {}
    for key in dict.keys():
        if dict[key][0] >= 10.:
            res[key] = (1., n)
            n += 1
            if dict[key][1] in ["A", "V"]:
                res["не " + key] = (1., n)
                n += 1
    return res


def extract_features(file, dict, extra_lines, annotated_dict = None):
    words_num = len(dict)
    fin_corp = open(file, 'r')
    rows = []
    cols = []
    data = []
    n = 0
    for line in fin_corp:
        words = line.strip().translate(refer.middle_punctuation_remover).translate(refer.end_punctuation_remover).split(' ')
        weight = 1.
        if line.endswith('!'):
            weight = 2.
        line_data = [0.] * words_num
        unzero_num = 0.
        prev = ""
        for word in words:
            lemma, pos = morph.choose_lemma(word.lower(), -1)
            if prev == "не" and pos in ["A", "V"]:
                lemma = "не " + lemma
                #lbl *= 0.
            if not (dict.get(lemma) is None):
                #lbl, idx = dict[lemma]
                #if not (annotated_dict is None or annotated_dict.get(lemma) is None):
                #    lbl, _ = annotated_dict[lemma]
                lbl, idx = dict[lemma]
                if line_data[idx] == 0.:
                    unzero_num += 1.
                if word == word.upper():
                    line_data[idx] += weight * 2. #* lbl
                else:
                    line_data[idx] += weight #* lbl
            prev = word
        for j in range(words_num):
            if line_data[j] == 0.:
                continue
            rows.append(n)
            cols.append(j)
            data.append(line_data[j] / unzero_num)
        n += 1
    fin_corp.close()
    data = csr_matrix((data, (rows, cols)), shape=(n + extra_lines, words_num))
    return data


def process_corpus(corpus_name = 'texts_train.txt', labels_name = 'scores_train.txt', input_corpus = 'dataset_40757_1.txt'):
    dict = read_dict(corpus_name)
    #annotated_dict = read_annotated_dict()
    print("read current dict")
    print(len(dict))

    labels = []
    fin_lab = open(labels_name, 'r')
    for line in fin_lab:
        labels.append(int(line.strip()))
    fin_lab.close()
    for i in range(1000):
        labels.append(5)
    data = extract_features(corpus_name, dict, 1000)#, annotated_dict)
    print("extracted features")
    test_data = extract_features(input_corpus, dict, 0)#, annotated_dict)
    print("extracted test features")

    clf = svm.LinearSVC(multi_class="crammer_singer", max_iter=10000)
    clf.fit(data, labels)
    print("finished fitting")
    result_labels = clf.predict(test_data)
    print("finished predicting")
    result = open('result.txt', 'w')
    for label in result_labels:
        result.write(str(label) + "\n")
    result.close()


def main():
    #model = api.load("word2vec-ruscorpora-300")
    #print(model.most_similar(positive=['мужчина_NOUN', 'король_NOUN'], negative=['женщина_NOUN']))

    xml_dict = '../hw1/dict.opcorpora.xml'
    xml_corpus = '../hw1/annot.opcorpora.no_ambig.xml'
    morph.read_lemmas(xml_dict)
    print("read lemmas")
    morph.read_forms(xml_dict)
    print("read forms")
    morph.read_corpus(xml_corpus)
    print("read lemmatic corpus")
    #read_annotated_dict()
    process_corpus()


if __name__ == '__main__':
    main()
