"""Apply sound changes to a lexicon

Exceptions:
    WordUnchanged -- exception to break out of repeated rule application

Classes:
    Rule -- represents a sound change rule

Functions:
    parseRuleset -- parses a sound change ruleset
    applyRule    -- applies a sound change rule to a word
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

from core import *

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
        parseTars -- parse the target field of a rule
        parseReps -- parse the replacement field of a rule
        parseEnvs -- parse the environment field of a rule
        parseFlag -- parse the flags of a rule
    """  
    def __init__(self, rule, cats): #format is tars>reps/envs!excs flag; envs, excs, and flag are all optional
        """
        
        Arguments:
            
        """
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
        self.tars = Rule.parseTars(tars, cats)
        self.reps = Rule.parseReps(reps, cats)
        self.envs = Rule.parseEnvs(envs, cats)
        self.excs = Rule.parseEnvs(excs, cats)
        self.flag = Rule.parseFlag(flag)
        if self.flag["ltr"]:
            self.reverse()
        return
    
    def __repr__(self):
        return "Rule('{!s}')".format(self)
    
    def __str__(self):
        return self.rule
    
    @staticmethod
    def parseTars(tars, cats):
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
            tar = parseSyms(tar, cats)
            _tars += [(tar,count)]
        return _tars

    @staticmethod
    def parseReps(reps, cats):
        """
        
        Arguments:
            
        """
        _reps = []
        for rep in reps.replace(",", " ").split():
            if "(" in rep or ")" in rep:
                raise FormatError("optional segments not allowed in rep")
            rep = parseSyms(rep, cats)
            _reps += [rep]
        return _reps

    @staticmethod
    def parseEnvs(envs, cats):
        """
        
        Arguments:
            
        """
        _envs = []
        for env in envs.replace(",", " ").split():
            if "~" in env: #~X is equivalent to X_,_X; add checks for bad formatting
                _envs += Rule.parseEnvs(env[1:]+"_,_"+env[1:], cats)
            else:
                if env.count("_") > 1:
                    raise FormatError("there should be no more than one '_' per env")
                env = parseSyms(env, cats)
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
    def parseFlag(flags):
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

def parseRuleset(ruleset, cats):
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
    
def applyRule(word, rule):
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
        matches = word.matchTar([], rule)
        _run = 0
        _rep = reps[0]
        for match in matches:
            word.replace(match, _run, _rep)
    elif not reps: #Deletion
        for tar in tars:
            matches = word.matchTar(tar, rule)
            _run = len(tar[0])
            _rep = []
            for match in matches:
                word.replace(match, _run, _rep)
    else: #Substitution
        for tar, rep in zip(tars, reps):
            matches = word.matchTar(tar, rule)
            tar = tar[0]
            if isinstance(rep[0], Cat) and isinstance(tar[0], Cat):
                tar, rep = tar[0], rep[0]
                for match in matches:
                    index = tar.find(word[match])
                    _rep = [rep[index]]
                    word.replace(match, 1, _rep)
            else:
                _run = len(tar)
                if rep == ["?"]: #Metathesis
                    _rep = tar[::-1]
                else:
                    _rep = rep
                for match in matches:
                    word.replace(match, _run, _rep)
    if rule.flag["ltr"]:
        word.reverse()
    if word.phones == phones:
        raise WordUnchanged
    return word

