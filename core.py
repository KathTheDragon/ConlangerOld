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
Look into revising the parsing of nonce categories

=== Features ===
Implement cat subsets

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
class Cat():
    '''Represents a category of graphemes.
    
    Instance variables:
        values -- the values in the category (list)
    '''
    
    def __init__(self, values):
        '''Constructor for Cat.
        
        Arguments:
            values -- the values in the category (str, list)
        '''
        _values = []
        if isinstance(values, str): #we want an iteratible with each value as an element
            values = values.replace(',',' ').split()
        for value in values:
            if isinstance(value, Cat): #another category
                _values.extend(value.values)
            else:
                _values.append(value)
        self.values = _values
    
    def __repr__(self):
        return 'Cat({})'.format(repr(self.values))
    
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
        else:
            self.phones = parse_word(' {} '.format(lexeme), self.sep, self.polygraphs)
        self.syllables = syllables #do a bit of sanity checking here
    
    def __repr__(self):
        return "Word('{!s}')".format(self)
    
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
    
    def find(self, sub, start=None, end=None):
        '''Match a list using pattern notation to the word.
        
        Arguments:
            sub   -- the list to be found (list)
            start -- the index of the beginning of the range to check (int)
            end   -- the index of the end of the range to check (int)
        
        Returns an int
        '''
        if not (start is None and end is None): #this sucks and should be changed
            return self[start:end].find(sub)
        i = 0 #position in the word
        for j, sym in enumerate(sub):
            if i >= len(self):
                return -1 #we've run out of word, so this fails
            elif isinstance(sym, tuple): #optional sequence; this isn't actually fixed yet
                seg = self[i]
                if not (seg in sym if isinstance(sym, Cat) else seg == sym):
                    i -= 1 #if this fails, we jump back to where we were
            elif sym == '*': #wildcard
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
        '''Match a sound change environment to the word.
        
        Arguments:
            env -- the environment to be matched (list)
            pos -- the index of the left edge of the target (int)
            run -- the length of the target (int)
        
        Returns a bool
        '''
        if len(env) == 1:
            return env[0] in self
        elif len(env) == 2:
            if pos:
                matchLeft = self[::-1].find(env[0],-pos)
            else: #at the left edge, which can only be matched by a null env
                matchLeft = -1 if env[0] else 0
            matchRight = self.find(env[1], pos+run)
            return matchLeft == matchRight == 0
    
    def replace(self, start, run, rep):
        self[start:start+run] = rep
        return

Config = namedtuple('Config', 'patterns, counts, constraints, freq, monofreq')

#== Functions ==#
def parse_syms(syms, cats):
    '''Parse a string using pattern notation.
    
    Arguments:
        syms -- the input string using pattern notation (str)
        cats -- a list of cats to use for interpreting categories (list)
    
    Returns a list
    '''
    for char in '()[]{},#*_':
        syms = syms.replace(char, '.'+char+'.')
    syms = syms.replace('.', ' ').split()
    ends = [] #store indices of close-brackets here
    for i in reversed(range(len(syms))): #process brackets
        if syms[i] in ')]}':
            ends.append(i)
        elif syms[i] == '(': #optional segment - to tuple
            end = ends.pop()
            syms[i:end+1] = tuple(syms[i+1:end])
        elif syms[i] == '[': #category - to list and then Cat
            end = ends.pop()
            if ',' in syms[i+1:end]: #nonce category
                temp = syms[i+1:end]
                cat = []
                while True: #the list is partitioned by ','
                    index = temp.find(',')
                    if index != -1:
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
        elif syms[i] == '{': #subset - unimplemented, delete contents
            end = ends.pop()
            del syms[i:end+1]
    return syms

def parse_word(word, sep, polygraphs):
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
    for char in '#'.join('.{}.'.format(word).split()).strip('.')+sep: #convert all whitespace to a single #
        test += char
        while len(test) > 1 and not any(g.startswith(test) for g in polygraphs): #while test isn't a single character and doesn't begin any polygraph
            for i in reversed(range(1,len(test)+1)): #from i=len(test) to i=1
                if i == 1 or test[:i] in polygraphs: #does test begin with a valid graph? Single characters are always valid
                    graphemes.append(test[:i]) #add this valid graph to the output
                    test = test[i:].lstrip(sep) #remove the graph from test, and remove leading instances of sep
                    break
    return graphemes

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

