import json 
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt

"""
This script calculates statistics about the timemap JSON files collected from the extracted URIs.
"""

def extract_uri_number(filename):
    """
    Fetches file number for one JSON timemap file.

    Argument(s):
    - filename: String representing filename.

    Output:
    Returns integer representing file number of given filename.
    """
    return int(os.path.basename(filename).split('uri')[1].split('.')[0])

def load_json(file):
    """
    Loads in each timemap JSON file according to its object type.

    Argument(s):
    - file: String representing filename.

    Output:
    Returns content stored in given file.
    """
    if hasattr(file, 'read'):
        uri_info = json.load(file)
    else:
        file_content = file.read()
        uri_info = json.loads(file_content)
    return uri_info

def get_memento_counts():
    """
    Collects the number of mementos for every timemap file stored in the 'timemaps' folder. 

    Output:
    Returns a list of integers representing the memento counts.
    """
    # Fetch all files stored in 'timemaps' directory
    tm_files = sorted(glob.glob(os.path.join('timemaps', 'uri*.json')), key=extract_uri_number)
    memento_counts = []
    for i, tm_file in enumerate(tm_files):
        try:
            with open(tm_file, "r") as file:
                uri_info = load_json(file)
                # Fetch the number of mementos collected for a URI
                if 'mementos' in uri_info:
                    memento_counts.append(len(uri_info['mementos']['list']))
                else:
                    memento_counts.append(0)
        # Error handling
        except Exception as e:
            print(f"Error processing {tm_file}: {e}")
    return memento_counts

def get_age(earliest_memento):
    """
    Reformats earliest memento date, calculates the age of each URI, and returns URI age in days.

    Argument(s):
    - earliest_memento: String representing time the earliest memento was captured.

    Output:
    Integer representing age of URI in days.
    """
    date_format = "%Y-%m-%dT%H:%M:%SZ" 
    # Convert to a datetime object
    date_object = dt.strptime(earliest_memento, date_format)
    # Calculate URI age in days
    age = (dt.now()-date_object).days
    return age

def get_uri_ages():
    """
    Fetches the age of each URI with > 0 mementos stored in the 'timemaps' folder.

    Output:
    - Returns a list of integers representing the ages of URIs. If a URI has 0 mementos, it is represented as None. 
    - Returns a list of strings representing the earilest mementos for each URI.
    """
    # 
    tm_files = sorted(glob.glob(os.path.join('timemaps', 'uri*.json')), key=extract_uri_number)
    uri_ages = []
    earliest_mementos = []
    for tm_file in tm_files:
        try:
            with open(tm_file, "r") as file:
                uri_info = load_json(file)
                if 'mementos' not in uri_info:
                    uri_ages.append(None)
                    earliest_mementos.append(None)
                else:
                    earliest_memento = uri_info['mementos']['first']['datetime']
                    earliest_mementos.append(earliest_memento)
                    uri_age = get_age(earliest_memento)
                    uri_ages.append(uri_age)
        except:
            print(tm_file)
    return uri_ages, earliest_mementos

def get_links_list():
    """
    Generates a list of the links stored in tweet_links.txt.

    Output:
    Returns a list of strings representing links in tweet_links.txt.
    """
    with open('tweet_links.txt', 'r') as file:
        links = file.read().splitlines()
    return links

def get_oldest_memento():
    """
    Calculates the oldest URI and the date of its first memento.

    Output:
    Returns string representing oldest URI and string representing date of the URI's first memento.
    """
    uri_ages, earliest_mementos = get_uri_ages()
    uris = get_links_list()
    uri_dates = []
    for uri, em in zip(uris, earliest_mementos):
        if em is None:
            continue
        date_format = "%Y-%m-%dT%H:%M:%SZ" 
        # Convert to a datetime object
        date_object = dt.strptime(em, date_format)
        # Calculate URI age in days
        uri_dates.append((uri, date_object))

    sorted_uri_dates = sorted(uri_dates, key=lambda x: x[1])

    # Format final date
    final_date = sorted_uri_dates[0][1].strftime("%B %d, %Y")

    return sorted_uri_dates[0][0], final_date

def get_distribution_table():
    """
    Get a distribution table of the number of mementos and number of URIs.

    Output:
    Returns a dataframe representing the distribution table of the number of mementos and number of URIs.
    """
    memento_counts = get_memento_counts()
    # Define the ranges
    ranges = [0, 1, 11, 21, 101, 1001, 10000000]
    range_labels = ['0', '1-10', '11-20', '21-100', '101-1000','1001+']

    # Split the memento counts into categories and fetch the counts for each category
    memento_categories = pd.cut(memento_counts, bins=ranges, labels=range_labels, right=False, include_lowest=True)
    memento_table_values = pd.Series(memento_categories).value_counts(sort=False)
    # Create a DataFrame to represent the table
    df = pd.DataFrame({
        'Memento Count': memento_table_values.index,
        '# of URIs': memento_table_values.values
    })
    return df

def summary_statistics():
    """
    Calculates summary statistics for the collected time maps and URIs. 

    Output:
    Prints the percentage of URIs in the dataset that have been archived, the oldest memento that was collected, and the number of URIs that had 
    their first memento collected during the same week as data collection.    
    """
    memento_counts = get_memento_counts()
    # Filter out memento counts of 0
    nonzero_memento_counts = [x for x in memento_counts if x != 0]
    decimal = len(nonzero_memento_counts)/len(memento_counts)
    # Calculate percentage of URIs that have been archived
    print(f"\nApproximately {decimal * 100:.0f}% of the URIs have been archived.\n")

    # Fetch oldest memento
    uri, date = get_oldest_memento()
    print(f"The oldest memento was collected on {date} for the following link: {uri}\n")

    # Calculate URI ages
    uri_ages, ems = get_uri_ages()
    uri_ages_stripped = [x for x in uri_ages if x != None]
    # URIs with age < 1 week
    young_uri_count = sum(1 for age in uri_ages_stripped if age < 7)
    young_decimal = young_uri_count/len(uri_ages)
    print(f"Approximately {young_decimal * 100:.0f}% of the URIs had their first memento collected in the same week as data collection.\n")
    return

def get_results():
    """
    Generates a dataframe containing the URI, the memento count for the URI, the age of the earliest memento using the URI's timemap data.

    Output:
    Returns a dataframe containing all features calculated for timemaps and URIs.
    """
    memento_counts = get_memento_counts()
    uri_ages, ems = get_uri_ages()
    # Fetch list of links to map to memento count and URI age properties
    links = get_links_list()
    df = pd.DataFrame(columns=['URI','Number of Mementos','Age in Days'])
    # for i in range(len(links)):
    for i in range(len(links)):
        new_row = {'URI':links[i],'Number of Mementos':memento_counts[i],'Age in Days':uri_ages[i]}
        df.loc[len(df)] = new_row
    return df

def get_age_results():
    """
    Generates a dataframe that lists the age of the earliest memento for each URI sorted in descending order by age. If a URI has not been archived, 
    it is represented as None.
    
    Output:
    Returns a dataframe containing the age of the earliest memento for each URI.
    """
    df = get_results()
    return df[['URI','Age in Days']].sort_values(by='Age in Days',ascending=False)

def get_memento_results():
    """
    Generates a DataFrame that lists the number of mementos for each URI, sorted in descending order by the number of mementos.    

    Output:
    Returns a dataframe containing the number of mementos for each URI.
    """
    df = get_results()
    return df[['URI','Number of Mementos']].sort_values(by='Number of Mementos',ascending=False)

def get_scatterplot():
    """
    Generates a scatterplot to show the correlation between URI ages and their number of mementos.

    Output:
    Returns a scatterplot representing the correlation between URI ages and their number of mementos.
    """
    # Fetch URI ages
    uri_ages, ems = get_uri_ages()
    uri_ages_stripped = [x for x in uri_ages if x != None]
    memento_counts = get_memento_counts()
    # Filter out memento counts of 0
    nonzero_memento_counts = [x for x in memento_counts if x != 0]
    # Create a scatterplot
    plt.scatter(uri_ages_stripped, nonzero_memento_counts, marker = 'o', alpha = 0.5)
    plt.xlabel('Age in Days')
    plt.ylabel('Number of Mementos')
    plt.title('Age vs. Number of Mementos')
    plt.grid(True)
    plt.show()

    return