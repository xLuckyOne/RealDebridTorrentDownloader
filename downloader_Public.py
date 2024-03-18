import win32clipboard
import time
import threading
import requests
from tqdm import * 

#CHANGE ME!
secretKey = '?auth_token=[SecretkeyGoesHere]'

#Function to get the clipboard data
def get_clipboard_data():
    win32clipboard.OpenClipboard()
    try:
        data = win32clipboard.GetClipboardData()
    except TypeError:
        data = None
    win32clipboard.CloseClipboard()
    return data

#Clipboard monitoring thread
class ClipboardMonitor:
    def __init__(self):
        self.running = True

    def stop(self):
        self.running = False

    def monitor_clipboard(self, magnetList):
        while self.running:
            current_data = get_clipboard_data()

            if current_data and current_data.startswith('magnet:'):
                if current_data not in magnetList:
                    magnetList.append(current_data)
                    print('\n New clipboard entry added:', current_data)

            time.sleep(1)  # Adjust the interval as needed

def main():
    magnetList = []
    monitor = ClipboardMonitor()
    monitor_thread = threading.Thread(target=monitor.monitor_clipboard, args=(magnetList,))
    monitor_thread.start()

    print('## Real-Debrid Torrent Downloader ##')
    print('https://github.com/xLuckyOne')


    print("Clipboard monitoring started. Enter 'q' to exit.")

    # Wait for user to press 'q' and stop monitoring thread
    while True:
        user_input = input()
        if user_input.lower() == 'q':
            monitor.stop()
            break

    monitor_thread.join()  # Wait for clipboard monitoring thread to finish

    #get current torrents before adding new
    torrentsBeforeAdding = requests.get('https://api.real-debrid.com/rest/1.0/torrents/' + secretKey)


    print('Monitoring ended, starting downloads')
    
    for downloadTask in magnetList:
        #Add Magnet from downloadTask to Downloadlist 
        postMagnet = requests.post('https://api.real-debrid.com/rest/1.0/torrents/addMagnet' + secretKey ,{'magnet': downloadTask.strip()})
        
        #Select all Files from magnetJsonObject Magnet
        selectFiles = requests.post('https://api.real-debrid.com/rest/1.0/torrents/selectFiles/'+ postMagnet.json().get('id') +  secretKey,{'files': 'all'})

        #Get Info from TorrentID 
        infofromTorrentID = requests.get('https://api.real-debrid.com/rest/1.0/torrents/info/'+ postMagnet.json().get('id') + secretKey)

        #Display if Torrent has been successfully added or nah
        if selectFiles.status_code == 204:
            print('Torrent ' + infofromTorrentID.json().get('filename') + ' has been added')
        else:
            print('Failure in adding Torrent: ' + downloadTask)

    #Get all Torrents in https://real-debrid.com/torrents
    torrentsAfterAdding = requests.get('https://api.real-debrid.com/rest/1.0/torrents' + secretKey)

    #Calculate difference between torrent lists, only downloads newly added torrents, kill this if you want to download everything always.
    torrentsToDownload = [x for x in torrentsAfterAdding.json() if x not in torrentsBeforeAdding.json()]
    print('******** Downloads *************')
    #Get Torrent Objects in Torrent List (https://real-debrid.com/torrents)
    #For each Torrent
    for link in torrentsToDownload.json():
        #Display the Filename iteration
        print(link.get('filename'))
        #For Each Downloadlink in Torrent
        for downloadlink in link.get('links'):
            
            #Unrescrict the current Link iteration
            unrestrictLink = requests.post('https://api.real-debrid.com/rest/1.0/unrestrict/link' + secretKey,{'link': downloadlink})
        
            #Download the Link and display Downloadstatus
            print('Starting DL of: ' + unrestrictLink.json().get('download'))
            with requests.get(unrestrictLink.json().get('download'), stream=True) as r:
                r.raise_for_status()
                with open(link.get('filename'), 'wb') as f:
                    pbar = tqdm(total=int(r.headers['Content-Length']))
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                            pbar.update(len(chunk))   
        print('\n')
    

if __name__ == '__main__':
    main()
