Metadata Games (metadatagames.dartmouth.edu/mg/www/) is an open source software platform designed to provide archivists with an easy-to-use and efficient interface to generate and share image metadata.

This project aims to extend the back-end Metadata Games logic with Natural Language Processing and Machine Learning techniques for tag verification.

Files:
confidence.py contains feature engineering function prototypes
Exampe usage: computeScoresFromDB('localhost', 'root', '', 'db_MG', 'out.csv')

spell_check.py implements a spelling correction algo (courtesy of Piter Norvig)
Example usage: SC = SpellChecker() # class initialization
for w in list_of_words:
	corrected = SC.correct(w)
	print "%s was corrected to %s" % (w, corrected)

tweet_data_tags.csv is a sample inpt for confidence.computeScoresFromCSV('tweet_data_tags.csv', 'out.csv')