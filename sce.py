"""Apply sound changes to a lexicon

Exceptions:
    WordUnchanged -- exception to break out of repeated rule application

Classes:
    Rule -- represents a sound change rule

Functions:
    parse_ruleset -- parses a sound change ruleset
    apply_rule    -- applies a sound change rule to a word
""""""
==================================== To-do ====================================
=== Bug-fixes ===

=== Implementation ===
Integrate core.Language
Check that tar still matches immediately before replacement (difficult)
Check if a rule is able to run infinitely and raise an exception if it can
- (tar in rep and rule["repeat"] < 1)
Move compiling code to own functions
Tidy up after moving Word() and Cat() to core.py
Remove formatting checks - this will all be done in the interface script

=== Features ===
Implement $ and syllables
Implement % for target reference
Implement " for copying previous segment

=== Style ===
Write docstrings
Raise Exceptions where necessary
"""

from core import LangException, Cat, parse_syms

class WordUnchanged(LangException):
    """Used to indicate that the word was not changed by the rule."""

class Rule():
    """Class for representing a sound change rule.
    
    Instance variables:
        rule -- the rule as a string (str)
        tars -- target segments (list)
        reps -- replacement segments (list)
        envs -- application environments (list)
        excs -- exception environments (list)
        flag -- flags for altering execution (dict)
    
    Methods:
        parse_tars -- parse the target field of a rule
        parse_reps -- parse the replacement field of a rule
        parse_envs -- parse the environment field of a rule
        parse_flag -- parse the flags of a rule
    """  
    def __init__(self, rule, cats): #format is tars>reps/envs!excs flag; envs, excs, and flag are all optional
        """
        
        Arguments:
            
        """
        self.rule = rule
        if " " in rule:
            rule, flag = rule.split(" ")
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
        if "+" in rule: #+reps/... is alias for >reps/...
            if rule[0] != "+":
                raise FormatError("'+' must be at the beginning of the rule")
            else:
                tars, reps = "", rule[1:]
        if "-" in rule: #-tars/... is alias for tars>/...
            if rule[0] != "-":
                raise FormatError("'-' must be at the beginning of the rule")
            else:
                tars, reps = rule[1:], ""
        elif ">" in rule:
            tars, reps = rule.split(">")
            if not tars and not reps:
                raise FormatError("tars and reps may not both be empty")
            if "," in tars and "," not in reps:
                reps = ",".join([reps]*(tars.count(",")+1))
        self.tars = Rule.parse_tars(tars, cats)
        self.reps = Rule.parse_reps(reps, cats)
        self.envs = Rule.parse_envs(envs, cats)
        self.excs = Rule.parse_envs(excs, cats)
        self.flag = Rule.parse_flag(flag)
        if self.flag["ltr"]:
            self.reverse()
        return
    
    def __repr__(self):
        return "Rule('{!s}')".format(self)
    
    def __str__(self):
        return self.rule
    
    @staticmethod
    def parse_tars(tars, cats):
        """
        
        Arguments:
            
        """
        _tars = []
        for tar in tars.replace(",", " ").split():
            if "@" in tar:
                try:
                    tar, count = tar.replace("@", " ").split()
                except ValueError:
                    raise FormatError("there should only be one '@' per target")
                count = count.replace("|", " ").split()
            else:
                count = []
            tar = parse_syms(tar, cats)
            _tars += [(tar,count)]
        return _tars

    @staticmethod
    def parse_reps(reps, cats):
        """
        
        Arguments:
            
        """
        _reps = []
        for rep in reps.replace(",", " ").split():
            if "(" in rep or ")" in rep:
                raise FormatError("optional segments not allowed in rep")
            rep = parse_syms(rep, cats)
            _reps += [rep]
        return _reps

    @staticmethod
    def parse_envs(envs, cats):
        """
        
        Arguments:
            
        """
        _envs = []
        for env in envs.replace(",", " ").split():
            if "~" in env: #~X is equivalent to X_,_X; add checks for bad formatting
                _envs += Rule.parse_envs(env[1:]+"_,_"+env[1:], cats)
            else:
                if env.count("_") > 1:
                    raise FormatError("there should be no more than one '_' per env")
                env = parse_syms(env, cats)
                if "_" in env:
                    index = env.index("_")
                    if index == 0:
                        env = [[], env[1:]]
                    else:
                        env = [env[index-1::-1], env[index+1:]]
                else:
                    env = [env]
                _envs.append(env)
        return _envs
    
    @staticmethod
    def parse_flag(flags):
        """
        
        Arguments:
            
        """
        _flags = {"ltr":0, "repeat":1, "age":1} #default values
        for flag in flags.replace(",", " ").split():
            if flag not in _flags:
                raise FormatError("'{}' is not a valid flag".format(flag))
            if ":" in flag:
                try:
                    flag, arg = flag.split(":")
                except ValueError:
                    raise FormatError("each flag may only be followed by one ':'")
                _flags[flag] = arg
            else:
                _flags[flag] = 1-_flags[flag]
        return _flags
    
    def reverse(self):
        for tar in self.tars:
            tar.reverse()
        for rep in self.reps:
            rep.reverse()
        for env in self.envs:
            env.reverse()
            env[0].reverse()
            if len(env) == 2:
                env[1].reverse()
        for exc in self.excs:
            exc.reverse()
            exc[0].reverse()
            if len(exc) == 2:
                exc[1].reverse()

def parse_ruleset(ruleset, cats):
    """Parse a sound change ruleset.
    
    Arguments:
        ruleset -- the set of rules to be parsed
        cats    -- the categories to be used to parse the rules
    
    Returns a list.
    """
    if isinstance(ruleset, str):
        ruleset = ruleset.splitlines()
    for i in range(len(ruleset)):
        rule = ruleset[i]
        if rule == "":
            ruleset[i] = None
        elif isinstance(rule, Rule):
            continue
        elif "=" in rule: #rule is a cat definition
            try:
                if rule.count("=") != 1: #tbr
                    raise FormatError("there should only be one '='")
                cop = rule.index("=")
                op = (rule[cop-1] if rule[cop-1] in "+-" else "") + "="
                name, vals = rule.split(op)
                if op != "=" and name not in cats: #tbr
                    raise FormatError("categories must exist to be modified")
                exec("cats[name] {} Cat(vals)".format(op))
                for cat in cats.keys(): #discard blank categories
                    if not cats[cat]:
                        del cats[cat]
                ruleset[i] = None
            except FormatError as e: #tbr
                print("Error parsing cat '{}': {}. Skipping.".format(rule, e.args[0]))
                ruleset[i] = None
        else: #rule is a sound change
            try:
                ruleset[i] = Rule(rule, cats)
            except FormatError as e:
                print("Error parsing rule '{}': {}. Skipping.".format(rule, e.args[0]))
                ruleset[i] = None
    for i in reversed(range(len(ruleset))):
        if ruleset[i] is None:
            del ruleset[i]
    return ruleset
    
def apply_rule(word, rule):
    """Apply a single sound change rule to a single word.
    
    Arguments:
        word -- the word to which the rule is to be applied (Word)
        rule -- the rule to be applied to the word (Rule)
    
    Returns a Word
    
    Raises WordUnchanged if the word was not changed by the rule.
    """
    tars, reps = rule.tars, rule.reps
    phones = word.phones
    if rule.flag["ltr"]:
        word.reverse()
    if not tars: #Epenthesis
        word.substitute(rule, ([],[]), reps[0])
    elif not reps: #Deletion
        for tar in tars:
            word.substitute(rule, tar, [])
    else: #Substitution
        for tar, rep in zip(tars, reps):
            if isinstance(rep[0], Cat) and isinstance(tar[0][0], Cat): #Cat substitution
                matches = word.match_tar(tar, rule)
                tar, rep = tar[0][0], rep[0]
                for match in matches:
                    index = tar.find(word[match])
                    _rep = [rep[index]]
                    word.replace(match, 1, _rep)
            else:
                if rep == ["?"]: #Metathesis
                    rep = tar[0][::-1]
                word.substitute(rule, tar, rep)
    if rule.flag["ltr"]:
        word.reverse()
    if word.phones == phones:
        raise WordUnchanged
    return word

