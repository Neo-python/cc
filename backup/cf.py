from datetime import datetime
from shutil import copyfile, copy
import os
path = "/var/backup"
List = os.listdir(path)
os.chdir(path)
today = datetime.now().strftime("%Y-%m-%d")
hour = datetime.now().strftime("%H")
current = os.getcwd()
if today not in List:
    os.mkdir(path+f"/{today}")
if hour not in os.listdir(path+f"/{today}"):
    os.mkdir(path+f"/{today}/{hour}")
os.chdir(path+f"/{today}/{hour}")
copy("/var/www/cc/models/DPM.db", path+f"/{today}/{hour}")

for i in List:
    if (datetime.now() - datetime.strptime(i, "%Y-%m-%d")).days >= 2:
        def deletedir(delete_path):
            if len(os.listdir(delete_path)) == 0:
                os.rmdir(delete_path)
            else:
                for i in os.listdir(delete_path):
                    this_path = delete_path+f"/{i}"
                    if os.path.isdir(this_path):
                        deletedir(this_path)
                    else:
                        os.remove(this_path)
                os.rmdir(delete_path)
        deletedir(path+f"/{i}")