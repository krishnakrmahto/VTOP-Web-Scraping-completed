import os, datetime, re, exam_schedule, platform, shutil, time, logging


#set up log configuration to log download records
logging.basicConfig(filename = 'log/downloadlog.txt', level = logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s')

def find_dir_name():
    date_re_str = r'(\d{2})-([A-Za-z]{3})-(\d{4})'
    date_re = re.compile(date_re_str)
    mo = date_re.search(lecture_date)
    lecture_date = datetime.datetime(int(mo.group(3)),int(exam_schedule.monthname_monthnum[mo.group(2)]),int(mo.group(1)))

    if exam_schedule.exam_schedule['CAT-1_end'] >= lecture_date:
        return 'CAT-1'
    elif exam_schedule.exam_schedule['CAT-1_end'] < lecture_date and exam_schedule.exam_schedule['CAT-2_end'] >= lecture_date:
        return 'CAT-2'
    else:
        return 'FAT'

def find_download_dir():
    if platform.system() == 'Windows':
        download_dir = 'C:\\VTOP_Course_Materials'

    elif platform.system() == 'Linux':
        download_dir = os.environ['HOME'] + '/VTOP_Course_Materials'

    return download_dir

def download_files(browser, dir_name, download_links):
    root_dir_name = browser.find_element_by_css_selector('#CoursePageLectureDetail > div > div.panel-body > div:nth-child(1) > div > table > tbody > tr:nth-child(2) > td:nth-child(2)').text
    logging.debug('Course name: ' + root_dir_name)
    download_dir = find_download_dir()
    print('Download directory: ' + download_dir)

    if not os.path.isdir(download_dir):
        os.mkdir(download_dir)

    os.chdir(download_dir)
    if not os.path.isdir(root_dir_name):
        os.mkdir(root_dir_name)
    if not os.path.isdir('temp'):
        os.mkdir('temp')

    os.chdir(root_dir_name)
    faculty_name = browser.find_element_by_css_selector('#CoursePageLectureDetail > div > div.panel-body > div:nth-child(1) > div > table > tbody > tr:nth-child(2) > td:nth-child(6)').text
    faculty_name = (faculty_name.split(' - '))[1]
    logging.debug('Faculty name: ' + faculty_name)

    if not os.path.isdir(faculty_name):
        os.mkdir(faculty_name)
    os.chdir(faculty_name)

    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)
    else:
        print('Files already downloaded.')
        logging.debug('Files were already downloaded')
        return
    os.chdir(os.path.join(download_dir, 'temp'))

#Download and save and rename the file in temp directory synchronously, ie, wait for one file to complete download before starting the next
    for k, v in download_links.items(): # v is a list
        counter_append = 0
        if len(v) > 1:
            for link in v:
                counter_append += 1
                intuitive_file_name = k + '_' + str(counter_append)

                logging.debug(intuitive_file_name + ': ' + str(len(v)) + ' files')
                browser.get(link)
                time.sleep(2)

                while True:
                    download_file_name = (os.listdir())[0]
                    filename, extension = os.path.splitext(download_file_name) # if download is done before this line is executed, then extension will be ppt or pdf, else it will be crdownload
                    # if download was done, download_ext will be empty str, else it will be pdf or ppt
                    if extension != '.crdownload': # and not download_ext: # download is complete
                        shutil.move(filename+extension, intuitive_file_name)
                        shutil.move(intuitive_file_name, os.path.join(download_dir, root_dir_name, faculty_name, dir_name))
                        logging.debug('File ' + str(counter_append) + ' downloaded.')
                        break

                    else:
                        continue

        else:
            counter = 1
            for link in v:
                intuitive_file_name = k
                if intuitive_file_name == '':
                    intuitive_file_name = 'file' + str(counter)
                    counter += 1
                # browser.switch_to_window(browser.window_handles[0])
                logging.debug(intuitive_file_name + ': 1 file')
                browser.get(link)
                time.sleep(2)
                # browser.switch_to_window(browser.window_handles[1])
                while True:
                    download_file_name = (os.listdir())[0]
                    filename, extension = os.path.splitext(download_file_name) # if download is done before this line is executed, then extension will be ppt or pdf, else it will be crdownload
                    # if download was done, download_ext will be empty str, else it will be pdf or ppt
                    if extension != '.crdownload':# and (download_ext == 'pdf' or 'ppt' in download_ext or 'doc' in download_ext): # download is complete
                        shutil.move(filename+extension, intuitive_file_name)
                        shutil.move(intuitive_file_name, os.path.join(download_dir, root_dir_name, faculty_name, dir_name))
                        logging.debug('1 file downloaded.')
                        break

                    else:
                        continue

def download_course_materials(browser):
    print('Hold your seat, your files are downloading...')
    rows_in_ref_material_table = browser.find_elements_by_css_selector('#CoursePageLectureDetail > div > div.panel-body > div:nth-child(3) > div:nth-child(2) > div > table > tbody > tr')

    now = datetime.datetime.now()
    today_date = datetime.datetime(now.year, now.month, now.day)
    date_re_str = r'(\d{2})-([A-Za-z]{3})-(\d{4})'
    date_re = re.compile(date_re_str)

#Finding the most recent exam that got finished
    any_exam_done = False
    today_date = datetime.datetime(2018,1,29)
    if exam_schedule.exam_schedule['CAT-1_end'] < today_date:
        exam_done = 'CAT-1' # ie, download after lecture dates that fall in CAT-1 period, or do not download CAT-1 files
        exam_done_end_date = exam_schedule.exam_schedule[exam_done +'_end']
        # print(exam_done_end_date)
        any_exam_done = True
    if exam_schedule.exam_schedule['CAT-2_end'] < today_date:
        exam_done = 'CAT-2' # downlaod after lecture dates that fall in CAT-1 and CAT-2 period
        exam_done_end_date = exam_schedule.exam_schedule[exam_done +'_end']
        # print(exam_done_end_date)
        any_exam_done = True
    if any_exam_done == False:
        exam_done = 'none'
        exam_done_end_date = datetime.datetime(1,1,1) # smaller than any other date in the recent


# Remove those rows whose lecture_date < end date of exam that has alrady been conducted
    initial_row_num = len(rows_in_ref_material_table)
    updated_row_num = initial_row_num

#NOTE: while it may appear that using two nested loop (while-for) is not required for removing elements from the
#NOTE contd..: list rows_in_ref_material_table and that it can be done with the single for loop similar to the inner for loop, it cannot be actually. Because
#NOTE contd..: for remove method removes item and then does a left shift as well, so for eg, l = [1,2,3,4,5] for i in l: l.remove(i) will actually remove the objects
#NOTE contd..: 1,3,5 not all the objects of the list. Same happens in the indexed loop used in association with range function.
    not_done = True
    while not_done:
        for i in range(1, initial_row_num):
            if i >= updated_row_num:
                not_done = False
                break
            cells = rows_in_ref_material_table[i].find_elements_by_css_selector('td')
            lecture_date = cells[1].text
            # print(lecture_date)
            mo = date_re.search(lecture_date)
            lecture_date = datetime.datetime(int(mo.group(3)),int(exam_schedule.monthname_monthnum[mo.group(2)]),int(mo.group(1)))
            print(lecture_date)
            if exam_done_end_date > lecture_date:
                # print('len before: '+ str(len((rows_in_ref_material_table))))
                rows_in_ref_material_table.remove(rows_in_ref_material_table[i])
                print(cells[3].text)
                updated_row_num -= 1
                break

# Accumulate the download links for the reference materials
    download_links = {}
    for i in range(1, len(rows_in_ref_material_table)):
        cells = rows_in_ref_material_table[i].find_elements_by_css_selector('td')
        anchor_tags = cells[len(cells)-1].find_elements_by_css_selector('p a')

        if len(anchor_tags) == 0:
            continue

        if exam_done == 'CAT-1':
            dir_name = 'CAT-2'
        elif exam_done == 'CAT-2':
            dir_name = 'FAT'
        else:
            dir_name = 'CAT-1'

        key = cells[3].text
        download_links[key] = []
        for anchor_tag in anchor_tags:
            href = anchor_tag.get_attribute('href')
            download_link = href
            download_links[key].append(download_link)

    download_files(browser, dir_name, download_links)
    print('Download finished!')
