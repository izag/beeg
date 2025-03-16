import json
from tbselenium.tbdriver import TorBrowserDriver
from selenium.webdriver.common.by import By


if __name__ == "__main__":
    with TorBrowserDriver(tbb_fx_binary_path="C:\\Users\\Gregory\\Desktop\\TorBrowser\\Browser\\firefox.exe",
                          tbb_profile_path="C:\\Users\\Gregory\\Desktop\\TorBrowser\\Browser\\TorBrowser\\Data\\Browser\\profile.default\\") as driver:
        driver.get('view-source:https://www.chaturbate.com/api/ts/roomlist/room-list/')
        content = driver.page_source
        content = driver.find_element(By.TAG_NAME, 'pre').text
        print(json.loads(content))