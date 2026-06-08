f = "eval_amc_baseline.py"
s = open(f).read()
old = 'is_correct = predicted is not None and predicted.strip() == gold_answer.strip()'
new = ('try:\n'
       '        is_correct = predicted is not None and abs(float(str(predicted).replace(",","")) - float(str(gold_answer).replace(",",""))) < 1e-6\n'
       '    except (ValueError, TypeError):\n'
       '        is_correct = False')
assert old in s, "F3 anchor not found - already patched or file differs"
open(f, "w").write(s.replace(old, new))
print("F3 patched:", f)
