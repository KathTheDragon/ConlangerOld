"""Base classes and functions

Exceptions:
    LangException -- Base exception
    FormatError   -- Error for incorrect formatting

Classes:
    Cat    -- represents a category of phonemes
    Word   -- represents a run of text
    Config -- collection of gen.py configuration data

Functions:
    parse_syms    -- parses a string of symbols
""""""
==================================== To-do ====================================
=== Bug-fixes ===
Word.find is not aware that optional segments are now in tuples (not urgent)

=== Implementation ===
Utilise new implementation of Word as sequence type
- investigate reindexing Word
Break out format checking into separate functions

=== Features ===
Implement cat subsets

=== Style ===
Write docstrings
Consider where to raise/handle exceptions
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
        values -- the values in the category (list)
    """
    
    def __init__(self, values):
        """Constructor for Cat.
        
        Arguments:
            values -- the values in the category (str, list)
        """
        _values = []
        if isinstance(values, str): #we want an iteratible with each value as an element
            values = values.replace(","," ").split()
        for value in values:
            if isinstance(value, Cat): #another category
                _values.extend(value.values)
            else:
                _values.append(value)
        self.values = _values
    
    def __repr__(self):
        return "Cat({})".format(repr(self.values))
    
    def __bool__(self):
        return bool(self.values)
    
    def __len__(self):
        return len(self.values)
    
    def __getitem__(self, key):
        return self.values[key]
    
    def __setitem__(self, key, value):
        self.values[key] = value
    
    def __delitem__(self, key):
        del self.values[key]
    
    def __iter__(self):
        return iter(self.values)
    
    def __contains__(self, item):
        return item in self.values
    
    def __and__(self, cat):
        values = [value for value in self if value in cat]
        return Cat(values)
    
    def __add__(self, cat):
        values = self.values + cat.values
        return Cat(values)
    
    def __sub__(self, cat):
        values = [value for value in self if value not in cat]
        return Cat(values)

class Word():
    """
    
    Instance variables:
    
    
    Methods:
    
    """
    def __init__(self, lexeme=None, syllables=None, graphs=None):
        """
        
        Arguments:
            
        """
        if graphs is None:
            graphs = ["'"]
        self.sep = graphs[0]
        self.polygraphs = [g for g in graphs if len(g)>1]
        if lexeme is None:
            self.phones = []
        elif isinstance(lexeme, str): #black magic
            test = ""
            phones = []
            for char in "#"+lexeme.replace(" ","#")+"#"+self.sep: #flank the word with '#' to indicate the edges
                test += char
                while len(test) > 1 and not(any(g.startswith(test) for g in self.polygraphs)): #test isn't a single character and doesn't begin any polygraph
                    for i in reversed(range(1,len(test)+1)): #from i=len(test) to i=1
                        if i == 1 or test[:i] in self.polygraphs: #does test begin with a valid graph? Single characters are always valid
                            phones += [test[:i]]
                            test = test[i:].lstrip(self.sep)
                            break
            self.phones = phones
        else:
            self.phones = list(lexeme)
        for i in reversed(range(1,len(self.phones))): #clean up multiple consecutive '#'s
            if self.phones[i] == self.phones[i-1] == "#":
                del self.phones[i]
        self.syllables = syllables #do a bit of sanity checking here
    
    def __repr__(self):
        return "Word('{!s}')".format(self)
    
    def __str__(self):
        word = curr = ""
        for graph in self.phones:
            curr += graph
            for poly in self.polygraphs:
                if graph in poly and graph != poly:
                    break
            else:
                curr = ""
            for poly in self.polygraphs:
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
    
    def match_env(self, env, pos=0, run=0): #test if the env matches the word at index pos
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
    
    def match_tar(self, tar, rule): #get all places where tar matches against self
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
                if self.match_env(exc, match, len(tar)):
                    break
            else:
                for env in envs: #keep this match if any environment matches
                    if self.match_env(env, match, len(tar)):
                        yield match
                        break
    
    def substitute(self, rule, tar, rep):
        matches = self.match_tar(tar, rule)
        run = len(tar[0])
        for match in matches:
            self[match:match+run] = rep
    
    def replace(self, start, run, rep):
        self[start:start+run] = rep
        return

Config = namedtuple('Config', 'patterns, counts, constraints, freq, monofreq')

#== Functions ==#
def parse_syms(syms, cats):
    """
    
    Arguments:
        
    """
    for lbr, rbr in zip("([{",")]}"): #check for unbalanced brackets
        if syms.count(lbr) != syms.count(rbr):
            raise FormatError("unbalanced '{}{}'".format(lbr,rbr))
    for char in "()[]{}|#*_":
        syms = syms.replace(char, "."+char+".")
    syms = syms.replace(".", " ").split()
    ends = [] #store indices of close-brackets here
    for i in reversed(range(len(syms))): #process brackets
        if syms[i] in ")]}":
            ends.append(i)
        elif syms[i] == "(": #optional segment - to tuple
            if syms[ends[-1]] != ")":
                raise FormatError("cannot interleave bracket types")
            end = ends.pop()
            syms[i:end+1] = tuple(syms[i+1:end])
        elif syms[i] == "[": #category - to list and then Cat
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
        elif syms[i] == "{": #subset - unimplemented, delete contents
            if syms[ends[-1]] != "}":
                raise FormatError("cannot interleave bracket types")
            end = ends.pop()
            del syms[i:end+1]
    return syms

