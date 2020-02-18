import json
import pymorphy2 as pm
from os import listdir
from os.path import isfile, join


def extract_entities(filename):
    ans = set()
    with open(filename) as file:
        for line in file:
            ans.add(line.strip().split('\t')[-1])
    return ans


def write_dict(filename, entities):
    with open(filename, 'w') as outfile:
        json.dump(entities, outfile)


morph = pm.MorphAnalyzer()


def transform_entitity(ngram):
    if len(ngram.split()) == 1:
        if ngram[0].isupper():
            return ngram[0] + morph.parse(ngram)[0].normal_form[1:]
        else:
            return morph.parse(ngram)[0].normal_form

    if len(ngram.split()) > 2:
        return ngram

    w1, w2 = ngram.split()[0], ngram.split()[1]
    gender = morph.parse(w2)[0].tag.gender
    if w2[0].isupper():
        w2 = w2[0] + morph.parse(w2)[0].normal_form[1:]
    else:
        w2 = morph.parse(w2)[0].normal_form
    parsed = morph.parse(w1)[0]
    if 'NOUN' in parsed.tag:
        if w1[0].isupper():
            return w1[0] + parsed.normal_form[1:] + ' ' + w2
        else:
            return parsed.normal_form + ' ' + w2
    elif 'UNKN' in parsed.tag:
        return w1 + ' ' + w2
    elif 'ADJF' in parsed.tag or 'ADJS' in parsed.tag:
        if gender is None:
            return w1 + ' ' + w2
        else:
            return parsed.normalized.inflect({gender}).word + ' ' + w2
    return ngram


if __name__ == '__main__':
    mypath = 'named_entities/'
    files = [join(mypath, f) for f in listdir(mypath) if isfile(join(mypath, f)) and f.endswith('.ann')]
    entities = set()
    for file in files:
        entities = entities.union(extract_entities(file))
    entities = list(entities)
    entities_norm = [transform_entitity(e) for e in entities]
    print(len(entities))
    print(entities[:10])
    print(entities_norm[:10])
    write_dict('named_entities.json', entities_norm)
