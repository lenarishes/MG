'''
Created on Feb 20, 2013

@author: courtesy of Piter Norvig
'''

import re, collections
from nltk.corpus import brown

class SpellChecker():
    def __init__(self):
        #holds a count of how many times the word w has been seen
        self.nwords = self.train([w.lower() for w in brown.words()])
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz'
    
    def train(self, features):
        # +1 smoothing for the unseen words
        model = collections.defaultdict(lambda: 1)
        for f in features:
            model[f] += 1
        return model

    # corrections at the edit1 from the input
    # For a word of length n, there will be n deletions, n-1 transpositions, 
    # 26n alterations, and 26(n+1) insertions, for a total of 54n+25 
    # (of which a few are typically duplicates).
    def edits1(self, word):
       splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
       deletes    = [a + b[1:] for a, b in splits if b]
       transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
       replaces   = [a + c + b[1:] for a, b in splits for c in self.alphabet if b]
       inserts    = [a + c + b     for a, b in splits for c in self.alphabet]
       return set(deletes + transposes + replaces + inserts)

    # edit over an edit
    def known_edits2(self, word):
        return set(e2 for e1 in self.edits1(word) for e2 in self.edits1(e1) if e2 in self.nwords)

    def known(self, words): return set(w for w in words if w in self.nwords)

    # The function correct chooses as the set of candidate words the set with the shortest edit distance 
    # to the original word, as long as the set has some known words. 
    # Once it identifies the candidate set to consider, it chooses the element 
    # with the highest P(c) value, as estimated by the NWORDS model.
    # This is an simplifying assumption here : build no model of spelling errors. 
    def correct(self, word):
        if word.isupper():
            return word
        candidates = self.known([word]) or self.known(self.edits1(word)) or self.known_edits2(word) or [word]
        return max(candidates, key=self.nwords.get)
