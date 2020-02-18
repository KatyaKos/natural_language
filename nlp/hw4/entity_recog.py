import numpy as np
from tqdm import tqdm
import re
from natasha import NamesExtractor, PersonExtractor, OrganisationExtractor

input_data = "train_sentences.txt"
labels_data = "train_nes.txt"
test_data = "dataset_40163_1.txt"
silly_words = ['']
with open("../hw2/stop-words.txt") as f:
    for line in f:
        silly_words.append(line.strip().lower())
with open("countries.txt") as f:
    for line in f:
        silly_words.append(line.strip().lower())


def natasha_process():
    extractors = [NamesExtractor(), PersonExtractor(), OrganisationExtractor()]

    result = []

    with open(test_data) as file_data:
        for i, text in tqdm(enumerate(file_data)):
            result.append([extr(text) for extr in extractors])

    output = []

    for line in result:
        output.append({})
        for i, extr in enumerate(line):
            for match in extr:
                output[-1][(match.span[0], match.span[1])] = 'PERSON' if i != 2 else 'ORG'
    with open('res.txt', 'w') as file_res:
        with open(test_data, 'r') as file_data:
            for line in output:
                tmp = []
                processed = []
                s = file_data.readline()
                for key in line:
                    k1, k2 = key
                    sub = s[k1:k2]
                    for el in sub.split(' '):
                        if k1 in processed:
                            continue
                        processed.append(k1)
                        tmp.append(str(k1) + " " + str(len(el)) + " " + line[key] + " ")
                        #file_res.write(str(k1) + " " + str(len(el)) + " " + line[key] + " ")
                        k1 += len(el) + 1
                tmp.sort()
                for l in tmp:
                    file_res.write(l)
                file_res.write('EOL\n')



def tokenize(fname, punctuation_remover):
    result = []
    with open(fname, 'r') as fin:
        for line in fin:
            tmp = []
            words = line.strip().split(' ')
            i = 0
            for word in words:
                if word.startswith("«"):
                    i += 1
                    word = word[1:]
                w = word.translate(punctuation_remover)
                tmp.append([w, i, len(w)])
                i += len(word) + 1
            result.append(tmp)
    return result


def names_extract():
    names = []
    surnames = []
    with open("vocabs/russian_names.csv", 'r') as fin:
        print(fin.readline())
        for line in fin:
            w = line.split(';')
            if isRussian(w[1]) and int(w[3]) > 500:
                names.append(w[1])
    with open("vocabs/russian_surnames.csv", 'r') as fin:
        print(fin.readline())
        for line in fin:
            w = line.split(';')
            if isRussian(w[1]) and int(w[3]) > 500:
                surnames.append(w[1])
    return set(names), set(surnames)


def distance(a, b):
    l = 0
    while a[l] == b[l]:
        l += 1
        if l == len(a) or l == len(b):
            break
    return max(len(a), len(b)) - l


def preprocess():
    labeled_data = {}
    lines = tokenize("train_sentences_enhanced.txt", str.maketrans({key: None for key in [':', ';', '!', '?', '«', '»', '.']}))
    for line in lines:
        flag, prev = "", ""
        for word, _, _ in line:
            if "{ORG}" in word:
                w = word.split("{ORG}")[0]
                if flag == "ORG":
                    #labeled_data.pop(prev, None)
                    w = prev + " " + w
                labeled_data[w] = "ORG"
                flag, prev = "ORG", w
            elif "{PERSON}" in word:
                w = word.split("{PERSON}")[0]
                if flag == "PERSON":
                    labeled_data.pop(prev, None)
                    w = prev + " " + w
                labeled_data[w] = "PERSON"
                flag, prev = "PERSON", w
            else:
                flag, prev = "", ""
            if word.endswith(','):
                flag, prev = "", ""
    return labeled_data


def isRussian(word):
    for char in word:
        o = ord(char)
        if o < ord("А") or o > ord("я"):
            return False
    return True


def isEnglish(word):
    for char in word:
        o = ord(char)
        if o < ord("a") or o > ord("z"):
            return False
    return True


def process(fname=test_data, win=5):
    lines = tokenize(fname, str.maketrans({key: None for key in [',', ':', ';', '!', '?', '«', '»', '.']}))
    labeled_data = preprocess()
    names, surnames = names_extract()
    res = []
    #lines_punct = tokenize(fname, str.maketrans({key: None for key in [',', ':', ';', '!', '?', '.']}))
    for lid, line in enumerate(lines):
        n = len(line)
        processed = []
        tmp = []
        prev = ""
        #bracks = 0
        for i in range(n):
            w = line[i][0].lower()
            m = len(w)
            if w in silly_words or m > 5 and (w[:m - 1] in silly_words or w[:m - 2] in silly_words):
                continue
            flag = False
            if line[i][1] in processed:
                continue
            '''if "«" in lines_punct[lid][i][0]:
                processed.append(line[i][1])
                prev = "ORG"
                bracks += 1
                tmp.append([line[i][1], m, "ORG"])
                continue
            if bracks > 0:
                if "»" in lines_punct[lid][i][0]:
                    bracks -= 1
                processed.append(line[i][1])
                tmp.append([line[i][1], m, prev])
                continue'''
            phrase = ""
            for j in range(win):
                if i + j == n:
                    break
                phrase += line[i + j][0]
                if labeled_data.get(phrase) is None:
                    phrase += " "
                    continue
                prev = labeled_data[phrase]
                flag = True
                for k in range(i, i + j + 1):
                    if line[k][1] in processed:
                        continue
                    processed.append(line[k][1])
                    tmp.append([line[k][1], len(line[k][0]), labeled_data[phrase]])
                    break
            w = line[i][0]
            if not (line[i][1] in processed):
                if w in names or w in surnames or m > 5 and\
                        (w[:m - 1] in names or w[:m - 1] in surnames or w[:m - 2] in names or w[:m - 2] in surnames):
                    processed.append(line[i][1])
                    prev = "PERSON"
                    flag = True
                    tmp.append([line[i][1], m, "PERSON"])
                elif prev != "" and w[:1].isupper():
                    processed.append(line[i][1])
                    flag = True
                    tmp.append([line[i][1], m, prev])
                elif (line[i][1] != 0 or m > 1) and w.isupper():
                    prev = "ORG"
                    flag = True
                    processed.append(line[i][1])
                    tmp.append([line[i][1], m, "ORG"])
                elif isEnglish(w.lower()):
                    prev = "ORG"
                    flag = True
                    processed.append(line[i][1])
                    tmp.append([line[i][1], m, "ORG"])
            if not flag:
                prev = ""

        res.append(tmp)
    return res




def main():
    #model = api.load("word2vec-ruscorpora-300")
    #print(model.most_similar(positive=['мужчина_NOUN', 'король_NOUN'], negative=['женщина_NOUN']))
    res = process()
    fout = open("res.txt", "w")
    for line in res:
        for token in line:
            fout.write(str(token[0]) + " " + str(token[1]) + " " + token[2] + " ")
        fout.write("EOL\n")


if __name__ == '__main__':
    main()
