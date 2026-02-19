import json
import jsonlines
import requests
import os
import yaml

from dotenv import load_dotenv
from yaml import Loader

load_dotenv()

INSTA_USER_ID = os.getenv("INSTA_USER_ID")
INSTA_HASHTAGS = os.getenv("INSTA_HASHTAGS")

META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_USER_ID = os.getenv("META_USER_ID")
META_PAGE_NAME = os.getenv("META_PAGE_NAME")
META_SU_ACCESS_TOKEN = os.getenv("META_SU_ACCESS_TOKEN")


stream = open("configuration.yaml", 'r')
config = yaml.load(stream, Loader=Loader)

INSTA_API_VERSION = config['instagram']['api_version']
OUTPUT_FILE = config['video']['output_file_name']


def getPageAccessToken(userID, userAccessToken, metaPageName):
    url = f"https://graph.facebook.com/{userID}/accounts?access_token={userAccessToken}"

    r = requests.get(url)
    if not r.ok:
        print("STATUS:", r.status_code)
        print("RESPONSE:", r.text)
    r.raise_for_status()

    pageAccessToken = ""
    for page in r.json()["data"]:
         if page["name"] == metaPageName:
              pageAccessToken = page["access_token"]
              break
        
    if pageAccessToken:
        return pageAccessToken
    return None


def createReelContainer(apiVersion, instaUserID, accessToken, postTitle, hashTags):
    url = f"https://graph.facebook.com/{apiVersion}/{instaUserID}/media"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {accessToken}"
    }
    data = {
        "caption": f'''{postTitle}
                       .
                       .
                       .
                       {hashTags}''',
        "media_type": "REELS",
        "upload_type": "resumable",
        "share_to_feed": "true",
    }
    r = requests.post(url, headers=headers, data=data, timeout=60)
    if not r.ok:
            print("STATUS:", r.status_code)
            print("RESPONSE:", r.text)
    r.raise_for_status()

    return r.json()["id"], r.json()["uri"]


# generate an App access token
"""
def getAccessToken(appID, appSecret):
    url = f"https://graph.facebook.com/oauth/access_token?client_id={appID}&client_secret={appSecret}&grant_type=client_credentials"

    r = requests.get(url)
    if not r.ok:
            print("STATUS:", r.status_code)
            print("RESPONSE:", r.text)
    r.raise_for_status()

    return r.json()['access_token']
"""


def uploadToContainer(containerURI, userAccessToken, videoPath):
    videoFileSize = str(os.path.getsize(videoPath))

    headers = {
         "Authorization": f"OAuth {userAccessToken}",
         "offset": "0",
         "file_size": videoFileSize
    }

    with open(videoPath, "rb") as file:
         r = requests.post(containerURI, headers=headers, data=file, timeout=300)

    if not r.ok:
        print("STATUS:", r.status_code)
        print("RESPONSE:", r.text)
    r.raise_for_status()

    return r.text


def publishContainer(apiVersion, instaUserID, userAccessToken, containerID):
    url = f"https://graph.facebook.com/{apiVersion}/{instaUserID}/media_publish"
    headers = {
         "Authorization": f"OAuth {userAccessToken}"
    }
    data = {
         "creation_id": containerID
    }

    r = requests.post(url, headers=headers, data=data)

    if not r.ok:
        print("STATUS:", r.status_code)
        print("RESPONSE:", r.text)
    r.raise_for_status()

    return r.text


def main():
    videoPath = ""

    with jsonlines.open(OUTPUT_FILE, 'r') as jsonf:
        for jsonObject in jsonf:
            videoPath = jsonObject["video_path"]
    
    if videoPath:
        # NOTE: Currently there is a 7 day restriction before creating a system user on the Meta business profile
        #       Use the following website to create an access token in the meantime: https://developers.facebook.com/tools/explorer/?method=GET&path=me%3Ffields%3Did%2Cname&version=v24.0
        #       Generate a user access token for the proper Meta App
        #       After the 7 day restriction create a system user and generate a system user access token and update it for META_SU_ACCESS_TOKEN in .env
        metaPageAccessToken = getPageAccessToken(META_USER_ID, META_SU_ACCESS_TOKEN, META_PAGE_NAME)
        
        videoTitle = videoPath.split("/")[-1].replace(".mp4", "") 
        containerID, containerURI = createReelContainer(INSTA_API_VERSION, INSTA_USER_ID, metaPageAccessToken, videoTitle, INSTA_HASHTAGS)

        uploadMessage = json.loads(uploadToContainer(containerURI, META_SU_ACCESS_TOKEN, videoPath))["message"]
        print(f"Container Upload Status: {uploadMessage}")

        publishID = json.loads(publishContainer(INSTA_API_VERSION, INSTA_USER_ID, META_SU_ACCESS_TOKEN, containerID))["id"]
        print(f"Media successfully published from container {containerID} with ID: {publishID}")

    else:
        print("Error: Video path could not be found, please check output text file.")


if __name__ == "__main__":
    main()