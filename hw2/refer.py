import json
import hw1.morph as morph


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
with open("stop-words.txt") as f:
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


def find_anafor(words):
    for word in words:
        if word in anafors:
            return word
    return None


def get_sorted_sentences(text, dict, bigrams):
    sentences = []
    weights = []

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
        sent_len += len(sentence)

        weight = 0.
        words = sentence.translate(end_punctuation_remover).split(" ")
        if len(sentence) < 3:
            continue
        if len(words) < 4:
            sentences.append(sentence)
            weights.append(0)
            continue

        prev = ''
        for word in words:
            word, _ = morph.choose_lemma(word, -1)
            if dict.get(word) is None:
                continue
            weight += dict[word]
            pair = (prev, word) if prev < word else (word, prev)
            if bigrams.get(pair) is None:
                continue
            weight += bigrams[pair]
        weight = weight * 1. / len(sentence)
        # weight = weight + 1. / 3. if sent_len <= text_len / 3. else weight

        if find_anafor(words[:4]) is None:
            sentences.append(sentence)
            weights.append(weight)
        else:
            continue
            '''anaf = find_anafor(words[:4])
            flag = False
            for punct in anafors_punctuation:
                if sentence.find(anaf) > sentence.find(punct) != -1:
                    flag = True
                    break
            if len(sentences) == 0 or flag:
                sentences.append(sentence)
                weights.append(weight)
            else:
                sentences[-1] = sentences[-1] + sentence
                weights[-1] = (weights[-1] + weight) / 2.'''
    return sentences, weights


def preproocess_text(text):
    text = text.strip().replace("\n", ". ")
    text = ' '.join(text.split())
    text = text.translate(middle_punctuation_remover)
    return text


def build_with_frequencies(text):
    text = preproocess_text(text)
    dict = build_dictionary(text)
    bigrams = build_bigrams(text)
    sentences, weights = get_sorted_sentences(text, dict, bigrams)

    if len(sentences) == 0:
        return text[:LIMIT]
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

    with open(input2) as f:
        data = json.load(f)
    n = len(data)
    referators = []
    for i in range(n):
        referators.append(build_with_frequencies(data[i].lower()))

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
