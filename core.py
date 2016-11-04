"""Base classes and functions

Exceptions:
    LangException -- Base exception
    FormatError   -- Error for incorrect formatting

Classes:
    Cat    -- represents a category of phonemes
    Word   -- represents a run of text
    Config -- collection of gen.py configuration data

Functions:
    parseSyms    -- parses a string of symbols
""""""
==================================== To-do ====================================
=== Bug-fixes ===
Word.find is not aware that optional segments are now in tuples (not urgent)

=== Implementation ===
Utilise new implementation of Word as sequence type
- investigate reindexing Word

=== Features ===
Implement cat subsets

=== Style ===
Write docstrings
Raise Exceptions where necessary
"""

from collections import namedtuple

#== Exceptions ==#
class LangException(Exception):
    """Base class for exceptions in this package"""

class FormatError(LangException):
    """Exception raised for errors in formatting objects."""

#== Classes ==#
class Cat():
    """Represents a category of graphemes.
    
    Instance variables:
        vals -- the values in the category (list)
    """
    
    def __init__(self, vals):
        """Constructor for Cat.
        
        Arguments:
            vals -- the values in the category (str, list)
        """
        _vals = []
        if isinstance(vals, str): #we want an iteratible with each value as an element
            vals = vals.replace(","," ").split()
        for val in vals:
            if isinstance(val, Cat): #another category
                _vals.extend(val.vals)
            else:
                _vals.append(val)
        self.vals = _vals
    
    def __repr__(self):
        return "Cat({})".format(repr(self.vals))
    
    def __bool__(self):
        return bool(self.vals)
    
    def __len__(self):
        return len(self.vals)
    
    def __getitem__(self, key):
        return self.vals[key]
    
    def __setitem__(self, key, value):
        self.vals[key] = value
    
    def __delitem__(self, key):
        del self.vals[key]
    
    def __iter__(self):
        return iter(self.vals)
    
    def __contains__(self, item):
        return item in self.vals
    
    def __and__(self, cat):
        vals = [val for val in self if val in cat]
        return Cat(vals)
    
    def __add__(self, cat):
        vals = self.vals + cat.vals
        return Cat(vals)
    
    def __sub__(self, cat):
        vals = [val for val in self if val not in cat]
        return Cat(vals)

class Word():
    """
    
    Instance variables:
    
    
    Methods:
    
    """
    def __init__(self, lex=None, syllables=None, graphs=None):
        """
        
        Arguments:
            
        """
        if graphs is None:
            self.sep = "'"
            self.graphs = []
        else:
            self.sep = graphs[0]
            self.graphs = graphs[1:]
        if lex is None:
            self.phones = []
        elif isinstance(lex, str):
            test = ""
            phones = []
            for char in "#"+lex.replace(" ","#")+"#"+self.sep: #flank the word with '#' to indicate the edges
                test += char
                while len(test) > 1 and all(g.find(test) for g in self.graphs):
                    for i in reversed(range(1,len(test)+1)):
                        if len(test[:i]) == 1 or test[:i] in self.graphs:
                            phones += [test[:i]]
                            test = test[i:].lstrip(self.sep)
                            break
            self.phones = phones
        else:
            for i in reversed(range(1,len(lex))): #clean up multiple consecutive '#'s
                if lex[i] == lex[i-1] == "#":
                    del lex[i]
            self.phones = list(lex)
        self.syllables = syllables #do a bit of sanity checking here
    
    def __repr__(self):
        return "Word('{!s}')".format(self)
    
    def __str__(self):
        word = curr = ""
        for graph in self.phones:
            curr += graph
            for poly in [g for g in self.graphs if len(g) > 1]:
                if graph in poly and graph != poly:
                    break
            else:
                curr = ""
            for poly in [g for g in self.graphs if len(g) > 1]:
                if curr in poly:
                    if curr == poly:
                        word += self.sep
                        curr = graph
                    break
            else:
                curr = curr[1:]
            word += graph
        return word.strip(self.sep+"#").replace("#"," ")
    
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
    
    def copy(self):
        return Word(self.phones, self.lang, self.syllables)
    
    def reverse(self):
        self.phones.reverse()
    
    def find(self, sub, start=None, end=None):
        """
        
        Arguments:
            
        """
        if not (start is None and end is None):
            return self[start:end].find(sub)
        i = 0 #position in the word
        for j, sym in enumerate(sub):
            if i >= len(self):
                return -1 #we've run out of word, so this fails
            elif sym[0] == "(": #optional; this needs to changed, as optionals are tuples
                seg, sym = self[i], sym[1:-1]
                if not (seg in sym if isinstance(sym, Cat) else seg == sym):
                    i -= 1 #if this fails, we jump back to where we were
            elif sym == "*": #wildcard
                if self.find(sub[j+1:],i) == -1:
                    break #only fails if the rest of the sequence is nowhere present
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
    
    def matchEnv(self, env, pos=0, run=0): #test if the env matches the word at index pos
        """
        
        Arguments:
            
        """
        if len(env) == 1:
            return env[0] in self
        elif len(env) == 2:
            if pos:
                matchLeft = self[::-1].find(env[0],-pos)
            else: #at the left edge, which can only be matched by a null env
                matchLeft = -1 if env[0] else 0
            matchRight = self.find(env[1], pos+run)
            return matchLeft == matchRight == 0
    
    def matchTar(self, tar, rule): #get all places where tar matches against self
        """
        
        Arguments:
            
        """
        matches = []
        if tar:
            tar, count = tar
        else:
            tar, count = [], []
        index = 0
        while True:
            match = self.find(tar, index) #find the next place where tar matches
            if match == -1: #no more matches
                break
            index += match
            matches.append(index)
            index += 1
        if not count:
            count = range(len(matches))
        envs, excs = rule.envs, rule.excs
        for match in sorted([matches[c] for c in count], reverse=True):
            for exc in excs: #don't keep this match if any exception matches
                if self.matchEnv(exc, match, len(tar)):
                    break
            else:
                for env in envs: #keep this match if any environment matches
                    if self.matchEnv(env, match, len(tar)):
                        yield match
                        break
    
    def replace(self, start, run, rep):
        self[start:start+run] = rep
        return

Config = namedtuple('Config', 'patterns, counts, constraints, freq, monofreq')

#== Functions ==#
def parseSyms(syms, cats):
    """
    
    Arguments:
        
    """
    for lbr, rbr in zip("([{",")]}"): #check for unbalanced brackets
        if syms.count(lbr) != syms.count(rbr):
            raise FormatError("unbalanced '{}{}'".format(lbr,rbr))
    for char in "()[]{}|#*_":
        syms = syms.replace(char, "."+char+".")
    syms = syms.replace(".", " ").split()
    ends = []
    for i in reversed(range(len(syms))): #process brackets
        if syms[i] in ")]}":
            ends.append(i)
        elif syms[i] == "(":
            if syms[ends[-1]] != ")":
                raise FormatError("cannot interleave bracket types")
            end = ends.pop()
            syms[i:end+1] = tuple(syms[i+1:end])
        elif syms[i] == "[":
            if syms[ends[-1]] != "]":
                raise FormatError("cannot interleave bracket types")
            end = ends.pop()
            if "|" in syms[i+1:end]: #nonce category
                temp = syms[i+1:end]
                cat = []
                while True: #the list is partitioned by "|"
                    if "|" in temp:
                        index = temp.index("|")
                        if index == 1:
                            seg = temp[0]
                            if seg in cats:
                                seg = cats[seg]
                            cat.append(seg)
                        else:
                            cat.extend(temp[:index]) #as it stands, this can't deal with sequences
                        del temp[:index+1]
                    else:
                        if len(temp) == 1:
                            seg = temp[0]
                            if seg in cats:
                                seg = cats[seg]
                            cat.append(seg)
                        else:
                            cat.extend(temp)
                        del temp
                        break
                syms[i:end+1] = [Cat(cat)]
            elif syms[i+1] in cats and end == i+2: #named category
                syms[i:end+1] = [cats[syms[i+1]]]
            else:
                raise FormatError("mal-formatted category") # Improve message?
        elif syms[i] == "{": #unimplemented
            if syms[ends[-1]] != "}":
                raise FormatError("cannot interleave bracket types")
            end = ends.pop()
            del syms[i:end+1]
    return syms

