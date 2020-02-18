import json
import hw1.morph as morph
from gensim.models import KeyedVectors
import numpy as np


LIMIT = 300
input1 = "example_texts.json"
input2 = "dataset_43428_1.txt"
xml_dict = '../hw1/dict.opcorpora.xml'
xml_corpus = '../hw1/annot.opcorpora.no_ambig.xml'

middle_punctuation_remover = str.maketrans({key: None for key in [',', ':', ';', '«', '»', '-', '(', ')', '—', '%', '&', '*', '^', '$', '#']})
end_punctuation = ['.', '?', '!']
end_punctuation_remover = str.maketrans({key: None for key in end_punctuation})
anafors = ['этот', 'это', 'эта', 'эту', 'этих', 'этого', 'этим', 'этой', 'этими', 'этом', 'эти']
anafors_punctuation = ['-', '—']
silly_words = ['']
with open("../hw2/stop-words.txt") as f:
    for line in f:
        silly_words.append(line.strip())


def build_dictionary(text):
    text = text.translate(end_punctuation_remover)
    dict = {}
    words = text.split(" ")
    for word in words:
        if word in silly_words or word.isdigit() or len(word) < 3:
            continue
        word, _ = morph.choose_lemma(word, -1)
        if dict.get(word) is None:
            dict[word] = 1
        else:
            dict[word] += 1
    return dict


def build_bigrams(text):
    text = text.translate(end_punctuation_remover)
    bigrams = {}
    words = text.split(" ")
    prev = ''
    for word in words:
        if prev == '' or word in silly_words:
            continue
        word, _ = morph.choose_lemma(word, -1)
        pair = (prev, word) if prev < word else (word, prev)
        if bigrams.get(pair) is None:
            bigrams[pair] = 1
        else:
            bigrams[pair] += 1
        prev = word
    return bigrams


def get_sentence_end(text, start):
    for i in range(start, len(text)):
        if text[i] in end_punctuation:
            return i
    return -1


def get_sentences(text):
    sentences = []
    start = 0
    while start != -1:
        end = get_sentence_end(text, start)
        if end != -1:
            if text[end] == '?':
                start = end + 1
                continue
            end += 1
            sentence = text[start:end].strip()
        else:
            sentence = text[start:].strip()
        start = end
        if len(sentence) < 3:
            continue
        sentences.append(sentence)
    return sentences


def preproocess_text(text):
    text = text.strip().replace("\n", ". ")
    text = ' '.join(text.split())
    text = text.translate(middle_punctuation_remover)
    return text


def find_anafor(words):
    for word in words:
        if word in anafors:
            return word
    return None


'''def make_anafored_sentence(anafor, sentence, weight, sentence_prev, weight_prev):
    flag = False
    for punct in anafors_punctuation:
        if sentence.find(anafor) > sentence.find(punct) != -1:
            flag = True
            break
    if flag
    return sentence_prev + sentence, (weight_prev + weight) / 2.'''


def get_closest_words(model, dict, top=3):
    print("finished")
    closest = {}
    for word1 in dict.keys():
        if not (word1 in model.vocab):
            continue
        words = dict.keys()
        weights = []
        for word2 in words:
            if not (word2 in model.vocab):
                continue
            weights.append(model.similarity(word1, word2))
        _, words = zip(*sorted(zip(weights, words), reverse=True))
        closest[word1] = words[1:top + 1]
    return closest


def build_with_frequencies(model, text):
    text = preproocess_text(text)
    dict = build_dictionary(text)
    closest_dict = get_closest_words(model, dict, 3)
    bigrams = build_bigrams(text)
    sentences = get_sentences(text)

    if len(sentences) == 0:
        return text[:LIMIT]

    weights = []
    for sentence in sentences:
        weight = 0.
        words = sentence.translate(end_punctuation_remover).split(" ")
        if len(words) < 4 or not (find_anafor(words[:4]) is None):
            weights.append(0)
            continue

        prev = ''
        for word in words:
            word, _ = morph.choose_lemma(word, -1)
            if dict.get(word) is None:
                continue
            weight += dict[word]
            closest = closest_dict.get(word)
            if not (closest is None):
                for word2 in closest:
                    weight += dict[word2] / 3.
            pair = (prev, word) if prev < word else (word, prev)
            if bigrams.get(pair) is None:
                continue
            weight += bigrams[pair]
        weight = weight * 1. / len(sentence)
        # weight = weight + 1. / 3. if sent_len <= text_len / 3. else weight
        weights.append(weight)

    for i in range(len(weights) // 3):
        weights[i] += 1./2.
    weights, sentences = zip(*sorted(zip(weights, sentences), reverse=True))
    length = 0
    result = ""
    for i in range(len(sentences)):
        result += sentences[i]
        length += len(sentences[i])
        if length >= LIMIT:
            break
    return result


def build_with_beginning(text):
    text = text.strip().replace("\n", " ")
    return text[:LIMIT].strip()


def main():
    morph.read_lemmas(xml_dict)
    morph.read_forms(xml_dict)
    morph.read_corpus(xml_corpus)
    model = KeyedVectors.load_word2vec_format('/home/katyakos/jb_news/VectorX_mediaplanning/base_topics/vectors/wiki.ru.vec')

    with open(input2) as f:
        data = json.load(f)
    n = len(data)
    referators = []
    for i in range(n):
        referators.append(build_with_frequencies(model, data[i].lower()))

    out = open("result.json", "w+")
    out.write("[\n")
    for i in range(n):
        out.write("    \"")
        out.write(referators[i])
        if i != n - 1:
            out.write("\",\n")
        else:
            out.write("\"\n")
    out.write("]")


if __name__ == '__main__':
    main()
