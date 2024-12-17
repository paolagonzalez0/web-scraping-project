import subprocess
import os

"""
This script finds and collects the timemap for each URI in the tweet_links.txt file. The JSON files can be found under 
the 'timemaps' directory.
"""

def extract_json(full_output,link):
    """
    Returns extracted JSON output from the full command output. If the full output contains no JSON content, a 
    JSON string containing the original URI is returned.
    """
    # Find the index of the first and last curly braces
    start_index = full_output.find('{')
    end_index = full_output.rfind('}')
    # Extract the JSON content
    if start_index != -1 and end_index != -1:
        json_content = full_output[start_index:end_index+1]
        return json_content
    else:
        return str({"original_uri":f"{link}"}).replace("\'","\"")

def collect_timemap(link):
    """
    Executes Memgator command to collect the timemap for a single URI. Returns the full command output.
    """
    try:
        command = ["docker", "container", "run", "-it", "--rm", "oduwsdl/memgator", "--format=JSON", str(link)]
        # Execute the command and wait for it to complete
        result = subprocess.check_output(command, text = True, timeout = 120)
        # Strip out extraneous text
        json_content = extract_json(result,link)   
        return json_content
    # Error handling
    except subprocess.TimeoutExpired as e:
        print("ERROR OCCURRED:", command)
        print(e)
        return None
    except subprocess.CalledProcessError as e:
        print("ERROR OCCURRED:", command)
        print(e)
        return None
    
def save_timemaps(start_line=None):
    """
    Collects the timemaps for all URIs stored in tweet_links.txt. Processes output for each URI into a JSON file 
    and stores it in 'timemaps' directory. User can specify a line number to continue from in additional iterations of the 
    function to avoid overwriting previous files, otherwise function will start collecting timemaps from line 1 of 
    tweet_links.txt.
    """
    with open('../tweet_links.txt', 'r') as file:
        links = file.read().splitlines()
        # Start processing at given file, if specified.
        if start_line is not None:
            links = links[start_line-1:]
        for i, link in enumerate(links):
            if start_line is not None:
                # Create directory to store timemap data
                if not os.path.exists("../timemaps"):
                    os.makedirs("../timemaps")
                with open(f"../timemaps/uri{i+start_line}.json", "w") as json_file:
                    print(f"Collecting URI {i+start_line}: {link}..")
                    # Collect time map data and create a JSON file for a given URI
                    json_content = collect_timemap(link)
                    json_file.write(json_content)
            else:
                # Create directory to store timemap data
                if not os.path.exists("../timemaps"):
                    os.makedirs("../timemaps")
                with open(f"../timemaps/uri{i+1}.json", "w") as json_file:
                    print(f"Collecting URI {i+1}..")
                    # Collect time map data and create a JSON file for a given URI
                    json_content = collect_timemap(link)
                    json_file.write(json_content)

if __name__ == "__main__":
    # save_timemaps()
    pass