#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import random

forms = {}
dictionary = {}
xml_dict = 'dict.opcorpora.xml'
xml_corpus = 'annot.opcorpora.no_ambig.xml'
text = 'dataset_37845_1.txt'
posts = {"noun" : "S", "adjf" : "A", "adjs" : "A", "comp" : "A", "verb" : "V", "infn" : "V", "prtf" : "V",
         "prts" : "V", "grnd" : "V", "advb" : "ADV", "pred" : "ADV", "prcl" : "ADV", "intj" : "ADV",
         "prep" : "PR", "conj" : "CONJ", "numr" : "NI", "npro" : "NI"}
post_ids = {"S" : 0, "A" : 1, "V" : 2, "PR" : 3, "CONJ" : 4, "ADV" : 5, "NI" : 6}
lemma_freqs = {}


def read_lemmas(file_xml='dict.opcorpora.xml'):
    file = open(file_xml, "r")
    for line in file:
        if "<lemmata>" in line:
            break
    for line in file:
        if "</lemmata>" in line:
            break
        line = line.lower().replace("ё", "е")
        root = ET.fromstring(line)
        id = int(root.attrib['id'])
        lemma = root.find('l')
        dictionary[id] = (lemma.attrib['t'], lemma.find('g').attrib['v'])
    for line in file:
        if "<links>" in line:
            break
    for line in file:
        if "</links>" in line:
            break
        root = ET.fromstring(line)
        type = int(root.attrib['type'])
        if type <= 6 or type == 26:
            i = int(root.attrib['from'])
            j = int(root.attrib['to'])
            dictionary[j] = dictionary[i]

    for i in dictionary:
        post = posts[dictionary[i][1]]
        if post is None:
            post = "NI"
        dictionary[i] = (dictionary[i][0], post)

    file.close()


def read_forms(file_xml='dict.opcorpora.xml'):
    file = open(file_xml, "r")
    for line in file:
        if "<lemmata>" in line:
            break
    for line in file:
        if "</lemmata>" in line:
            break
        line = line.lower().replace("ё", "е")
        #print(line)
        root = ET.fromstring(line)
        id = int(root.attrib['id'])
        for tag in root.findall('f'):
            form = tag.attrib['t']
            if forms.get(form) is None:
                forms[form] = [dictionary[id]]
            else:
                forms[form].append(dictionary[id])

    for key in forms:
        forms[key] = list(set(forms[key]))

    file.close()


def read_corpus(file_xml='annot.opcorpora.no_ambig.xml'):
    tree = ET.parse(file_xml)
    root = tree.getroot()
    for text in root.findall('text'):
        for paragraph in text.find('paragraphs').findall('paragraph'):
            for sentence in paragraph.findall('sentence'):
                pr = -1
                for token in sentence.find('tokens').findall('token'):
                    tmp = token.find('tfr').find('v').find('l')
                    if pr == -1:
                        post = tmp.find('g').attrib['v'].lower()
                        if posts.get(post) is None:
                            continue
                        post = posts[post]
                        if post is None:
                            post = "NI"
                        pr = post_ids[post]
                    else:
                        post = tmp.find('g').attrib['v']
                        if post == "PNCT":
                            continue
                        if dictionary.get(int(tmp.attrib['id'])) is None:
                            continue
                        lemma = dictionary[int(tmp.attrib['id'])]
                        if lemma_freqs.get(lemma[0]) is None:
                            lemma_freqs[lemma[0]] = [0, 0, 0, 0, 0, 0, 0]
                            lemma_freqs[lemma[0]][pr] = 1
                        else:
                            lemma_freqs[lemma[0]][pr] += 1
                        pr = post_ids[lemma[1]]


def choose_lemma(word, prev):
    if forms.get(word) is None:
        return word, "NI"
    lemmas = forms[word]
    if len(lemmas) == 1:
        return lemmas[0][0], lemmas[0][1]
    else:
        max_l = ""
        max_p = ""
        max_f = -1
        for lemma in lemmas:
            if lemma[1] == "CONJ" or lemma[1] == "PR":
                max_l = lemma[0]
                max_p = lemma[1]
                break
            if lemma_freqs.get(lemma[0]) is None:
                continue
            if prev == -1:
                if max_f < sum(lemma_freqs[lemma[0]]):
                    max_f = sum(lemma_freqs[lemma[0]])
                    max_l = lemma[0]
                    max_p = lemma[1]
            else:
                if max_f < lemma_freqs[lemma[0]][prev]:
                    max_f = lemma_freqs[lemma[0]][prev]
                    max_l = lemma[0]
                    max_p = lemma[1]
        if max_f == -1:
            lemma = random.choice(lemmas)
            return lemma[0], lemma[1]
        else:
            return max_l, max_p


def process_text(file_txt):
    file = open(file_txt, "r")
    out = open("result.txt", "w+")
    for line in file:
        line = line.replace(",", "").replace(".", "").replace("?", "").replace("!", "").strip()
        words = line.split(" ")
        pr = -1
        res = ""
        for word in words:
            res += word + "{"
            word = word.lower().replace("ё", "е")
            if forms.get(word) is None:
                res += word + "=NI} "
            else:
                lemma, post = choose_lemma(word, pr)
                res += lemma + "=" + post + "} "
                pr = post_ids[post]
        out.write(res + "\n")

    file.close()
    out.close()


def main():
    read_lemmas(xml_dict)
    read_forms(xml_dict)
    read_corpus(xml_corpus)
    process_text(text)


if __name__ == '__main__':
    main()
