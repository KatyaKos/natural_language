import json


def read_real_answers(filename):
    res = {}
    n  = 0
    with open(filename) as file:
        data = json.load(file)
        for ans in data:
            res[ans['uid']] = ans['entities']
            n += len(ans['entities'])
    print(n)
    return res


def evaluate(filename, real_ans):
    tp, fp, fn = [], [], []
    with open(filename) as file:
        data = json.load(file)
        for ans in data:
            uid =  ans['uid']
            if uid in real_ans:
                ttp, ffp, ffn = 0, 0, 0
                my_ents = ans['entities']
                real_ents = real_ans[uid]
                for ent in my_ents:
                    if ent in real_ents:
                        ttp += 1
                    else:
                        ffp += 1
                ffn = len(real_ents) - ttp
                tp.append(ttp)
                fp.append(ffp)
                fn.append(ffn)
    print(sum(tp), sum(fp), sum(fn))

    micro_ap = sum(tp) / (sum(tp) + sum(fp))
    micro_ar = sum(tp) / (sum(tp) + sum(fn))
    return micro_ap, micro_ar



if __name__ == '__main__':
    my_ans_file, real_ans_file = 'results/koshchenko_named-1-2-grams_result.json', 'results/answers.json'
    real_ans = read_real_answers(real_ans_file)
    micro_ap, micro_ar = evaluate(my_ans_file, real_ans)
    print("micro-AP:", micro_ap)
    print('micro-AR:', micro_ar)
