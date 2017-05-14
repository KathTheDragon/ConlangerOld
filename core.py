'''Base classes and functions

Exceptions:
    LangException -- Base exception
    FormatError   -- Error for incorrect formatting

Classes:
    Cat    -- represents a category of phonemes
    Word   -- represents a run of text
    Config -- collection of gen.py configuration data

Functions:
    parse_syms -- parses a string using pattern notation
    nest_split -- splits a string while aware of nesting
''''''
==================================== To-do ====================================
=== Bug-fixes ===

=== Implementation ===
Utilise new implementation of Word as sequence type
- investigate reindexing Word
Break out format checking into separate functions
I want to change supplying the actual syllable boundaries to Word to giving a syllabifier function - this is obviously language-dependent
Perhaps adjust Cat.__init__ to allow sequences of graphemes to be stored

=== Features ===
Implement cat subsets - maybe?
Perhaps write another splitting function to replace the .replace(char, ' ').split() almalgam

=== Style ===
Consider where to raise/handle exceptions
'''

from collections import namedtuple

#== Exceptions ==#
class LangException(Exception):
    '''Base class for exceptions in this package'''

class FormatError(LangException):
    '''Exception raised for errors in formatting objects.'''

#== Classes ==#
class Cat(list):
    '''Represents a category of graphemes.
    
    Instance variables:
        values -- the values in the category (list)
    '''
    
    def __init__(self, values=None, cats=None):
        '''Constructor for Cat.
        
        Arguments:
            values -- the values in the category (str, list)
            cats   -- dictionary of categories (dict)
        '''
        _values = []
        if values is None:
            values = []
        elif isinstance(values, str): #we want an iteratible with each value as an element
            values = values.replace(',',' ').split()
        for value in values:
            if isinstance(value, Cat): #another category
                _values.extend(value.values)
            elif '[' in value:
                if cats is not None and value.strip('[]') in cats:
                    _values.extend(cats[value.strip('[]')])
                else:
                    continue
            else:
                _values.append(value)
        list.__init__(self, _values)
    
    def __repr__(self):
        return f"Cat('{self!s}')"
    
    def __str__(self):
        return ', '.join(self)
    
    def __and__(self, cat):
        values = [value for value in self if value in cat]
        return Cat(values)
    
    def __sub__(self, cat):
        values = [value for value in self if value not in cat]
        return Cat(values)

class Word():
    '''Represents a word as a list of graphemes.
    
    Instance variables:
        sep        -- a character used to disambiguate polygraphs from sequences (chr)
        polygraphs -- a list of multi-letter graphemes (list)
        phones     -- a list of the graphemes in the word (list)
        syllables  -- a list of tuples representing syllables (list)
    
    Methods:
        find      -- match a list using pattern notation to the word
        match_env -- match a sound change environment to the word
    '''
    def __init__(self, lexeme=None, syllables=None, graphs=None):
        '''Constructor for Word
        
        Arguments:
            lexeme    -- the word (str)
            syllables -- list of tuples representing syllables (list)
            graphs    -- list of graphemes (list)
        '''
        if graphs is None:
            graphs = ["'"]
        self.sep = graphs[0]
        self.polygraphs = [g for g in graphs if len(g)>1]
        if lexeme is None:
            self.phones = []
        elif isinstance(lexeme, list):
            self.phones = lexeme
        else:
            self.phones = parse_word(f' {lexeme} ', self.sep, self.polygraphs)
        self.syllables = syllables #do a bit of sanity checking here
    
    def __repr__(self):
        return f"Word('{self!s}')"
    
    def __str__(self):
        word = curr = ''
        for graph in self.phones:
            curr += graph
            for poly in self.polygraphs:
                if graph in poly and graph != poly:
                    break
            else:
                curr = ''
            for poly in self.polygraphs:
                if curr in poly:
                    if curr == poly:
                        word += self.sep
                        curr = graph
                    break
            else:
                curr = curr[1:]
            word += graph
        return word.strip(self.sep+'#').replace('#',' ')
    
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
    
    def find(self, sub, start=None, end=None, return_match=False):
        '''Match a sequence using pattern notation to the word.
        
        Arguments:
            sub   -- the list to be found (list)
            start -- the index of the beginning of the range to check (int)
            end   -- the index of the end of the range to check (int)
        
        Returns an int
        '''
        if start is None:
            start = 0
        elif start < 0:
            start += len(self)
        if end is None:
            end = len(self)
        elif end < 0:
            end += len(self)
        if isinstance(sub, Word):
            sub = sub[1:-1] #we want to strip out the leading and trailing '#'s so that this works like finding substrings
        #shitty implementation for return_match for now, at some point this will be redone
        if not return_match:
            for i in range(0, end-start):
                j = i + start #position in the word
                for k, sym in enumerate(sub):
                    if j >= end: #we've reached the end of the slice, so the find fails
                        return -1
                    elif isinstance(sym, tuple): #optional sequence
                        if self.find(list(sym)+sub[k+1:], j, end) == 0: #try with the optional sequence
                            return i
                        else: #if this fails, we jump back to where we were
                            j -= 1
                    elif isinstance(sym, Cat): #category
                        if not self[j] in sym: #this may change - definitely if categories are allowed to contain sequences
                            break
                    elif sym == '*': #wildcard
                        if self.find(sub[k+1:],j, end) != -1: #only fails if the rest of the sequence is nowhere present
                            return i
                        else:
                            break
                    else:
                        if self[j] != sym:
                            break
                    j += 1
                else:
                    return i
            else:
                return -1
        else:
            for i in range(0, end-start):
                j = i + start #position in the word
                for k, sym in enumerate(sub):
                    if j >= end: #we've reached the end of the slice, so the find fails
                        return -1, []
                    elif isinstance(sym, tuple): #optional sequence
                        index, match = self.find(list(sym)+sub[k+1:], j, end, return_match)
                        if index == 0: #try with the optional sequence
                            return i, self[i+start:j]+match
                        else: #if this fails, we jump back to where we were
                            j -= 1
                    elif isinstance(sym, Cat): #category
                        if not self[j] in sym: #this may change - definitely if categories are allowed to contain sequences
                            break
                    elif sym == '*': #wildcard
                        index, match = self.find(sub[k+1:],j, end, return_match)
                        if index != -1: #only fails if the rest of the sequence is nowhere present
                            return i, self[i+start:index+j]+match
                        else:
                            break
                    else:
                        if self[j] != sym:
                            break
                    j += 1
                else:
                    return i, self[i+start:j]
            else:
                return -1, []
    
    def match_env(self, env, pos=0, tar=None): #test if the env matches the word
        '''Match a sound change environment to the word.
        
        Arguments:
            env -- the environment to be matched (list)
            pos -- the index of the left edge of the target (int)
            tar -- the target (list)
        
        Returns a bool
        '''
        if tar is None:
            tar = []
        for i in reversed(range(len(env))):
            if env[i] == '%':
                env[i:i+1] = tar
            if env[i] == '<':
                env[i:i+1] = reversed(tar)
        if len(env) == 1:
            return env[0] in self
        else:
            if pos:
                matchLeft = self[::-1].find(env[0],-pos)
            else: #at the left edge, which can only be matched by a null env
                matchLeft = -1 if env[0] else 0
            matchRight = self.find(env[1], pos+len(tar))
            return matchLeft == matchRight == 0
    
    def replace(self, start, tar, rep):
        for i in reversed(range(len(rep))):
            if rep[i] == '%': #target copying
                rep[i:i+1] = tar
            elif rep[i] == '<': #target reversal/metathesis
                rep[i:i+1] = reversed(tar)
        self[start:start+len(tar)] = rep
        return

Config = namedtuple('Config', 'patterns, counts, constraints, freq, monofreq')

#== Functions ==#
def parse_syms(syms, cats=None):
    '''Parse a string using pattern notation.
    
    Arguments:
        syms -- the input string using pattern notation (str)
        cats -- a list of cats to use for interpreting categories (list)
    
    Returns a list
    '''
    if cats is None:
        cats = {}
    for char in '([{}])':
        syms.replace(char, f' {char} ')
    syms = nest_split(syms, ' ', ('([{','}])'), 0)
    for i in reversed(range(len(syms))):
        syms[i] = syms[i].replace(' ','')
        if syms[i][0] == '(': #optional - parse to tuple
            syms[i] = tuple(parse_syms(syms[i].strip('()'), cats))
        elif syms[i][0] == '[': #category - parse to Cat
            syms[i] = syms[i].strip('[]')
            if ',' in syms[i]: #nonce cat
                syms[i] = Cat(syms[i])
            else: #named cat
                syms[i] = cats[syms[i]]
        elif syms[i][0] == '{': #subset - unimplemented, delete
            del syms[i]
        else: #text - parse as word
            syms[i:i+1] = parse_word(syms[i])
    return syms

def parse_word(word, sep="'", polygraphs=[]):
    '''Parse a string of graphemes.
    
    Arguments:
        word       -- the word to be parsed (str)
        sep        -- disambiguator character (str)
        polygraphs -- list of polygraphs (list)
    
    Returns a list.
    '''
    #black magic
    test = ''
    graphemes = []
    for char in '#'.join(f'.{word}.'.split()).strip('.')+sep: #convert all whitespace to a single #
        test += char
        while len(test) > 1 and not any(g.startswith(test) for g in polygraphs): #while test isn't a single character and doesn't begin any polygraph
            for i in reversed(range(1,len(test)+1)): #from i=len(test) to i=1
                if i == 1 or test[:i] in polygraphs: #does test begin with a valid graph? Single characters are always valid
                    graphemes.append(test[:i]) #add this valid graph to the output
                    test = test[i:].lstrip(sep) #remove the graph from test, and remove leading instances of sep
                    break
    return graphemes

#this could potentially be changed at some point
def nest_split(string, sep, nests, level):
    '''Nesting-aware string splitting.
    
    Arguments:
        string -- the string to be split (str)
        sep    -- the separator character(s) (str)
        nests  -- a tuple of the form (open, close) containing opening and closing nesting characters (tuple)
        level  -- the nesting level at which splitting should take place (int)
    
    Returns a list.
    '''
    depth = 0
    for i in range(len(string)):
        if string[i] in sep and depth == level:
            string = string[:i] + ' ' + string[i+1:]
        if string[i] in nests[0]:
            depth += 1
        if string[i] in nests[1]:
            depth -= 1
    return string.split(' ')

