import requests
import json
import time
from tqdm import * 


print('## Real-Debrid Torrent Downloader ##')
print('https://github.com/xLuckyOne')


magnetList = []
#Edit your Secretkey to allow API access
secretKey = '?auth_token={SecretKeyGoesHere}'


#Get Userinput
while True:
    user_input = input("Enter a Magnet to add to the Downloadlist or continue with 'n' ")
    
    if user_input.lower() == 'n':
        break
    else:
        magnetList.append(user_input)
    
    
#Download the Magnets from Userinput    
for downloadTask in magnetList:
    #Add Magnet from downloadTask to Downloadlist 
    postMagnet = requests.post("https://api.real-debrid.com/rest/1.0/torrents/addMagnet" + secretKey ,{'magnet': downloadTask.strip()})
    
    #Select all Files from magnetJsonObject Magnet
    selectFiles = requests.post("https://api.real-debrid.com/rest/1.0/torrents/selectFiles/"+ postMagnet.json().get('id') +  secretKey,{'files': 'all'})

    #Get Info from TorrentID 
    infofromTorrentID = requests.get("https://api.real-debrid.com/rest/1.0/torrents/info/"+ postMagnet.json().get('id') + secretKey)

    #Display if Torrent has been successfully added or nah
    if selectFiles.status_code == 204:
        print("Torrent " + infofromTorrentID.json().get('filename') + " has been added")
    else:
        print("Failure in adding Torrent: " + downloadTask)
    




#Get all Torrents in https://real-debrid.com/torrents
getTorrentList = requests.get("https://api.real-debrid.com/rest/1.0/torrents" + secretKey)

print("******** Downloads *************")
#Get Torrent Objects in Torrent List (https://real-debrid.com/torrents)
#For each Torrent
for link in getTorrentList.json():
    #Display the Filename iteration
    print(link.get('filename'))
    #For Each Downloadlink in Torrent
    for downloadlink in link.get('links'):
        
        #Unrescrict the current Link iteration
        unrestrictLink = requests.post("https://api.real-debrid.com/rest/1.0/unrestrict/link" + secretKey,{'link': downloadlink})
       
        #Download the Link and display Downloadstatus
        #TODO: Download Pfad auswählbar machen
        print("Starting DL of: " + unrestrictLink.json().get('download'))
        with requests.get(unrestrictLink.json().get('download'), stream=True) as r:
            r.raise_for_status()
            with open(link.get('filename'), 'wb') as f:
                pbar = tqdm(total=int(r.headers['Content-Length']))
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        pbar.update(len(chunk))   
    print("\n")



