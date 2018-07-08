# Make the imports
import requests, sys, pytesseract, base64, getpass, datetime, time, threading, platform, os, argparse, shelve, logging
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.support.ui import Select
from PIL import Image
from parser import CaptchaParse
from source_of_functions import *

print(
        '''
        How to execute:
            new user login---  1. if user doesn't want his username/password to be saved     python automate_vtop.py -n
                                2. 1. if user wants his username/password to be saved     python automate_vtop.py -n -s
            login with saved credentials: python automate_vtop.py
        Make sure you used the appropriate way to execute the script, if not, press "CTRL+C" now to exit and retry running the program.
        '''
        )

#Set up log settings
logging.basicConfig(filename = 'log/downloadlog.txt', level = logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s')
log_file = open('log/downloadlog.txt','w')
log_file.close()


#1. Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument('-n', '--newuser', help= 'Give this option if you are logging in for the first time or \
                    you want to login into a new account.', action = 'store_true')
parser.add_argument('-s', '--savecredentials', help = 'Give this option to save the username and password you entered.', action = 'store_true')
args = parser.parse_args()

#2. Read registration number, password and semester from user-inputs if this is first time login or new login
# and also shelve the credentials
if args.newuser and args.savecredentials:
    registration_num = input('Enter registration number: ')
    password = getpass.getpass('Enter password: ')

    if registration_num == '' or password == '':
        print('None of registration number, password can be left empty.')
        logging.debug('Registration number/password not entered correctly. Attempted with -ns options')
        sys.exit()

    shelf_file = shelve.open('./shelf/shelf_file')
    shelf_file['registration_num'] = registration_num
    shelf_file['password'] = password
    shelf_file.close()

    print('** make sure you enter correct registration number and password **')

if args.newuser and not args.savecredentials:
    registration_num = input('Enter registration number: ')
    password = getpass.getpass('Enter password: ')

    if registration_num == '' or password == '':
        print('None of registration number, password, semester fields can be left empty.')
        logging.debug('None of registration number, password can be left empty. Attempted with -n option')
        sys.exit()

#it is a plausible case that a user will choose to save credentials but is not using new credentials becase the plan is to ask
# the user for new credentials only, ie, args.savecredentials and not args.newuser is being dropped to code for

if not args.newuser and not args.savecredentials:

    if not os.path.isfile('./shelf/shelf_file.dat'):
        print('No saved credentials. Try again with -n option to login as a new user. You can use -s option with -n to save the credentials entered.')
        logging.debug('Did not run the script either with -n or -s options and no credentials have been saved before')
        sys.exit()

    try:
        shelf_file = shelve.open('./shelf/shelf_file')
        registration_num = shelf_file['registration_num']
        password = shelf_file['password']
        shelf_file.close()
    except:
        pass

today = datetime.datetime.now()

print('Attempting to log you in...')

#3. Open a controllable browser using Selenium webdriver module with a custom download directory
chrome_options = webdriver.ChromeOptions()
download_dir = find_download_dir()
prefs = {'download.default_directory': download_dir + '/temp'}
chrome_options.add_experimental_option('prefs', prefs)
chromedriver = './chromedriver'
browser = webdriver.Chrome(executable_path=chromedriver, chrome_options = chrome_options)
browser.maximize_window()

#4. Create wait object
waiting = WebDriverWait(browser,300)

#5. Open vtop home page
try:
    try:
        browser.get('http://vtop.vit.ac.in')
    except:
        print('Check your internet connection!')
        sys.exit()

    #6. Find the link to the vtopbeta page
    try:
        vtopbeta_elem = browser.find_element_by_css_selector('a[href = "https://vtopbeta.vit.ac.in/vtop"] font b')
        # print('Found element that href\'s to vtopbeta')
    except:
        print('Unexpected error: failed to load the page. Please retry')
        logging.debug('No element with attribute value a[href="https://vtopbeta.vit.ac.in/vtop"] was found')
        sys.exit()

    #7. Open vtopbeta
    browser.get(vtopbeta_elem.text)

    #8. Find the link to login page on vtopbeta captcha_img_elem and click on the elem to open the next page, ie, the login page
    try:
        login_page_link_elem = browser.find_element_by_css_selector('.btn.btn-primary.pull-right')
        # print('Found element that href\'s to the login page')
    except NoSuchElementException:
        print('Unexpected error: Unable to open vtopbeta page properly. Please retry')
        logging.debug('Check the css selector for the button leading to the login page: ' + str(err))
        sys.exit()

    login_page_link_elem.click()
    waiting.until(lambda browser: len(browser.window_handles) == 2)
    browser.switch_to_window(browser.window_handles[1])

    #9. From the login page, find the input elements (uname and pwd boxes and captcha box)
    try:
        waiting.until(EC.presence_of_element_located((By.ID, 'captchaCheck')))
        username_elem = browser.find_element_by_css_selector('#uname')
        password_elem = browser.find_element_by_css_selector('#passwd')
        captcha_elem = browser.find_element_by_css_selector('#captchaCheck')
        captcha_img_elem = browser.find_element_by_css_selector('img[alt = "vtopCaptcha"]')
    except NoSuchElementException as err:
        print('Unexpected error: Failed to load the login page properly. Please retry')
        logging.debug('Input elements with the given css selectors were not found: ' + err)
        sys.exit()

    #10. Find the image source of the captcha image
    captcha_img_src = captcha_img_elem.get_attribute('src')

    #11. Extract the base64 stribg of the captcha image from the captcha_img_src
    base64_img = captcha_img_src[22:]

    #12. Save the captcha image
    captcha_img = open('./captcha_save/captcha.png','wb')
    captcha_img.write(base64.b64decode(base64_img))
    captcha_img.close()

    #13. Convert the image into string
    img = Image.open('./captcha_save/captcha.png')
    captcha_str = CaptchaParse(img)

    #14. Fill in login details
    username_elem.send_keys(registration_num)
    password_elem.send_keys(password)
    captcha_elem.send_keys(captcha_str)

    #15. Sign in
    # note: the form doesn't have a submit button, the sign in button is not the submit button
    # so maybe that is why using submit method on form elements leads to a page that doesn't exist
    signin_button = browser.find_element_by_css_selector('.btn.btn-primary.pull-right')
    signin_button.click()

    #16. Handle wrong reg/pwd inputs
    try:
        WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.user-image')))
    except:
        print('Wrong registration number/password')
        logging.debug('Wrong user credentials')
        sys.exit()

    #TODO: scrapped the profile to obtain different informations- time table of currrent day, for eg
    #17. Open the menu on the left using the toggle hamburger button- first find the button and then click
    try:
        waiting.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[role = "button"]')))
    except:
        print('VTOP taking too long to respond!')
        logging.debug('VTOP server taking too long to respond')
        sys.exit()
    hamburger_elem = browser.find_element_by_css_selector('a[role = "button"]')
    hamburger_elem.click()

    #18. Find the Academics option in the left menu and lick on it
    academics_elem = browser.find_element_by_css_selector('#dbMenu ul.sidebar-menu.tree>li:nth-child(2)')
    academics_elem.click()

    #19. Get the time table element and click on it
    waiting.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#dbMenu ul.sidebar-menu.tree>li:nth-child(2) li:nth-child(2)>a span')))
    coursepage_elem = browser.find_element_by_css_selector('#dbMenu ul.sidebar-menu.tree>li:nth-child(2) li:nth-child(4)>a span')
    coursepage_elem.click()
    hamburger_elem.click()

    #20. Let the user select semester name and course from the page manually
    print('Choose Semester Name and Course from the dropdown on the page.')
    waiting.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.table')))

    js = '''
                window.filterTable = function() {
                    var faculty_name = document.getElementById('faculty').value
                    console.log("hahaha");
                    var all_rows = Array.prototype.slice.call(document.querySelectorAll('tbody tr'));
                    all_rows = all_rows.slice(1,);
                    console.log('hahahah2');

                    for(var i = 0; i < all_rows.length; i++) {
                        var all_tds = Array.prototype.slice.call(all_rows[i].querySelectorAll("td"));
                        var td_faculty_name = (all_tds[6].textContent.split(' - '))[1];

                        if(td_faculty_name.includes(faculty_name.toUpperCase())) {
                            console.log('hahahah3');
                            all_rows[i].style.display = "";
                            continue;
                        }
                        else {
                            console.log('hahaha4');
                            all_rows[i].style.display = "none";
                        }
                    };
                    document.body.setAttribute("faculty_name", faculty_name);
                }
                document.getElementById('getSlotIdForCoursePage').style.display = 'none';
                document.querySelector('#getFacultyForCoursePage label').outerHTML = '<font color= "red">' + document.querySelector('#getFacultyForCoursePage label').outerHTML + '</font>'

                var faculty_selector_parent = document.getElementById('faculty').parentNode
                faculty_selector_parent.innerHTML = "<input placeholder = 'Enter name of the faculty' onkeyup = 'filterTable()' class = 'form-control' id = 'faculty'>";

        '''

    browser.execute_script(js)

    js = '''
                window.filterTable = function() {
                    var faculty_name = document.getElementById('faculty').value;
                    console.log("hahaha");
                    var all_rows = Array.prototype.slice.call(document.querySelectorAll('tbody tr'));
                    all_rows = all_rows.slice(1,);
                    console.log('hahahah2');

                    for(var i = 0; i < all_rows.length; i++) {
                        var all_tds = Array.prototype.slice.call(all_rows[i].querySelectorAll("td"));
                        var td_faculty_name = (all_tds[6].textContent.split(' - '))[1];

                        if(td_faculty_name.includes(faculty_name.toUpperCase())) {
                            console.log('hahahah3');
                            all_rows[i].style.display = "";
                            continue;
                        }
                        else {
                            console.log('hahaha4');
                            all_rows[i].style.display = "none";
                        }
                    }
                    document.body.setAttribute("faculty_name", faculty_name);
                };

            document.getElementById('courseCode').onchange = function() {
                            getSlotIdForCoursePage('courseCode','getSlotIdForCoursePage','source');
                            setTimeout(function() {
                                    document.getElementById('getSlotIdForCoursePage').style.display = 'none';
                                    document.querySelector('#getFacultyForCoursePage label').outerHTML = '<font color= "red">' + document.querySelector('#getFacultyForCoursePage label').outerHTML + '</font>';
                                    var faculty_selector_parent = document.getElementById('faculty').parentNode;
                                    faculty_selector_parent.innerHTML = "<input placeholder = 'Enter name of the faculty' onkeyup = 'filterTable()' class = 'form-control' id = 'faculty'>";
                            }, 3500);
                        };
            '''

    js2 = '''
            alert('Download for the exam to follow completed, PRESS OK and go to the command prompt/terminal to continue/quit. ');
        '''

    def find_download_element():
        try:
            time.sleep(1) # sleep so that the course material gets loaded by then if the button to view the page is clicked
            course_plan_download_elem = browser.find_element_by_css_selector('a[href="/vtop/academics/common/coursePlanReport/"]')
            # print('False')
            return False
        except NoSuchElementException:
            # print('True')
            return True

    #21. Create download thread, complete a download and then take user response whether or not the user wants to download more files
    while True:
        while find_download_element():
            browser.execute_script(js)

        downloader_thread = threading.Thread(target = download_course_materials, args = [browser])
        downloader_thread.start()
        downloader_thread.join()
        browser.execute_script(js2)
        resp = input('Do you want to download for other courses?(y or n) ')
        resp = resp.lower()
        if resp == 'y' or resp == 'yes':
            back_btn = browser.find_element_by_css_selector('#back')
            back_btn.click()
            waiting.until(EC.presence_of_element_located((By.ID, 'semesterSubId')))
            print('Choose Semester Name and Course from the dropdown on the page.')
            continue
        else:
            browser.quit()

except NoSuchWindowException:
    print('Either the browser is closed or the Authorization failed! Do comeback!')
    logging.debug('Browser closed/Authorization failed')
