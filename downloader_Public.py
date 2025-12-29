import win32clipboard
import time
import threading
import requests
import os
import re
from tqdm import tqdm

#CHANGE ME!
secretKey = '?auth_token=[SecretkeyGoesHere]'

def get_clipboard_data():
    win32clipboard.OpenClipboard()
    try:
        data = win32clipboard.GetClipboardData()
    except TypeError:
        data = None
    win32clipboard.CloseClipboard()
    return data

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

            time.sleep(1) 

def main():
    magnetList = []
    monitor = ClipboardMonitor()
    monitor_thread = threading.Thread(target=monitor.monitor_clipboard, args=(magnetList,))
    monitor_thread.start()

    print('## Real-Debrid Torrent Downloader ##')
    print('https://github.com/xLuckyOne')


    print("Clipboard monitoring started. Enter 'q' to exit.")

    # Wait for user to press 'q'
    while True:
        user_input = input()
        if user_input.lower() == 'q':
            monitor.stop()
            break

    # Wait for clipboard monitoring thread to finish
    monitor_thread.join()  


    print('DEBUG: Getting all current Torrents')
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

    torrentsToDownload = [x for x in torrentsAfterAdding.json() if x not in torrentsBeforeAdding.json()]
    
    print('******** Downloads *************')
    #Get Torrent Objects in Torrent List (https://real-debrid.com/torrents)
    #For each Torrent
    for link in torrentsToDownload:
        #Display the Torrent filename
        tqdm.write(str(link.get('filename')))
        #For Each Downloadlink in Torrent
        for downloadlink in link.get('links'):
            
            #Unrescrict the current Link iteration
            unrestrictLink = requests.post('https://api.real-debrid.com/rest/1.0/unrestrict/link' + secretKey,{'link': downloadlink})
        
            #Get the Link
            starting_dl = unrestrictLink.json().get('download')

            # Prefer the per-file filename returned by the unrestrict API. Fall back to torrent name
            raw_filename = unrestrictLink.json().get('filename') or link.get('filename')
            # Sanitize filename to avoid path traversal and invalid chars on Windows
            def sanitize_filename(name: str) -> str:
                # Keep only safe characters and replace others with '_'
                name = str(name)
                # Collapse any path separators and take basename to avoid directories
                name = os.path.basename(name)
                # Replace invalid Windows filename characters
                name = re.sub(r'[<>:"/\\|?*]', '_', name)
                # Trim whitespace
                name = name.strip()
                # Fallback
                if not name:
                    name = 'downloaded_file'
                return name

            filename = sanitize_filename(raw_filename)

            # Avoid accidental overwrites: if file exists, append a counter before extension
            base, ext = os.path.splitext(filename)
            counter = 1
            candidate = filename
            while os.path.exists(candidate):
                candidate = f"{base}({counter}){ext}"
                counter += 1
            filename = candidate

            with requests.get(starting_dl, stream=True) as r:
                r.raise_for_status()
                # Content-Length may be missing
                content_length = r.headers.get('Content-Length')
                try:
                    total = int(content_length) if content_length is not None else None
                except ValueError:
                    total = None

                # Open file and stream
                with open(filename, 'wb') as f:
                    if total:
                        pbar = tqdm(total=total, unit='B', unit_scale=True, desc=filename)
                    else:
                        pbar = tqdm(unit='B', unit_scale=True, desc=filename)

                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk: 
                            f.write(chunk)
                            pbar.update(len(chunk))
                    # ensure the bar is closed
                    pbar.close()
        print('\n')
    

if __name__ == '__main__':
    import sys

    main()

