# -*- coding: utf-8 -*-
"""
Obtains a 2-d vector for each record in the CSV export from GrantNav
(grantnav.threesixtygiving.org).
"""
from collections import Counter
from math import log
from re import findall
from sklearn.decomposition import TruncatedSVD
from sklearn.manifold import TSNE
from sklearn.preprocessing import Imputer
from sklearn.preprocessing import scale
import gensim
import numpy as np
import pandas as pd

# TODO: Retain common phrases, e.g. 'Los Angeles', like the word2vec model.
def string_to_words(string):
    """Splits text into lowercase words, removing characters other than
    apostrophes, hyphens and the Latin alphabet.

        Parameters:
        -----------
        A string of text.

        Returns:
        --------
        A list that holds the words.
     
    """
    return findall(r"[A-z'-]+", string.lower())

def term_doc_freq(corpus):
    """Counts the number of documents in a corpus in which each word in the
    corpus appears.

        Parameters:
        -----------
        A list (corpus) of lists (documents) of strings (words).

        Returns:
        --------
        A Counter object (dict) that maps a word to the number of documents in
        which it appears.

    """
    return Counter(word for document in corpus for word in set(string_to_words(document)))

def term_freq_funding_org(dataframe):
    """Counts the total number of documents .

        Parameters:
        -----------
        A DataFrame object that includes the columns 'Funding Org:Identifier'
        and 'text'.

        Returns:
        --------
        A dict that maps a Funding Org to a dict that holds the total number
        of grants with that Funding Org and a dict that maps a word to the
        number of grants with that Funding Org in which it appears.

    """
    aggregation = {
        'text': {
            'term_freq': term_doc_freq,
            'total': 'count'
        }
    }
    grouped = dataframe.groupby('Funding Org:Identifier').agg(aggregation)
    grouped.columns = grouped.columns.droplevel(level=0)
    
    return grouped.to_dict('index')

if __name__ == '__main__':
    # Create DataFrame from CSV
    csv = 'grantnav-all.csv'
    dataframe = pd.read_csv(csv, dtype={
        'Identifier': str,
        'Title': str,
        'Description': str,
        'Currency': str,
        'Amount Applied For': float,
        'Amount Awarded': float,
        'Amount Disbursed': float,
        'Award Date': str,
        'URL': str,
        'Planned Dates:Start Date': str,
        'Planned Dates:End Date': str,
        'Planned Dates:Duration (months)': float,
        'Actual Dates:Start Date': str,
        'Actual Dates:End Date': str,
        'Actual Dates:Duration (months)': float,
        'Recipient Org:Identifier': str,
        'Recipient Org:Name': str,
        'Recipient Org:Charity Number': str,
        'Recipient Org:Company Number': str,
        'Recipient Org:Postal Code': str,
        'Recipient Org:Location:0:Geographic Code Type': str,
        'Recipient Org:Location:0:Geographic Code': str,
        'Recipient Org:Location:0:Name': str,
        'Recipient Org:Location:1:Geographic Code Type': str,
        'Recipient Org:Location:1:Geographic Code': str,
        'Recipient Org:Location:1:Name': str,
        'Recipient Org:Location:2:Geographic Code Type': str,
        'Recipient Org:Location:2:Geographic Code': str,
        'Recipient Org:Location:2:Name': str,
        'Funding Org:Identifier': str,
        'Funding Org:Name': str,
        'Funding Org:Postal Code': str,
        'Grant Programme:Code': str,
        'Grant Programme:Title': str,
        'Grant Programme:URL': str,
        'Beneficiary Location:0:Name': str,
        'Beneficiary Location:0:Country Code': str,
        'Beneficiary Location:0:Geographic Code': str,
        'Beneficiary Location:0:Geographic Code Type': str,
        'Beneficiary Location:1:Name': str,
        'Beneficiary Location:1:Country Code': str,
        'Beneficiary Location:1:Geographic Code': str,
        'Beneficiary Location:1:Geographic Code Type': str,
        'Beneficiary Location:2:Name': str,
        'Beneficiary Location:2:Country Code': str,
        'Beneficiary Location:2:Geographic Code': str,
        'Beneficiary Location:2:Geographic Code Type': str,
        'Beneficiary Location:3:Name': str,
        'Beneficiary Location:3:Country Code': str,
        'Beneficiary Location:3:Geographic Code': str,
        'Beneficiary Location:3:Geographic Code Type': str,
        'Beneficiary Location:4:Name': str,
        'Beneficiary Location:4:Country Code': str,
        'Beneficiary Location:4:Geographic Code': str,
        'Beneficiary Location:4:Geographic Code Type': str,
        'Beneficiary Location:5:Name': str,
        'Beneficiary Location:5:Country Code': str,
        'Beneficiary Location:5:Geographic Code': str,
        'Beneficiary Location:5:Geographic Code Type': str,
        'Beneficiary Location:6:Name': str,
        'Beneficiary Location:6:Country Code': str,
        'Beneficiary Location:6:Geographic Code': str,
        'Beneficiary Location:6:Geographic Code Type': str,
        'Beneficiary Location:7:Name': str,
        'Beneficiary Location:7:Country Code': str,
        'Beneficiary Location:7:Geographic Code': str,
        'Beneficiary Location:7:Geographic Code Type': str,
        'From An Open Call?': str,
        'The following fields are not in the 360 Giving Standard and are added by GrantNav.': str,
        'Data Source': str,
        'Publisher:Name': str,
        'Recipient Region': str,
        'Recipient District': str,
        'Recipient District Geographic Code': str,
        'Recipient Ward': str,
        'Recipient Ward Geographic Code': str,
        'Retrieved for use in GrantNav': str,
        'License (see note)': str,
        'Note, this file also contains OS data © Crown copyright and database right 2016, Royal Mail data © Royal Mail copyright and Database right 2016, National Statistics data © Crown copyright and database right 2015 & 2016, see http://grantnav.threesixtygiving.org/datasets/ for more information.': str
    })

    # Retain columns of interest
    dataframe = dataframe[[
        'Identifier',
        'Award Date',
        'Title',
        'Description',
        'Currency',
        'Amount Awarded',
        'Recipient Org:Identifier',
        'Recipient Org:Name',
        'Funding Org:Identifier',
        'Funding Org:Name'
    ]]

    # Get inverse document frequencies among grants with same funding org
    dataframe['text'] = dataframe['Title'].map(str) + ' ' + dataframe['Description'].map(str) + ' ' + dataframe['Recipient Org:Name'].map(str)
    funding_org_freq = term_freq_funding_org(dataframe)

    # Loads 300-d word vectors as a KeyedVectors instance
    model = gensim.models.KeyedVectors.load_word2vec_format('./GoogleNews-vectors-negative300.bin', binary=True)

    # Create a list of lists that holds the weighted word embeddings for each record
    vectors = [
        [
            model[word] * log(funding_org_freq[record['Funding Org:Identifier']]['total'] / funding_org_freq[record['Funding Org:Identifier']]['term_freq'][word])
            for word in string_to_words(record['text']) if word in model
        ]
        for record in dataframe.to_dict('records')
    ]

    # Average to give a single 300-d vector for each record
    vectors = [np.mean(vector, axis=0) if vector else np.zeros_like(model['empty']) for vector in vectors]

    # Replace NaN values to prevent ValueError
    X = Imputer(missing_values='NaN', strategy='mean', axis=0, verbose=1).fit_transform(vectors)

    # Scale to zero mean and unit variance
    X_scaled = scale(X, axis=0)
    print(X_scaled)

    # Reduce number of features
    X_reduced = TruncatedSVD(n_components=50, random_state=0).fit_transform(X_scaled)
    print(X_reduced)

    # Obtain 2-d vectors by t-SNE
    X_embedded = TSNE(verbose=1).fit_transform(X_reduced)
    print(X_embedded)

    # Append to DataFrame and save to CSV
    dataframe['x'] = X_embedded[:,0]
    dataframe['y'] = X_embedded[:,1]
    print(dataframe.head())
    dataframe.to_csv('result.csv')
