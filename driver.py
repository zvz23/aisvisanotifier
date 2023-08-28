import os
import sys
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from seleniumwire.undetected_chromedriver.v2 import Chrome, ChromeOptions

    
def get_driver(profile_name: str, headless=True):
    profile_path = None
    options = ChromeOptions()
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.accept_insecure_certs = True
    # options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    # options.set_capability('goog:perfLoggingPref', {'enableNetwork': True})
    driver_executable_path = None
    if sys.platform == 'linux' or sys.platform == 'linux2':
        profile_path = os.path.expanduser('~/.config/google-chrome', profile_name)
    elif sys.platform == 'win32' or sys.platform == 'win64':
        profile_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data', profile_name)
        driver_executable_path = os.path.join('chromedrivers', 'windows.exe')
    elif sys.platform == 'darwin':
        profile_path = os.path.expanduser('~/Library/Application Support/Google/Chrome', profile_name)
        driver_executable_path = os.path.join('chromedrivers', 'mac')
    return Chrome(options=options, user_data_dir=profile_path, driver_executable_path=driver_executable_path, headless=headless)
