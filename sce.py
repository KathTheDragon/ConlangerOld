"""Apply sound changes to a lexicon

Exceptions:
    WordUnchanged -- exception to break out of repeated rule application

Classes:
    Rule -- represents a sound change rule

Functions:
    parse_ruleset -- parses a sound change ruleset
    apply_ruleset -- applies a set of sound change rules to a set of words
""""""
==================================== To-do ====================================
=== Bug-fixes ===

=== Implementation ===
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
Consider where to raise/handle exceptions
"""

from core import LangException, Cat, parse_syms

#== Exceptions ==#
class WordUnchanged(LangException):
    """Used to indicate that the word was not changed by the rule."""

#== Classes ==#
class Rule():
    """Class for representing a sound change rule.
    
    Instance variables:
        rule  -- the rule as a string (str)
        tars  -- target segments (list)
        reps  -- replacement segments (list)
        envs  -- application environments (list)
        excs  -- exception environments (list)
        flags -- flags for altering execution (dict)
    
    Methods:
        parse_field -- parse the fields of a rule
        parse_flags -- parse the flags of a rule
        apply       -- apply the rule to a word 
    """  
    def __init__(self, rule, cats): #format is tars>reps/envs!excs flag; envs, excs, and flag are all optional
        """
        
        Arguments:
            
        """
        self.rule = rule
        if ' ' not in rule:
            rule.append(' ')
        if '!' not in rule:
            rule.replace(' ', '! ')
        if '/' not in rule:
            rule.replace('!', '/_!')
        if '+' in rule:
            rule.replace('+', '>')
        if '-' in rule:
            rule.replace('-', '').replace('/', '>/')
        tars, reps, envs, excs, flags = rule.replace('>', ' ').replace('/', ' ').replace('!', ' ').split(' ')
        if "," in tars and "," not in reps:
            reps = ",".join([reps]*(tars.count(",")+1))
        self.tars = Rule.parse_field(tars, 'tars', cats)
        self.reps = Rule.parse_field(reps, 'reps', cats)
        self.envs = Rule.parse_field(envs, 'envs', cats)
        self.excs = Rule.parse_field(excs, 'envs', cats)
        self.flags = Rule.parse_flags(flags)
        if self.flags["ltr"]:
            self.reverse()
        return
    
    def __repr__(self):
        return "Rule('{!s}')".format(self)
    
    def __str__(self):
        return self.rule
    
    @staticmethod
    def parse_field(field, mode, cats):
        """
        
        Arguments:
        
        """
        _field = []
        if mode == 'envs':
            for env in field.split(','):
                if "~" in env: #~X is equivalent to X_,_X
                    _field += Rule.parse_field(env[1:]+'_,_'+env[1:], 'envs', cats)
                else:
                    if '_' in env:
                        env = env.split('_')
                        env = [parse_syms(env[0], cats)[::-1], parse_syms(env[1], cats)]
                    else:
                        env = [parse_syms(env, cats)]
                    _field.append(env)
        else:
            for tar in field.split(','):
                if mode == 'tars':
                    if '@' in tar:
                        tar, count = tar.split('@')
                        count = count.split('|')
                    else:
                        count = []
                tar = parse_syms(tar, cats)
                if mode == 'tars':
                    tar = (tar, count)
                _field.append(tar)
        return _field
    
    @staticmethod
    def parse_flags(flags):
        """
        
        Arguments:
            
        """
        _flags = {"ltr":0, "repeat":1, "age":1} #default values
        for flag in flags.replace(",", " ").split():
            if ":" in flag:
                flag, arg = flag.split(":")
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
    
    def apply(self, word):
        """Apply a single sound change rule to a single word.
        
        Arguments:
            word -- the word to which the rule is to be applied (Word)
        
        Returns a Word
        
        Raises WordUnchanged if the word was not changed by the rule.
        """
        tars, reps = self.tars, self.reps
        phones = word.phones
        if self.flags["ltr"]:
            word.reverse()
        if not tars: #Epenthesis
            word.substitute(self, ([],[]), reps[0])
        elif not reps: #Deletion
            for tar in tars:
                word.substitute(self, tar, [])
        else: #Substitution
            for tar, rep in zip(tars, reps):
                if isinstance(rep[0], Cat) and isinstance(tar[0][0], Cat): #Cat substitution
                    matches = word.match_tar(tar, self)
                    tar, rep = tar[0][0], rep[0]
                    for match in matches:
                        index = tar.find(word[match])
                        _rep = [rep[index]]
                        word.replace(match, 1, _rep)
                else:
                    if rep == ["?"]: #Metathesis
                        rep = tar[0][::-1]
                    word.substitute(self, tar, rep)
        if self.flags["ltr"]:
            word.reverse()
        if word.phones == phones:
            raise WordUnchanged
        return word


#== Functions ==#
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

def apply_ruleset(words, ruleset):
    """Applies a set of sound change rules to a set of words.
    
    Arguments:
        words   -- the words to which the rules are to be applied (list)
        ruleset -- the rules which are to be applied to the words (list)
    
    Returns a list.
    """
    ruleset = parse_ruleset(ruleset)
    rules = [] #we use a list to store rules, since they may be applied multiple times
    for rule in ruleset:
        rules.append(rule)
        print("Words =",[str(word) for word in words]) #for debugging
        for i in range(len(words)):
            for rule in reversed(rules):
                print("rule =",rule) #for debugging
                for j in range(rule.flags["repeat"]):
                    try:
                        words[i] = rule.apply(words[i])
                    except WordUnchanged: #if the word didn't change, stop applying
                        break
        for i in reversed(range(len(rules))):
            rules[i].flags["age"] -= 1
            if rules[i].flags["age"] == 0: #if the rule has 'expired', discard it
                del rules[i]
    return words

