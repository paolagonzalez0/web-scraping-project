import subprocess
import os

"""
This script addresses Q2 of the assignment. It finds and collects the timemap for each URI in the 1000_tweet_links.txt 
file. The JSON files can be found under the 'timemaps' folder.
"""

def extract_json(full_output,link):
    """
    Extracts the JSON output from the full command output and returns it. If the command returns no JSON content, a 
    JSON string containing the original link is returned.
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
    Runs memgator command to collect the timemap for a single link. Returns the full command output.
    """
    try:
        command = ["docker", "container", "run", "-it", "--rm", "oduwsdl/memgator", "--format=JSON", str(link)]
        # Execute the command and wait for it to complete
        result = subprocess.check_output(command, text = True, timeout = 120)
        # Strip out extraneous text
        json_content = extract_json(result,link)   
        return json_content

    except subprocess.TimeoutExpired as e:
        print("ERROR OCCURRED:", command)
        print(e)
        return None
        # return str({"original_uri":f"{link}"}).replace("\'","\"")
    except subprocess.CalledProcessError as e:
        print("ERROR OCCURRED:", command)
        print(e)
        return None
        # return str({"original_uri":f"{link}"}).replace("\'","\"")

def save_timemaps(start_line=None):
    """
    Collects the timemaps for all links stored in 1000_tweet_links.txt. Processes output for each link into a JSON file 
    and stores it in 'timemaps' folder. User can specify a line number to continue from in additional iterations of the 
    function to avoid overwriting previous files, otherwise function will start collecting timemaps from line 1 of 
    1000_tweet_links.txt.
    """
    with open('1000_tweet_links.txt', 'r') as file:
        links = file.read().splitlines()
        if start_line is not None:
            links = links[start_line-1:]
        for i, link in enumerate(links):
            if start_line is not None:
                if not os.path.exists("timemaps"):
                    os.makedirs("timemaps")
                with open(f"timemaps/uri{i+start_line}.json", "w") as json_file:
                    print(f"Collecting URI {i+start_line}: {link}..")
                    json_content = collect_timemap(link)
                    json_file.write(json_content)
            else:
                if not os.path.exists("timemaps"):
                    os.makedirs("timemaps")
                with open(f"timemaps/uri{i+1}.json", "w") as json_file:
                    print(f"Collecting URI {i+1}..")
                    json_content = collect_timemap(link)
                    json_file.write(json_content)

if __name__ == "__main__":
    # save_timemaps(260)
    pass
