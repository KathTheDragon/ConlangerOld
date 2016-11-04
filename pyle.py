"""Create and manipulate languages

Classes:
    Language -- represents a language
""""""
==================================== To-do ====================================
=== Bug-fixes ===

=== Implementation ===

=== Features ===
Add saving/loading Languages to/from file
Add generating every possible word/root

=== Style ===
Raise Exceptions where necessary (done?)

"""

from core import *
import gen
import sce

# Naswiyan
# cats = 'T=t,d,þ,n|C=c,z,s|Č=č,ž,š|Ć=ć,ź,ś|K=k,g,h,ŋ|Q=q,ġ,ḫ|G=ʔ,ḥ|D=d,z,ž,ź,g,ġ|N=m,n,ŋ|R=r,l|A=n,þ,w,ḥ,r,ŋ,h,y,m,š,t,ś,ʔ,s,d,k,ḫ,č,l,g,ć,ž,c,ź,q,z,ġ|V=a,i,u,ə,e,o'
# sylPatterns = ''
# wordConstraints = ''
# rootPatterns = '[A]'
# rootConstraints = '[T][T],[C][C],[Č|Ć][Č|Ć],[Ć|K|Q][Ć|K|Q],[Q|G][Q|G],[D][D],[N][N],[R][R],y.y,w.w'
# wordConfig = None
# rootConfig = Config(rootPatterns, range(2,6), rootConstraints, 0.5, 0.3)
# patternFreq = 0.6
# graphFreq = 0.125
# lang = Language('Naswiyan', cats, wordConfig, rootConfig, patternFreq, graphFreq)

class Language():
    """Class for representing a single language.
    
    Instance variables:
        name        -- language name (str)
        cats        -- grapheme categories (dict)
        wordConfig  -- word configuration data (Config)
        rootConfig  -- root configuration data (Config)
        patternFreq -- drop-off frequency for patterns (float)
        graphFreq   -- drop-off frequency for graphemes (float)
    
    Methods:
        parsePatterns -- parse a string denoting generation patterns
        genWord       -- generate words
        genRoot       -- generate roots
        applyRules    -- apply sound changes
    """
    
    def __init__(self, name='', cats=None, wordConfig=None, rootConfig=None, patternFreq=0, graphFreq=0):
        """Constructor for Language().
        
        Arguments:
            name        -- language name (str)
            cats        -- grapheme categories (str, list or dict)
            wordConfig  -- word configuration data (str, Config)
            rootConfig  -- root configuration data (str, Config)
            patternFreq -- drop-off frequency for patterns (str, float)
            graphFreq   -- drop-off frequency for graphemes (str, float)
        
        Raises TypeError on invalid argument types.
        """
        if isinstance(name, str):
            self.name = name
        else:
            raise TypeError("argument 'name' requires str")
        if isinstance(cats, str):
            cats = cats.replace('|',' ').split()
        elif cats is None:
            cats = {}
        if isinstance(cats, list):
            self.cats = {}
            for cat in cats:
                name, vals = cat.split('=')
                vals = vals.replace(',',' ').split()
                if not vals: #this would yeild an empty cat
                    continue
                for i in range(len(vals)):
                    if '[' in vals[i]: #this is another category
                        vals[i] = self.cats[vals[i][1:-1]]
                self.cats[name] = Cat(vals)
        elif isinstance(cats, dict):
            for name in cats.keys():
                if not isinstance(cats[name], Cat):
                    if isinstance(cats[name], str):
                        cats[name] = cats[name].replace(',',' ').split()
                    if not vals: #this would yeild an empty cat
                        continue
                    for i in range(len(vals)):
                        if '[' in vals[i]: #this is another category
                            vals[i] = self.cats[vals[i][1:-1]]
                    self.cats[name] = vals
                if not cats[cat]: #this cat is empty
                    del cats[cat]
            self.cats = cats
        else:
            raise TypeError("argument 'cats' requires str, list or dict")
        if 'graphs' not in self.cats:
            self.cats['graphs'] = Cat("'")
        for cat in self.cats.keys(): #discard blank categories
            if not self.cats[cat]:
                del self.cats[cat]
        if isinstance(wordConfig, str):
            wordConfig = eval(wordConfig) #improve
        elif isinstance(wordConfig, Config):
            patterns, constraints = wordConfig.patterns, wordConfig.constraints
            if isinstance(patterns, str):
                patterns = self.parsePatterns(wordConfig.patterns)
            if isinstance(constraints, str):
                constraints = self.parsePatterns(wordConfig.constraints)
            self.wordConfig = Config(patterns, wordConfig.counts, contraints, wordConfig.freq, wordConfig.monofreq)
        elif wordConfig is None:
            self.wordConfig = Config([],range(0),[],0,0)
        else:
            raise TypeError("argument 'wordConfig' requires Config")
        if isinstance(rootConfig, str):
            rootConfig = eval(rootConfig) #improve
        elif isinstance(rootConfig, Config):
            patterns, constraints = rootConfig.patterns, rootConfig.constraints
            if isinstance(patterns, str):
                patterns = self.parsePatterns(rootConfig.patterns)
            if isinstance(constraints, str):
                constraints = self.parsePatterns(rootConfig.constraints)
            self.rootConfig = Config(patterns, rootConfig.counts, constraints, rootConfig.freq, rootConfig.monofreq)
        elif rootConfig is None:
            self.rootConfig = Config([],range(0),[],0,0)
        else:
            raise TypeError("argument 'rootConfig' requires Config")
        if isinstance(patternFreq, float):
            self.patternFreq = patternFreq
        elif isinstance(patternFreq, str):
            self.patternFreq = float(patternFreq)
        else:
            raise TypeError("argument 'patternFreq' requires str or float")
        if isinstance(graphFreq, float):
            self.graphFreq = graphFreq
        elif isinstance(graphFreq, str):
            self.graphFreq = float(graphFreq)
        else:
            raise TypeError("argument 'graphFreq' requires str or float")
    
    def parsePatterns(self, patterns):
        """Parses generation patterns.
        
        Arguments:
            patterns -- set of patterns to parse (str or list)
        
        Returns a list
        
        Raises TypeError on invalid argument types"""
        if isinstance(patterns, str):
            patterns = patterns.replace(",", " ").split()
        if isinstance(patterns, list):
            for i in range(len(patterns)):
                if isinstance(patterns[i], str):
                    patterns[i] = parseSyms(patterns[i], self.cats)
        else:
            raise TypeError("requires str or list")
        return patterns
    
    def genWord(self, num):
        """Generates 'num' words.
        
        Arguments:
            num -- number of words to generate, 0 generates every possible word (int)
        
        Returns a list
        
        Raises TypeError on invalid argument types
        """
        if num == 0: #generate every possible word, unimplemented
            pass
        elif isinstance(num, int):
            results = []
            for i in range(num):
                results.append(gen.genWord(self))
            return results
        else:
            raise TypeError("requires int")
    
    def genRoot(self, num):
        """Generates 'num' roots.
        
        Arguments:
            num -- number of roots to generate, 0 generates every possible root (int)
        
        Returns a list
        
        Raises TypeError on invalid argument types
        """
        if num == 0: #generate every possible word, unimplemented
            pass
        elif isinstance(num, int):
            results = []
            for i in range(num):
                results.append(gen.genRoot(self))
            return results
        else:
            raise TypeError("requires int")
    
    @staticmethod
    def applyRules(words, ruleset):
        """Applies a set of sound change rules to a set of words.
        
        Arguments:
            words   -- the words to which the rules are to be applied (list)
            ruleset -- the rules which are to be applied to the words (list)
        
        Returns a list.
        """
        ruleset = sce.parseRuleset(ruleset)
        rules = [] #we use a list to store rules, since they may be applied multiple times
        for rule in ruleset:
            rules.append(rule)
            print("Words =",[str(word) for word in words]) #for debugging
            for i in range(len(words)):
                for rule in reversed(rules):
                    print("rule =",rule) #for debugging
                    for j in range(rule.flag["repeat"]):
                        try:
                            words[i] = sce.applyRule(words[i], rule)
                        except WordUnchanged: #if the word didn't change, stop applying
                            break
            for i in reversed(range(len(rules))):
                rules[i].flag["age"] -= 1
                if rules[i].flag["age"] == 0: #if the rule has 'expired', discard it
                    del rules[i]
        return words

def loadLang(name): #do something with the path
    with open('langs/{}.dat'.format(name), 'r') as f:
        data = list(f)
    name = data[0]
    cats = data[1]
    wordConfig = data[2]
    rootConfig = data[3]
    patternFreq = data[4]
    graphFreq = data[5]
    return Language(name, cats, wordConfig, rootConfig, patternFreq, graphFreq)

def saveLang(lang, filename):
    pass

