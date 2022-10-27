import re
import datetime
import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromiumService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

from settings import *

options = Options()
# options.add_argument("start-maximized")
options.add_argument("--headless")

driver = webdriver.Chrome(service=ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
# driver.implicitly_wait(0.2)


def find_all_files_on_pc_to_load(folder_with_cams):
    folders_to_load = []
    for camera in os.listdir(folder_with_cams):
        unchanged_folders = [folder_with_cams + '/' + camera + '/' + folder for folder in
                             os.listdir(folder_with_cams + '/' + camera) if re.search('_', folder) is None]
        folders_to_load = [*folders_to_load, *unchanged_folders]

    files_to_load = []
    for folder in folders_to_load:
        files_in_folder = [folder + '/' + file for file in os.listdir(folder)]
        files_to_load = [*files_to_load, *files_in_folder]

    return files_to_load


def switch_login_button_on_email(driver):
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.AuthLoginInputToggle-type>button[data-type="login"]')))
    log_buttons = driver.find_elements(By.CLASS_NAME, 'AuthLoginInputToggle-type')
    for button in log_buttons:
        if button.text == 'Почта':
            aria_pressed = button.find_element(By.CSS_SELECTOR, 'button').get_attribute('aria-pressed')
            if aria_pressed == 'false':
                button.click()


def load_files(files, driver, folder):
    if files != []:
        for file in files:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.upload-button__attach-wrapper')))  # .send_keys(file)
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.upload-button__attach[type="file"]'))).send_keys(file)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h3.uploader-progress__progress-primary')))
        WebDriverWait(driver, 1000).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'h3.uploader-progress__progress-primary'), 'Все файлы загружены'))
    print(str(len(files)) + ' -- files loaded in folder -->', folder)
    script_info['messages'].append(str(len(files)) + ' -- files loaded in folder -->' + folder)


def creating_new_dirs(driver, folders, cam_name):
    print('creating new dirs')
    for folder in folders:
        try:
            css = 'button.Button2.Button2_view_raised.Button2_size_m.Button2_width_max'
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).click()

            css = 'button.create-resource-button.create-resource-popup-with-anchor__create-item[aria-label="Папку"]'
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).click()

            css = 'form.rename-dialog__rename-form>span>input'
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css))).send_keys(Keys.CONTROL + "a")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css))).send_keys(Keys.DELETE)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css))).send_keys(folder)

            css = 'form.rename-dialog__rename-form>span>input'
            WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element_value((By.CSS_SELECTOR, css), folder))
            css = 'button.Button2.Button2_view_action.Button2_size_m.confirmation-dialog__button.confirmation-dialog__button_submit'
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).click()

        except Exception as err:
            print(cam_name + ' --- ' + 'folder -->' + folder + ' -- NOT CREATED')
            script_info['errors'].append('creating_new_dirs -- ' + cam_name + ' --- ' + 'folder -->' + folder + ' -- NOT CREATED')
            print(err)

def get_folder_with_last_date(folders_to_check):
    text_to_date = [datetime.datetime.strptime(folder, "%Y%m%d%H") for folder in folders_to_check]
    sorted_folders_to_check = [x for _, x in sorted(zip(text_to_date, folders_to_check))]
    return sorted_folders_to_check[-1]

def check_file_in_last_folder_and_download_new_files_if_it_existed(files, cam_name, driver):
    folders_to_check = list(set([file.split('/')[-2] for file in files]))
    last_date_folder = get_folder_with_last_date(folders_to_check)

    files_in_last_folder = [file for file in files if file.split('/')[-2] == last_date_folder]

    driver.get(way_to_load + '/' + cam_name + '/' + last_date_folder)

    files_in_folder_on_disk = []

    try:
        WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'listing-item__info')))
        css = 'div.listing-item.listing-item_theme_tile.listing-item_size_m.listing-item_type_file.js-prevent-deselect'
        files_in_folder_on_disk = driver.find_elements(By.CSS_SELECTOR, css)
        files_in_folder_on_disk = [file.text.replace('\n', '') for file in files_in_folder_on_disk]
    except TimeoutException:
        print(cam_name + '--> is empty folder')
        script_info['errors'].append('check_file_in_old_folders_and_download_new_files_if_it_existed -- ' + cam_name + '--> is empty folder')

    files_to_load = []
    for file in files_in_last_folder:
        if file.split('/')[-1] not in files_in_folder_on_disk:
            files_to_load.append(file)

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.upload-button__attach-wrapper')))
    load_files(files_to_load, driver, last_date_folder)


def load_files_in_folders(files_to_load, new_dirs, cam_name, driver):
    # print('start load files to new folder')
    for folder in new_dirs:
        folder_url = way_to_load + '/' + cam_name + '/' + folder
        driver.get(folder_url)

        # load files to new dirs
        files_to_load_on_this_folder = [file for file in files_to_load if re.search(folder, file) is not None]
        load_files(files_to_load_on_this_folder, driver, folder)
    # print('finished load files to new folder')

    # load files in old dirs if files not in this dirs
    files_not_in_new_folders = [file for file in files_to_load if file.split('/')[-2] not in new_dirs]
    # print('start load files to old folder')
    check_file_in_last_folder_and_download_new_files_if_it_existed(files_not_in_new_folders, cam_name, driver)
    # print('finished load files to old folder')


def upload_data_from_camera(cam_name, allfiles, driver):
    driver.get(way_to_load + '/' + cam_name)

    # wait until all folders will be find if directory is empty - catch exception
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'listing-item__info')))
    except TimeoutException:
        print(cam_name + '--> is empty folder')
        script_info['errors'].append('upload_data_from_camera -- ' + cam_name + '--> is empty folder')

    folders_in_disk = [element.text for element in driver.find_elements(By.CLASS_NAME, 'listing-item__info')]
    print(folders_in_disk)

    files_to_load = [file for file in allfiles if re.search(camera_dict[cam_name], file) is not None]
    new_dirs = set([file.split('/')[-2] for file in allfiles if re.search(camera_dict[cam_name], file) is not None and file.split('/')[-2] not in folders_in_disk])
    print('new_dirs')
    print(new_dirs)

    creating_new_dirs(driver, new_dirs, cam_name)
    load_files_in_folders(files_to_load, new_dirs, cam_name, driver)


def delete_old_folders_from_disk(driver, storage_date, cam_name):
    date_to_delete = (datetime.datetime.today() - datetime.timedelta(days=storage_date))

    driver.get(way_to_load + '/' + cam_name)
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'listing-item__info')))
    except TimeoutException:
        print(cam_name + '--> is empty folder')
        script_info['errors'].append('delete_old_folders_from_disk -- ' + cam_name + '--> is empty folder')

    all_folders = [element.text for element in driver.find_elements(By.CLASS_NAME, 'listing-item__info')]
    folders_to_delete = [folder for folder in all_folders if datetime.datetime.strptime(folder[:8], '%Y%m%d') < date_to_delete]
    # print(folders_to_delete)
    # print(len(folders_to_delete))
    css = 'div.listing-item.listing-item_theme_tile.listing-item_size_m.listing-item_type_dir.js-prevent-deselect>div.listing-item__info'
    all_folders_on_disk = driver.find_elements(By.CSS_SELECTOR, css)

    folders_to_delete_on_disk = []
    for folder in folders_to_delete:
        for folder_on_disk in all_folders_on_disk:
            if folder_on_disk.text == folder:
                folders_to_delete_on_disk.append(folder_on_disk)

    for folder in folders_to_delete_on_disk:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((folder))).click()
        css = 'div.hover-tooltip__tooltip-anchor>button[aria-label="Удалить"]'
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).click()
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'listing-item__info')))

    if folders_to_delete_on_disk:
        css = 'div.notifications__item.notifications__item_trash.nb-island.notifications__item_moved'
        WebDriverWait(driver, 1000).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css)))

    print(str(len(folders_to_delete)) + ' --- ' + 'folders deleted before date --> ' + datetime.datetime.strftime(date_to_delete, '%Y-%m-%d'))
    script_info['messages'].append(str(len(folders_to_delete)) + ' --- ' + 'folders deleted before date --> ' + datetime.datetime.strftime(date_to_delete, '%Y-%m-%d'))


def get_disk_info(driver, script_info):
    driver.get(base_disk_url)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'listing-item__info')))
    css = f'div.listing-item__info>div.listing-item__title.listing-item__title_overflow_clamp[aria-label="{folder_with_cams_on_disk}"]'
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).click()
    css = 'div.hover-tooltip__tooltip-anchor>button[aria-label="Информация"]'
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).click()
    css = 'div.resources-info-dropdown__row'
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css)))
    css = 'div.resources-info-dropdown__row'
    folder_info = driver.find_elements(By.CSS_SELECTOR, css)

    info = {'Имя': folder_with_cams_on_disk,
            'Размер': None,
            'Количество файлов': None,
            'Изменён': None}

    for i in folder_info:
        if re.search('Размер', i.text):
            info['Размер'] = i.find_element(By.CSS_SELECTOR, 'span.ufo-resource-info-dropdown__value').text

        if re.search('Количество', i.text):
            info['Количество файлов'] = i.find_element(By.CSS_SELECTOR, 'span.ufo-resource-info-dropdown__value').text

        if re.search('Изменён', i.text):
            info['Изменён'] = i.find_element(By.CSS_SELECTOR, 'span.ufo-resource-info-dropdown__value').text

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.InfoSpace__Text')))

    script_info['storage disk usage'] = info
    script_info['free space on disk'] = driver.find_element(By.CSS_SELECTOR, 'div.InfoSpace__Text').text.split('из')[0][8:].replace(' ', '')


def write_changes_on_file(script_info):
    data_dict = None
    with open(logging_file, 'r', encoding='utf-8') as f:
        data_dict = json.load(f)
        f.close()

    if data_dict:
        data_dict['data'].append(script_info)
        data_dict['len'] = len(data_dict['data'])

        with open(logging_file, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False)
            f.close()


script_info = {'date': None,
               'messages': [],
               'errors': [],
               'is_success': False,
               'cameras': cameras_to_write_on_disk,
               'storage disk usage': None,
               'free space on disk': None,
               'script_time_work': None
               }

if __name__ == '__main__':
    start_time = time.time()

    driver.get(way_to_load)
    files_to_load = find_all_files_on_pc_to_load(folder_with_cams)

    if re.search('passport', driver.current_url):
        print('making authorization')
        script_info['messages'].append('making authorization')

        phone_err = True
        while phone_err:
            try:
                switch_login_button_on_email(driver)

                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'passp-field-login'))).send_keys(email)
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'passp:sign-in'))).click()

                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'passp-field-passwd'))).send_keys(password)
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'passp:sign-in'))).click()

                WebDriverWait(driver, 20).until(EC.url_to_be(way_to_load))

                print('authorization finished')
                script_info['messages'].append('authorization finished')
                for key in camera_dict:
                    if key in cameras_to_write_on_disk:
                        print('start upload camera --> ' + key)
                        script_info['messages'].append('start upload camera --> ' + key)
                        upload_data_from_camera(key, files_to_load, driver)
                        print('finished upload camera --> ' + key)
                        script_info['messages'].append('finished upload camera --> ' + key)

                        print('start delete old folders camera --> ' + key)
                        script_info['messages'].append('start delete old folders camera --> ' + key)
                        delete_old_folders_from_disk(driver, storage_date, key)
                        print('finished delete old folders camera --> ' + key)
                        script_info['messages'].append('finished delete old folders camera --> ' + key)

                get_disk_info(driver, script_info)

                phone_err = False
                driver.close()
                script_info['is_success'] = True

            except TimeoutException:
                phone_err = True
                driver.close()
                driver = webdriver.Chrome(service=ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
                driver.get(way_to_load)

        script_info['date'] = datetime.datetime.today().strftime('%d-%m-%Y---%H:%M')
        script_info['script_time_work'] = time.time() - start_time
        # write_changes_on_file(script_info)















































