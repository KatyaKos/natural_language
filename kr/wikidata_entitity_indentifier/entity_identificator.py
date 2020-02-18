import pymorphy2 as pm
import string
import pywikibot
import json


def read_data(file_name):
    uids, sentences = [], []
    with open(file_name) as file:
        data = json.load(file)
        for question in data:
            uids.append(question['uid'])
            sentences.append(question['q'])
    return sentences, uids


def read_entities(filename):
    entities_dict = []
    with open(filename) as file:
        data = json.load(file)
        for entity in data:
            entities_dict.append(entity)
    return entities_dict


def write_answer(file_name, uids, qualifiers):
    data = []
    for i, id in enumerate(uids):
        dict = {}
        dict['uid'] = id
        dict['entities'] = qualifiers[i]
        data.append(dict)
    with open(file_name, 'w') as outfile:
        json.dump(data, outfile)


def entities_grams(sentences, entities_dict, window = 3):
    morph = pm.MorphAnalyzer()
    punctuation_table = str.maketrans('', '', string.punctuation)
    processed = []
    for s in sentences:
        s = s.translate(punctuation_table)
        words = s.split()
        grams, bigrams = [], []
        for i in range(len(words)):
            w = words[i]
            parsed = morph.parse(w)[0]
            if w[0].isupper():
                w = w[0] + parsed.normal_form[1:]
            else:
                w = parsed.normal_form
            if not ('NOUN' in parsed.tag or 'UNKN' in parsed.tag) and not (w in entities_dict):
                continue

            gender = parsed.tag.gender
            grams.append(w)
            for j in range(max(0, i - window), i):
                parsed = morph.parse(words[j])[0]
                if 'NOUN' in parsed.tag:
                    if words[j][0].isupper():
                        bigrams.append(words[j][0] + parsed.normal_form[1:] + ' ' + w)
                    else:
                        bigrams.append(parsed.normal_form + ' ' + w)
                elif 'UNKN' in parsed.tag:
                    bigrams.append(words[j] + ' ' + w)
                elif 'ADJF' in parsed.tag or 'ADJS' in parsed.tag:
                    if gender is None:
                        bigrams.append(words[j] + ' ' + w)
                    else:
                        bigrams.append(parsed.normalized.inflect({gender}).word + ' ' + w)
        processed.append([grams, bigrams])
    return processed


def get_qualifiers(tokenized):
    site = pywikibot.Site("ru", "wikipedia")

    def api(gram):
        try:
            page = pywikibot.Page(site, gram)
            if page.isRedirectPage():
                page = page.getRedirectTarget()
            item = pywikibot.ItemPage.fromPage(page)
            return item.getID()
        except Exception as ex:
            return None

    identifs = []
    for s in tokenized:
        grams, bigrams = s[0], s[1]
        grams_id, bigrams_id = [], []
        for gr in grams:
            grams_id.append(api(gr))
        for gr in bigrams:
            bigrams_id.append(api(gr))
        identifs.append([grams_id, bigrams_id])
    return identifs


def filter_qualifiers(grams, qualifs):
    answer_qualifs, answer_grams = [], []
    for i, s in enumerate(qualifs):
        answer_q, answer_g = [], []
        w_grams, w_bigrams = grams[i][0], grams[i][1]
        q_grams, q_bigrams = s[0], s[1]
        for j, big in enumerate(q_bigrams):
            if big:
                answer_q.append(big)
                answer_g.append(w_bigrams[j])
        for j, g in enumerate(w_grams):
            flag = False
            for word in answer_g:
                if g in word:
                    flag = True
                    break
            if flag:
                continue
            if q_grams[j]:
                answer_q.append(q_grams[j])
                answer_g.append(g)
        answer_qualifs.append(answer_q)
        answer_grams.append(answer_g)
    return answer_grams, answer_qualifs


if __name__ == '__main__':
    file = 'hw_task.json'
    sentences, uids = read_data(file)
    sentences, uids = sentences, uids
    entities_dict = read_entities('named_entities.json')
    print(sentences)
    tokens = entities_grams(sentences, entities_dict)
    #print(tokens)
    qualifs = get_qualifiers(tokens)
    #print(qualifs)
    answer_grams, answer_qualifs   = filter_qualifiers(tokens, qualifs)
    #print(answer_grams)
    #print(answer_qualifs)
    write_answer('koshchenko_result.json', uids, answer_qualifs)