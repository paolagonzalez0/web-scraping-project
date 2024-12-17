# Web-Scraped Tweet Timemap Analysis

The project writeup can be found [here](documentation/documentation.pdf).

### Project Description
This project focuses on the collection and analysis of web-linked resources (URIs) shared through tweets, specifically around social movements. By scraping tweets that discuss key topics related to various social movements such as climate change, racial justice, and gender equality, this project aims to examine how well the linked content (often news articles, studies, or other online resources) is preserved over time. The study specifically tracks how these web resources are archived using web mementos (time snapshots), assessing the availability and longevity of these crucial records in the digital archive.

### Project Summary and Objectives

This project is structured into four key phases:

1. Tweet Collection: Gather tweets related to social movements through web scraping.
2. URI Extraction: Identify and extract URIs embedded within the collected tweets.
3. Timemap Retrieval: Use MemGator to obtain timemaps (lists of mementos) for each extracted URI.
4. Memento Analysis: Analyze the mementos to uncover patterns in the preservation of digital resources associated with social movements.

### Project Execution
This project can be executed in two approaches. The first approach involves both data collection and analysis, covering all four phases of the project: tweet collection, URI extraction, timemap retrieval, and memento analysis. The second approach uses previously existing data to run phase four of the project exclusively, without collecting new data.

**To execute all four phases of the project:**
- Ensure the prerequisites in next section of the documentation are met.
- Run the tweet collection, URI extraction, and timemap retrieval processes by navigating to the scripts directory and running the following command in terminal:
    - `python main.py --total_links_to_scrape 150`
    - Upon running this command, the Nightly browser should open automatically to the Twitter log in page. From here, input your login credentials from your new Twitter account and the program will begin executing the first three phases of the project.
    - In this example, the program will collect data until 150 URIs have been saved. To collect more or less URIs, replace 150 with the desired number of URIs to be analyzed.
    - Note: This program has been run previously to collect sample data. By running the program again, new data will be added to the previously existing data.
- Next, the analysis of the project can be executed by opening and running the code in `analysis.ipynb`. This notebook showcases the results and summary statistics calculated on the collected data.

**To execute the project without data collection:**
- The analysis of the project can be executed by opening and running the code in \texttt{analysis.ipynb}. This notebook uses previously collected data to calculate the results and summary statistics showcased in final analysis.

### Prerequisites

Prior to execution, ensure the following prerequisites are fulfilled for the program
to function correctly.

1. Clone the repository

- Navigate to your desired local directory and execute the following command in
your terminal.
- `git clone https://github.com/paolagonzalez0/web-scraping-project.git`
2. Create a Twitter account

- To complete tweet collection, a Twitter account is needed. To set up an account, follow the instructions provided [here](https://help.x.com/en/using-x/create-x-account). 

- Note: To avoid any disruptions, do not use your personal account or an account you can’t afford to lose. There’s a possibility that the account might be flagged or suspended for suspicious activity
during the scraping process. Consider creating a dedicated account specifically
for this project.

3. Download Docker Desktop

- Download and install Docker Desktop [here](https://www.docker.com/products/docker-desktop/). This tool will be used for retrieving the URI timemaps in phase three of the project. 
- For timemap retrieval to execute properly, pull a published image from a Docker image registry to run
Memgator by running the following command in your terminal:
- `docker image pull oduwsdl/memgator`

4. Install necessary libraries and tools

- Python Version
    - The program requires Python 3.8 or newer. Ensure Python on your device is up to date by running the following command in your terminal:
    - `python --version`
- Required Libraries
    - Install dependencies listed in requirements.txt by running the following command in your terminal:
    - `pip install -r requirements.txt`
- Browser Automation Tools
    - Ensure Playwright browser tool is installed by running the following command in your terminal:
    - `playwright install`
- Network Access
    - Ensure you have stable internet access for scraping.