import praw
import os
import yaml
import random
import time
import json

from dotenv import load_dotenv
from yaml import Loader
from yt_dlp import YoutubeDL

DOWNLOAD_DIR = (os.getcwd() + "\downloads\\").replace("\\", "/")

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

stream = open("configuration.yaml", 'r')
config = yaml.load(stream, Loader=Loader)

REDDIT_SEARCH_LIMIT = config['reddit']['search_limit']
NUM_SUBREDDIT_CHOICES = config['reddit']['num_subreddit_choices']
MAX_VID_DURATION = config['video']['max_duration']


def downloadLatestVideo(redditInstance, subredditChosen):

    try:
        currentSubreddit = redditInstance.subreddit(subredditChosen)
    except Exception as e:
        print(f"Unable to connect to the subreddit '{subredditChosen}' due to the following error: {e}")
        return None

    print(f"Successfully connected to subreddit '{subredditChosen}'\nSearching for video to download from 'hot' category...")

    for post in currentSubreddit.hot(limit=REDDIT_SEARCH_LIMIT):
        
        # 5 second delay to deter bot detection
        time.sleep(5)

        if post.is_video and post.media:
            hasAudio = post.media['reddit_video']['has_audio']
            duration = post.media['reddit_video']['duration']
            
            if duration <= MAX_VID_DURATION and hasAudio:
                print(f"Found video titled: {post.title} from subreddit '{currentSubreddit.display_name}'")
                print("Attempting video download...")

                postURL = "https://www.reddit.com" + post.permalink
                filterPostTitle = ''.join(i for i in post.title if i.isalnum() or i == " ")
                try:
                    time.sleep(5)

                    ydl_opts = {
                        "format": "bv*+ba/b",
                        "merge_output_format": "mp4",
                        "outtmpl": DOWNLOAD_DIR + filterPostTitle + ".%(ext)s"
                    }
                    
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.download([postURL])
                except Exception as e:
                    print(f"Error downloading video: {e}\nAttempting new video download...")
                    continue
                
                return post, filterPostTitle + ".mp4"
    return None


def main():
    redditInstance = praw.Reddit(
                    client_id=REDDIT_CLIENT_ID, 
                    client_secret=REDDIT_CLIENT_SECRET,
                    user_agent=REDDIT_USER_AGENT)
    
    subredditList = []
    for num in range(1, NUM_SUBREDDIT_CHOICES + 1):
        subredditList.append(os.getenv(f"SUBREDDIT_CHOICE_{num}"))
    
    subredditChosen = random.choice(subredditList)

    post, videoFileTitle = downloadLatestVideo(redditInstance, subredditChosen) 

    if post != None:
        videoData = {
            "video_path": DOWNLOAD_DIR + videoFileTitle
        }
        
        with open("output_video_path.txt", "w") as f:
            json.dump(videoData, f)
        
        print("Output text file successfully created.")
        print("Download.py script successfully completed.")
    else:
        print("Download.py script completed with errors.")


if __name__ == "__main__":
    main()