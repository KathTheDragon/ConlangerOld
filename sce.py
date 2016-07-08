"""Apply sound changes to a lexicon

Classes:
    Cat  -- represents a category of phonemes
    Rule -- represents a sound change rule
    Word -- represents a run of text

Functions:
    run  -- applies the sound changes to the lexicon
""""""
==================================== To-do ====================================
=== Bug-fixes ===

=== Implementation ===
Utilise new implementation of Word as sequence type
- investigate reindexing Word
Check that tar still matches immediately before replacement (difficult)
Check if a rule is able to run infinitely and raise an exception if it can
- (tar in rep and rule["repeat"] < 1)
Move compiling code to own functions

=== Features ===
Implement new featural notation
Implement $ and syllables
Implement cat subsets
Implement target reference

=== Style ===
Write docstrings
Raise Exceptions where necessary
"""

Cats = {}
Graphs = []
Sep = "'"

class SCEException(Exception):
    """Base class for exceptions in this module."""

class WordUnchanged(SCEException):
    """Used to indicate that the word was not changed by the rule."""

class FormatError(SCEException):
    """Exception raised for errors in formatting objects."""

class Cat():
    def __init__(self, vals, ftrs=None):
        _vals = []
        _ftrs = {}
        if isinstance(vals, str):
            vals = vals.replace(","," ").split()
        for val in vals:
            if "[" in val:
                val = val[1:-1]
                _vals += Cats[val].vals
            else:
                _vals += [val]
        if ftrs != None:
            for ftr,vals in ftrs.items():
                ftrs[ftr] = [val for val in Cat(vals) if val in self]
                if not ftrs[ftr] or ftrs[ftr] == _vals:
                    del ftrs[ftr]
            _ftrs = ftrs
        self.vals = _vals
        self.ftrs = _ftrs
    
    def __repr__(self):
        vals = repr(self.vals)
        if self.ftrs:
            ftrs = repr(self.ftrs)
            return "Cat({}, {})".format(vals, ftrs)
        else:
            return "Cat({})".format(vals)
    
    def __len__(self):
        return len(self.vals)
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.vals[key]
        else:
            return self.ftrs[key]
    
    def __setitem__(self, key, value):
        if isinstance(key, int):
            self.vals[key] = value
        else:
            self.ftrs[key] = [val for val in Cat(value) if val in self]
    
    def __delitem__(self, key):
        if isinstance(key, int):
            del self.vals[key]
        else:
            del self.ftrs[key]
    
    def __iter__(self):
        return iter(self.vals)
    
    def __contains__(self, item):
        return item in self.vals
    
    def __and__(self, cat):
        vals = [val for val in self if val in cat]
        ftrs = dict(**self.ftrs, **cat.ftrs)
        return Cat(vals, ftrs)
    
    def __add__(self, cat):
        vals = self.vals + cat.vals
        ftrs = dict(**self.ftrs, **cat.ftrs)
        return Cat(vals, ftrs)
    
    def __sub__(self, cat):
        vals = [val for val in self if val not in cat]
        return Cat(vals, self.ftrs)

class Rule():    
    def __init__(self, rule):
        self.rule = rule
        if " " in rule:
            rule, flag = rule.split()
        else:
            flag = ""
        if "!" in rule:
            rule, excs = rule.split("!")
        else:
            excs = ""
        if "/" in rule:
            rule, envs = rule.split("/")
        else:
            envs = "_"
        if rule.count("+") + rule.count("-") + rule.count(">") != 1:
            raise FormatError("there must be exactly one of '+', '-' and '>' in the rule")
        if "+" in rule:
            if rule.find("+"):
                raise FormatError("'+' must be at the beginning of the rule")
            else:
                tars, reps = "", rule[1:]
        if "-" in rule:
            if rule.find("-"):
                raise FormatError("'-' must be at the beginning of the rule")
            else:
                tars, reps = rule[1:], ""
        elif ">" in rule:
            tars, reps = rule.split(">")
            if not tars and not reps:
                raise FormatError("tars and reps may not both be empty")
            if "," in tars and "," not in reps:
                reps = ",".join([reps]*(tars.count(",")+1))
        self.tars = Rule.parseTars(tars)
        self.reps = Rule.parseReps(reps)
        self.envs = Rule.parseEnvs(envs)
        self.excs = Rule.parseEnvs(excs)
        self.flag = Rule.parseFlag(flag)
        if self.flag["ltr"]:
            self.reverse()
        return
    
    def __repr__(self):
        return "Rule({!s})".format(self)
    
    def __str__(self):
        return self.rule

    @staticmethod
    def parseSyms(syms):
        for lbr, rbr in zip("([{",")]}"):
            if syms.count(lbr) != syms.count(rbr):
                raise FormatError("unbalanced '{}{}'".format(lbr,rbr))
        for char in "()[]{}|#*_":
            syms = syms.replace(char, "."+char+".")
        syms = syms.replace(".", " ").split()
        ends = [[],[],[]]
        for i in reversed(range(len(syms))):
            if syms[i] in ")":
                ends[0].append(i)
            if syms[i] in "]":
                ends[1].append(i)
            if syms[i] in "}":
                ends[2].append(i)
            elif syms[i] == "(":
                if ends[0][-1] > ends[1][-1] or ends[0][-1] > ends[2][-1]:
                    raise FormatError("cannot interleave bracket types")
                end = ends[0].pop()
                syms[i:end+1] = tuple(syms[i+1:end])
            elif syms[i] == "[":
                if ends[1][-1] > ends[0][-1] or ends[1][-1] > ends[2][-1]:
                    raise FormatError("cannot interleave bracket types")
                end = ends[1].pop()
                if "|" in syms[i+1:end]:
                    temp = syms[i+1:end]
                    cat = []
                    while True:
                        index = temp.find("|")
                        if index == -1:
                            cat.append(temp)
                            del temp
                            break
                        else:
                            cat.append(temp[:index])
                            del temp[:index+1]
                    syms[i:end+1] = Cat(cat)
                elif ("+" in syms[i+1] or "-" in syms[i+1]) and end == i+2:
                    temp = syms[i+1]
                    temp = temp.replace("+"," +").replace("-"," -").split()
                    temp[0] = Cats[temp[0]]
                    while len(temp) != 1:
                        cat = temp[0]
                        op = temp[1][0]
                        ftr = temp[1][1:]
                        cat = cat & cat[ftr] if op == "+" else cat - cat[ftr]
                        temp[:2] = cat
                elif syms[i+1] in Cats and end == i+2:
                    syms[i:end+1] = Cats[syms[i+1]]
                else:
                    raise FormatError("mal-formatted category") # Improve message?
            elif syms[i] == "{": #unimplemented
                if ends[2][-1] > ends[0][-1] or ends[2][-1] > ends[1][-1]:
                    raise FormatError("cannot interleave bracket types")
                end = ends[2].pop()
                del syms[i:end+1]
        return syms
    
    @staticmethod
    def parseTars(tars):
        Tars = []
        for tar in tars.replace(",", " ").split():
            if "@" in tar:
                try:
                    tar, count = tar.replace("@", " ").split()
                except ValueError:
                    raise FormatError("there should only be one '@' per target")
                count = count.replace("|", " ").split()
            else:
                count = []
            tar = Rule.parseSyms(tar)
            Tars += [(tar,count)]
        return Tars

    @staticmethod
    def parseReps(reps):
        Reps = []
        for rep in reps.replace(",", " ").split():
            if "(" in rep or ")" in rep:
                raise FormatError("optional segments not allowed in rep")
            rep = Rule.parseSyms(rep)
            Reps += [rep]
        return Reps

    @staticmethod
    def parseEnvs(envs):
        Envs = []
        for env in envs.replace(",", " ").split():
            if "~" in env:
                Envs += Rule.parseEnvs(env[1:]+"_,_"+env[1:])
            else:
                if env.count("_") > 1:
                    raise FormatError("there should be no more than one '_' per env")
                env = Rule.parseSyms(env)
                if "_" not in env:
                    env = [env]
                else:
                    index = env.index("_")
                    if index == 0:
                        env = [[], env[1:]]
                    else:
                        env = [env[index-1::-1], env[index+1:]]
                Envs += [env]
        return Envs
    
    @staticmethod
    def parseFlag(flag):
        Flags = {"ltr":0, "repeat":1, "age":1}
        flags = flag.replace(",", " ").split()
        for flag in flags:
            if flag not in Flags:
                raise FormatError("'{}' is not a valid flag".format(flag))
            if ":" in flag:
                flag, arg = flag.split(":")
                Flags[flag] = arg
            else:
                Flags[flag] = 1-Flags[flag]
        return Flags
    
    def reverse(self):
        for i in range(len(self.tars)):
            self.tars[i].reverse()
        for i in range(len(self.reps)):
            self.reps[i].reverse()
        for i in range(len(self.envs)):
            self.envs[i].reverse()
            self.envs[i][0].reverse()
            self.envs[i][1].reverse()
        for i in range(len(self.excs)):
            self.excs[i].reverse()
            self.excs[i][0].reverse()
            self.excs[i][1].reverse()
    
class Word():
    def __init__(self, lex):
        if isinstance(lex, str):
            test = ""
            phones = []
            for char in "#"+lex.replace(" ","#")+"#"+Sep:
                test += char
                while len(test) > 1 and all(g.find(test) for g in Graphs):
                    for i in reversed(range(1,len(test)+1)):
                        if len(test[:i]) == 1 or test[:i] in Graphs:
                            phones += [test[:i]]
                            test = test[i:].lstrip(Sep)
                            break
            self.phones = phones
        else:
            for i in reversed(range(1,len(lex))):
                if lex[i] == lex[i-1] == "#":
                    del lex[i]
            self.phones = list(lex)
    
    def __repr__(self):
        return "Word('{!s}')".format(self)
    
    def __str__(self):
        word = curr = ""
        for graph in self.phones:
            curr += graph
            for poly in [g for g in Graphs if len(g) > 1]:
                if graph in poly and graph != poly:
                    break
            else:
                curr = ""
            for poly in [g for g in Graphs if len(g) > 1]:
                if curr in poly:
                    if curr == poly:
                        word += Sep
                        curr = graph
                    break
            else:
                curr = curr[1:]
            word += graph
        return word.strip(Sep+"#").replace("#"," ")
    
    def __eq__(self, other):
        return isinstance(other, Word) and self.phones == other.phones
    
    def __len__(self):
        return len(self.phones)
    
    def __getitem__(self, key):
        if isinstance(key, slice):
            return Word(self.phones[key])
        else:
            return self.phones[key]
    
    def __setitem__(self, key, value):
        self.phones[key] = value
    
    def __delitem__(self, key):
        del self.phones[key]
    
    def __iter__(self):
        return iter(self.phones)
    
    def __contains__(self, item):
        if isinstance(item, list):
            return self.find(item) != -1
        elif isinstance(item, Word):
            return self.find(item.phones) != -1
        else:
            return item in self.phones
    
    def __add__(self, other):
        return Word(self.phones + other.phones)
    
    def __mul__(self, other):
        return Word(self.phones * other)
    
    def __rmul__(self, other):
        return Word(self.phones * other)
    
    def reverse(self):
        self.phones.reverse()
    
    def find(self, sub, start=None, end=None):
        if start is not None or end is not None:
            return self[start:end].find(sub)
        i = 0 #Position in the word
        for j in range(len(sub)):
            sym = sub[j]
            if i >= len(self):
                return -1
            elif sym[0] == "(": #Optional; if this fails, try the next sym
                seg, sym = self[i], sym[1:-1]
                if not (seg in sym if isinstance(sym, Cat) else seg == sym):
                    i -= 1
            elif sym == "*": #Wildcard
                if self[i:].find(sub[j+1:]) == -1:
                    break
                else:
                    return 0
            else:
                seg = self[i]
                if not (seg in sym if isinstance(sym, Cat) else seg == sym):
                    break
            i += 1
        else:
            return 0
        pos = self[1:].find(sub)
        if pos == -1:
            return pos
        else:
            return pos+1
    
    def matchEnv(self, pos, len, env):
        if len(env) == 1:
            return env[0] in self
        elif len(env) == 2:
            if pos:
                matchLeft = self[::-1].find(env[0],-pos)
            else:
                matchLeft = -1 if env[0] else 0
            matchRight = self.find(env[1], pos+len)
            return matchLeft == matchRight == 0
    
    def matchTar(self, tar, rule):
        matches = []
        if tar:
            tar, count = tar
        else:
            tar, count = [], []
        index = 0
        while True:
            match = self.find(tar, index)
            if match == -1:
                break
            index += match
            matches.append(index)
            index += 1
        if not count:
            count = range(len(matches))
        envs, excs = rule.envs, rule.excs
        for match in sorted([matches[c] for c in count], reverse=True):
            for exc in excs:
                if self.matchEnv(match, len(tar), exc):
                    break
            else:
                for env in envs:
                    if self.matchEnv(match, len(tar), env):
                        yield match
                        break
    
    def replace(self, start, run, rep):
        self[start:start+run] = rep
        return
    
    def applyRule(self, rule):
        tars, reps = rule.tars, rule.reps
        phones = self.phones
        if rule.flag["ltr"]:
            self.reverse()
        if not tars: #Epenthesis
            matches = self.matchTar([], rule)
            _len = 0
            _rep = reps[0]
            for match in matches:
                self.replace(match, _len, _rep)
        elif not reps: #Deletion
            for tar in tars:
                matches = self.matchTar(tar, rule)
                _len = len(tar[0])
                _rep = []
                for match in matches:
                    self.replace(match, _len, _rep)
        else: #Substitution
            for tar, rep in zip(tars, reps):
                matches = self.matchTar(tar, rule)
                tar = tar[0]
                if isinstance(rep[0], Cat) and isinstance(tar[0], Cat):
                    tar, rep = tar[0], rep[0]
                    for match in matches:
                        index = tar.find(self[match])
                        _rep = [rep[index]]
                        self.replace(match, 1, _rep)
                else:
                    _len = len(tar)
                    if rep == ["?"]: #Metathesis
                        _rep = tar[::-1]
                    else:
                        _rep = rep
                    for match in matches:
                        self.replace(match, _len, _rep)
        if rule.flag["ltr"]:
            self.reverse()
        if self.phones == phones:
            raise WordUnchanged
        return

def run(iLex, strm):
    global Cats
    Words = [Word(lex) for lex in iLex]
    Rules = []
    for flow in strm:
        if flow == "":
            continue
        elif "=" in flow: #flow is a cat
            try:
                if flow.count("=") != 1:
                    raise FormatError("there should only be one '='")
                cop = flow.find("=")
                op = (flow[cop-1] if flow[cop-1] in "+-" else "") + "="
                name, vals = flow.split(op)
                lbr = name.find("[")
                rbr = name.find("]")
                if lbr == rbr == -1:
                    feature = None
                elif lbr < rbr-1 and name.count("[") == name.count("]") == 1:
                    name, feature = name.strip("]").split("[")
                else:
                    raise FormatError("features should be notated '[...]'")
                if op != "=" and name not in Cats:
                    raise FormatError("categories must exist to be modified")
                if feature:
                    exec("Cats[name][feature] {} Cat(vals)".format(op))
                else:
                    exec("Cats[name] {} Cat(vals)".format(op))
                for cat in Cats.keys():
                    if not Cats[cat]:
                        del Cats[cat]
            except FormatError as e:
                print("Error parsing cat '{}': {}".format(flow, e.args[0]))
        else: #flow is a rule
            try:
                rule = Rule(flow)
            except FormatError as e:
                print("Error parsing rule '{}': {}".format(flow, e.args[0]))
                continue
            Rules += [rule]
            print("Words =",[str(word) for word in Words])
            for Word in Words:
                for rule in Rules[::-1]:
                    print("rule =",rule)
                    repeat = rule.flag["repeat"]
                    while True:
                        try:
                            Word.applyRule(rule)
                        except WordUnchanged:
                            break
                        repeat -= 1
                        if not repeat:
                            break
            for i in reversed(range(len(Rules))):
                Rules[i].flag["age"] -= 1
                if Rules[i].flag["age"] == 0:
                    del Rules[i]
    return [str(word) for word in Words]
