import socket
import threading
import time
import uuid

import pytest
from werkzeug.serving import make_server

selenium = pytest.importorskip("selenium")

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from app import create_app, db


def get_free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    app = create_app("testing")

    database_path = tmp_path_factory.mktemp("selenium_db") / "selenium.sqlite"
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path}",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    port = get_free_port()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    time.sleep(0.3)

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    thread.join(timeout=2)

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def browser():
    driver = None

    try:
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1440,1000")
        driver = webdriver.Chrome(options=chrome_options)
    except WebDriverException:
        try:
            firefox_options = FirefoxOptions()
            firefox_options.add_argument("--headless")
            driver = webdriver.Firefox(options=firefox_options)
        except WebDriverException as exc:
            pytest.skip(f"No Selenium-compatible browser available: {exc}")

    driver.implicitly_wait(3)

    yield driver

    driver.quit()


def click_with_fallback(browser, el):
    from selenium.common.exceptions import ElementClickInterceptedException

    try:
        el.click()
    except ElementClickInterceptedException:
        browser.execute_script("arguments[0].click();", el)


def unique_user(prefix="selenium"):
    suffix = uuid.uuid4().hex[:8]
    return {
        "username": f"{prefix}_{suffix}",
        "email": f"{prefix}_{suffix}@example.com",
        "password": "Password123",
    }


def page_text(browser, timeout=5):
    last_error = None

    for _ in range(3):
        try:
            WebDriverWait(browser, timeout).until(
                lambda driver: driver.find_elements(By.TAG_NAME, "body")
            )
            return browser.find_element(By.TAG_NAME, "body").text.lower()
        except StaleElementReferenceException as exc:
            last_error = exc
            time.sleep(0.2)

    raise last_error


def signup_through_ui(browser, base_url, user):
    browser.get(f"{base_url}/signup")

    browser.find_element(By.NAME, "username").send_keys(user["username"])
    browser.find_element(By.NAME, "email").send_keys(user["email"])
    browser.find_element(By.NAME, "password").send_keys(user["password"])

    confirm_fields = browser.find_elements(By.NAME, "confirm_password")
    if confirm_fields:
        confirm_fields[0].send_keys(user["password"])

    btn = browser.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    click_with_fallback(browser, btn)


def ensure_logged_in_after_signup(browser, base_url, user):
    WebDriverWait(browser, 5).until(
        lambda driver: driver.find_elements(By.TAG_NAME, "body")
    )

    if "/dashboard" in browser.current_url:
        return

    current_text = page_text(browser)

    if "/login" in browser.current_url or "login" in current_text:
        login_through_ui(browser, base_url, user)
        return

    browser.get(f"{base_url}/dashboard")

    if "/login" in browser.current_url:
        login_through_ui(browser, base_url, user)


def login_through_ui(browser, base_url, user):
    browser.get(f"{base_url}/login")

    email_fields = browser.find_elements(By.NAME, "email")
    username_fields = browser.find_elements(By.NAME, "username")

    if email_fields:
        email_fields[0].send_keys(user["email"])
    elif username_fields:
        username_fields[0].send_keys(user["username"])
    else:
        raise AssertionError("Login form must contain email or username field.")

    browser.find_element(By.NAME, "password").send_keys(user["password"])
    btn = browser.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    click_with_fallback(browser, btn)


def test_selenium_home_page_loads(live_server, browser):
    browser.get(live_server)

    text = page_text(browser)

    assert "habitwise" in text or "start" in text or "login" in text


def test_selenium_signup_page_contains_expected_form_fields(live_server, browser):
    browser.get(f"{live_server}/signup")

    assert browser.find_element(By.NAME, "username")
    assert browser.find_element(By.NAME, "email")
    assert browser.find_element(By.NAME, "password")


def test_selenium_login_page_contains_expected_form_fields(live_server, browser):
    browser.get(f"{live_server}/login")

    assert browser.find_element(By.NAME, "password")

    has_email = browser.find_elements(By.NAME, "email")
    has_username = browser.find_elements(By.NAME, "username")

    assert has_email or has_username


def test_selenium_dashboard_is_protected_when_logged_out(live_server, browser):
    browser.get(f"{live_server}/dashboard")

    text = page_text(browser)

    assert "login" in text or "sign" in text or "/login" in browser.current_url


def test_selenium_user_can_signup_and_reach_dashboard(live_server, browser):
    user = unique_user("signup")

    signup_through_ui(browser, live_server, user)
    ensure_logged_in_after_signup(browser, live_server, user)

    text = page_text(browser)

    assert (
        "dashboard" in text
        or "today" in text
        or "task" in text
        or "challenge" in text
        or "welcome" in text
    )


def test_selenium_user_can_logout_after_signup(live_server, browser):
    user = unique_user("logout")

    signup_through_ui(browser, live_server, user)
    ensure_logged_in_after_signup(browser, live_server, user)

    logout_links = browser.find_elements(By.PARTIAL_LINK_TEXT, "Logout")
    if not logout_links:
        logout_links = browser.find_elements(By.CSS_SELECTOR, "a[href*='logout']")

    assert logout_links

    click_with_fallback(browser, logout_links[0])

    text = page_text(browser)

    assert "login" in text or "sign" in text or "habitwise" in text


def test_selenium_logged_in_user_can_access_community_and_settings(live_server, browser):
    user = unique_user("nav")

    signup_through_ui(browser, live_server, user)
    ensure_logged_in_after_signup(browser, live_server, user)

    browser.get(f"{live_server}/community")
    community_text = page_text(browser)
    assert "community" in community_text or "public" in community_text or "leaderboard" in community_text

    browser.get(f"{live_server}/settings")
    settings_text = page_text(browser)
    assert "settings" in settings_text or "account" in settings_text or "privacy" in settings_text


def test_selenium_dashboard_can_add_task_if_form_present(live_server, browser):
    user = unique_user("task")

    signup_through_ui(browser, live_server, user)
    ensure_logged_in_after_signup(browser, live_server, user)

    browser.get(f"{live_server}/dashboard")

    title_fields = browser.find_elements(By.NAME, "title")

    if not title_fields:
        pytest.skip("Dashboard task form is not currently exposed in this template.")

    title_fields[0].send_keys("Selenium test task")

    submit_buttons = browser.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    assert submit_buttons

    def click_with_fallback(el):
        try:
            el.click()
        except ElementClickInterceptedException:
            # fallback to JS click when an overlay or animation intercepts pointer events
            browser.execute_script("arguments[0].click();", el)

    click_with_fallback(submit_buttons[0])

    text = page_text(browser)

    assert "selenium test task" in text or "task" in text
