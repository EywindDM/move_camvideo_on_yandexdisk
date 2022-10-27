import os


folder_with_cams_on_disk = 'xiaomi_cams'
folder_with_cams = '/mnt/WDC/share/xiaomi_camera_videos'

base_disk_url = 'https://disk.yandex.ru/client/disk'
way_to_load = base_disk_url + '/' + folder_with_cams_on_disk

email = os.environ.get('EMAIL')
password = os.environ.get('PASSWORD')

camera_dict = {'кабинет': '607ea49ecea6',
               'детская': '607ea49f4f7e',
               'мастерская': '607ea49f4594',
               'парадная': '607ea49edf68',
               'двор': '607ea49f34af'
               }

# cameras_to_write_on_disk = ['мастерская', ]
cameras_to_write_on_disk = ['парадная', 'кабинет', 'детская', 'мастерская', 'двор']

logging_file = '/home/dmitry/python_projects/move_camvideo_on_yandexdisk/log/loggin_file.json'

# days to keep data in storage
storage_date = 30
