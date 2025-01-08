from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd

driver = webdriver.Chrome()

# Load the website
def load_homepage():
    driver.get("https://www.cabinns.com/")
    driver.maximize_window()

# location name with simulated human typing
def enter_location_name(location_name):
    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="js-search-autocomplete"]'))
    )
    search_input.clear()
    for letter in location_name:
        search_input.send_keys(letter)
        time.sleep(1)

# suggestions based on the location entered
def get_suggestions():
    time.sleep(2)  # Give suggestions time to load
    suggestions = WebDriverWait(driver, 20).until(
        EC.visibility_of_all_elements_located((By.XPATH, '//*[@id="js-search-items"]/li'))
    )
    print(f"Number of suggestions: {len(suggestions)}")
    return suggestions

# a random suggestion from the list
def select_random_suggestion(suggestions):
    index = random.randint(0, len(suggestions) - 1)
    selected_suggestion = suggestions[index]
    print(f"Selected index: {index}")
    span_tag = selected_suggestion.find_element(By.TAG_NAME, 'span')
    selected_location = span_tag.text
    print(f"Selected location: {selected_location}")
    return selected_suggestion, selected_location

# Getiing the data-id attribute to determine if the suggestion is hybrid
def get_data_id(selected_suggestion, index):
    selected_suggestion = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, f'//*[@id="js-search-items"]/li[{index + 1}]'))
    )
    data_id = selected_suggestion.get_attribute('data-id')
    is_hybrid = data_id is not None and data_id != ""
    print(f"Data ID: {data_id}")
    return data_id, is_hybrid

# Click on the suggestion
def click_suggestion(selected_suggestion):
    actions = ActionChains(driver)
    actions.move_to_element(selected_suggestion).perform()
    
    # Try to click, and use JavaScript as a fallback
    try:
        selected_suggestion.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", selected_suggestion)

# handling the date picker if it appears
def close_date_picker():
    try:
        date_picker_close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="js-date-picker-close"]'))
        )
        date_picker_close_button.click()
    except TimeoutException:
        pass

# Clicking on the search button to perform the search
def click_search_button():
    try:
        # Close the date picker if it's visible and blocking the button
        close_date_picker()

        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="js-btn-search"]'))
        )
        search_button.click()
    except ElementClickInterceptedException:
        # If the click is intercepted, use JavaScript to force the click
        driver.execute_script("arguments[0].click();", search_button)

# Validate the landing page (checking script data and URL)
def validate_landing_page(data_id, is_hybrid):
    time.sleep(20)
    current_url = driver.current_url

    try:
        script_data = driver.execute_script("return ScriptData.pageLayout;")
        contains_refine = "Refine" in script_data
        contains_hybrid = "Hybrid" in script_data
    except:
        contains_refine = False
        contains_hybrid = False
    
    # Check if data-id is part of the current URL
    is_data_id_in_url = data_id in current_url if is_hybrid else False
    print(f"Is Data ID in URL: {is_data_id_in_url}")

    # Initialize the url_comment variable to avoid UnboundLocalError
    url_comment = ""

    if data_id and data_id in current_url:
        url_comment = f"Expected: 'Hybrid', Landed: {current_url} (Hybrid match)"
    elif not data_id:
        url_comment = f"Expected: 'Refine', Landed: {current_url}"
    else:
        url_comment = f"Landed: {current_url} (No specific expectation matched)"

    # Determine test result
    if (not data_id and contains_refine) or (is_hybrid and contains_hybrid and is_data_id_in_url):
        test_result = "Pass"
    else:
        test_result = "Fail"

    return current_url, url_comment, test_result

# Main method to combine the other methods
def perform_search_and_validate(location_name):
    try:
        load_homepage()
        enter_location_name(location_name)
        suggestions = get_suggestions()
        selected_suggestion, selected_location = select_random_suggestion(suggestions)
        data_id, is_hybrid = get_data_id(selected_suggestion, suggestions.index(selected_suggestion))
        click_suggestion(selected_suggestion)
        close_date_picker()
        click_search_button()
        landing_page, url_comment, test_result = validate_landing_page(data_id, is_hybrid)

        return {
            "input_location": location_name,
            "selected_location": selected_location,
            "landing_page": url_comment,
            "test_result": test_result
        }

    except TimeoutException:
        print(f"Timeout: Suggestion list did not appear for location '{location_name}'")
        return {
            "input_location": location_name,
            "selected_location": "N/A",
            "landing_page": "N/A",
            "test_result": "Fail"
        }

# Example locations to test
locations = ["Finland", "Paris","India"]

# List to hold results
results = []

for location in locations:
    result = perform_search_and_validate(location)
    results.append(result)

print(results)
# Create a DataFrame and save results to CSV
df = pd.DataFrame(results)
df.to_csv("search_results.csv", index=False)

time.sleep(5)
driver.quit()

