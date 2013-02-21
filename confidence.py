'''
Created on Feb 4, 2013

@author: elenarishes
'''
import nltk
from nltk.corpus import wordnet as wn
from spell_check import SpellChecker
#from nltk.corpus import wordnet_ic
import re
import csv
import itertools
from collections import defaultdict
import MySQLdb as mdb
import sys

def fuzzyMatch(tag1, tag2):
    """
    Looks for the overlap between two tags
    @param tag1: string
    @param tag2: string
    @return int score of tag overlap
    """
    # for each n-gram length contains a list of overlaps found 
    matchCounter = defaultdict(list)
    # can add a stopword list here
    # to make tags like 'church bell' and 'church with a bell' count as a full match
    #stopwords = open(stopfile).read().split(',')
    
    # stemming
    tag1 = [nltk.PorterStemmer().stem(w) for w in tag1.split()]
    tag2 = [nltk.PorterStemmer().stem(w) for w in tag2.split()]  
    # pick a shorter tag
    if len(tag1) > len(tag2):
        tag = tag2
        str = ' '.join(tag1) 
    else: 
        tag = tag1
        str = ' '.join(tag2)
    # try matching n-grams of various length     
    for nwords in range(1, len(tag) + 1):
        substr = [" ".join(tag[i:i+nwords]) for i in range(len(tag) - nwords + 1)]
        matchCounter[nwords] = [s for s in substr if re.search(r"\b"+s+r"\b", str)]
    # compute total score of a tag-pair based on the matches found
    score = 0
    for k,v in matchCounter.items():
        score+=k*len(v)
    return score

def getMatchingScores(tags, image = ""):
    """
    For each tag in the image tag set computes a score based on the number of partial matches with other tags from the tag set
    @param tags: list of strings
    @param image: optional image name
    @return: dict {tag -> score}
    """
    confidence = defaultdict(int)
    match = defaultdict(list)
    n = len(tags)
    for i in range(n-1):
        for j in range(i+1, n):
            score = fuzzyMatch(tags[i], tags[j])
            confidence[tags[i]]+=score
            confidence[tags[j]]+=score
            if score:
                match[tags[i]].append(tags[j])
                match[tags[j]].append(tags[i])
    #for debugging
    if False:
        print "Image %s :" % image
        for k,v in confidence.items():
            if v:
                print "Tag '%s' matched '%s' and scored %d" % (k,"', '".join(match[k]), v)
        print "--------------"
    return confidence

def ontologyDist(w1, w2):
    """
    Computes similarity score between two words based on WordNet distance metrics: 
    path_similarity: shortest path that connects the senses in the hypernym taxonomy
    lch_similarity: takes tree depth into account
    lin_similarity: based on Probability of Least common subsummer, need to specify corpus for prob counts, brown_ic = wordnet_ic.ic('ic-brown.dat')
    """
    simscores = map(lambda x: x[0].lch_similarity(x[1]), 
                    itertools.product(wn.synsets(w1, pos = 'n'), 
                                      wn.synsets(w2, pos = 'n'))
                    )
    return max(simscores) if simscores else None

def getNouns(tag):
    """
    Returns the head of the noun phrase
    naive version: returns a single word or a second word in 2-word phrase 
    if it's noun (= 'NN' | 'NNS' in Penn tagset)
    Ex: white [background]
    need to elaborate by writing a grammar to parse NP (NP -> N Conj N; NP -> NP PP etc)
    """
    tag = nltk.pos_tag(tag.split())
    #print tag
    if len(tag) == 1 and tag[0][1] in 'NNS':return tag[0][0]
    elif len(tag) == 2 and tag[1][1] in 'NNS': return tag[1][0]
    else: return None
    
def getOntologyScores(tags, image = ""):
    """
    For each tag in the image tag set computes a sum of similarity scores with other tags from the tag set
    @param tags: list of strings
    @param image: optional image name
    @return: dict {tag -> score}
    """
    confidence = defaultdict(float)
    pairs = defaultdict(float)
    n = len(tags)
    for i in range(n-1):
        for j in range(i+1, n):
            hw1 = getNouns(tags[i])
            hw2 = getNouns(tags[j])
            #print hw1, hw2
            if not hw1 or not hw2: continue
            score = ontologyDist(hw1, hw2)
            # nltk uses Stanford tagger, often wrong, especially without context 
            if not score: continue
            pairs[(tags[i], tags[j])] = score
            confidence[tags[i]]+= score
            confidence[tags[j]]+= score
    
    return confidence

def examineScores(tag, tags):
    """
    This function is for debugging: why tag got high/low ontology score
    """
    hw = getNouns(tag)
    print 'Head word of '+ tag + ' is ' + hw
    print 'WordNet definitions of', hw
    for synset in wn.synsets(hw):
        print synset.definition
        
    pairs = defaultdict(float)
    for j in range(len(tags)):
        hw2 = getNouns(tags[j])
        if not hw2: continue
        score = ontologyDist(hw, hw2)
        # nltk uses Stanford tagger, often wrong, especially without context 
        if not score: continue
        pairs[tags[j]] = score
        
    for k,v in pairs.items():
        print "Print tag '%s' is %.2f" % (k, v)
        

def computeScoresFromCSV(inp_name, out_name):
    """
    Takes csv file from DB export (Image Name Tags)
    For each image-tag application computes confidence scores (fuzzy match and ontology similarity)
    Writes output into a file
    Ex:  computeScores("tweet_data_tags.csv","out.csv")
    @param inp_name: csv file 
    @param out_name: output file name 
    """
    SC = SpellChecker()
    with open(out_name, 'w') as out:
        outcsv = csv.writer(out, delimiter = ' ')
        outcsv.writerow(['Tag', 'WordNet Similarity', 'Fuzzy_match'])
        cr = csv.reader(open(inp_name, 'r'), delimiter='\t')
        for row in cr:
            if row[0].startswith('#') or row[0] == "Image Name":
                continue
            im_name = row[0]
            outcsv.writerow(['Image '+im_name+':'])
            # Spelling correction
            tags = [SC.correct(w.strip("'")) for w in row[1].split(', ')]
            fuzzy_scores = getMatchingScores(tags)
            # before computing ontology scores, remove duplicate tags (might appear after spelling correction)
            tags = list(set(tags))
            sim_scores = getOntologyScores(tags)
            for k, v in sorted([(i, sim_scores[i]) for i in tags], key = lambda x: x[1], reverse= True):
                outcsv.writerow([k, v, fuzzy_scores[k]])
            outcsv.writerow([])

def computeScoresFromDB(host, user, passwd, db_name, out_name):
    """
    Connects to the MSQL server and queries the metadata games database
    For each image-tag application computes confidence scores (weight, fuzzy match and ontology similarity)
    Writes output into a file
    Ex:  computeScores("tweet_data_tags.csv","out.csv")
    @param db_name: string 
    @param out_name: string 
    """
    SC = SpellChecker()
    weights = defaultdict(int)
    try:
        con = mdb.connect(host, user, passwd, db_name);
        cur = con.cursor()
        # get all images from image table
        cur.execute("SELECT id, name FROM image")
        images = cur.fetchall()
        with open(out_name, 'w') as out:
            outcsv = csv.writer(out, delimiter = ' ')
            outcsv.writerow(['Tag', 'WordNet Similarity', 'Fuzzy_match', 'Weight'])
           
           #select tags with weights for current image
            for i in images:
                cur.execute("SELECT tag.tag, SUM(tag_use.weight) FROM tag_use LEFT JOIN tag ON tag_use.tag_id = tag.id WHERE tag_use.image_id =" 
                        + str(i[0]) +" GROUP BY tag.tag")
                rows = cur.fetchall()
                weights.update(itertools.chain(rows))
                # Spelling correction
                tags = [SC.correct(t) for t in weights.keys()]
                im_name = i[1]
                outcsv.writerow(['Image '+im_name+':'])
                fuzzy_scores = getMatchingScores(tags)
                # before computing ontology scores, remove duplicate tags (might appear after spelling correction)
                tags = list(set(tags))
                sim_scores = getOntologyScores(tags)
                for k, v in sorted([(i, sim_scores[i]) for i in tags], key = lambda x: x[1], reverse= True):
                    outcsv.writerow([k, v, fuzzy_scores[k], weights[k]])
                outcsv.writerow([])
                weights.clear()
    
    except mdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])
        sys.exit(1)
    #close connection
    finally:    
        if con:    
            con.close()


    
