import socket
import threading
import time
import uuid
from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from werkzeug.serving import make_server

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
    from selenium import webdriver
    from selenium.common.exceptions import WebDriverException
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions

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


def unique_user(prefix="selenium"):
    suffix = uuid.uuid4().hex[:8]
    return {
        "username": f"{prefix}_{suffix}",
        "email": f"{prefix}_{suffix}@example.com",
        "password": "Password123",
    }


def page_text(browser, timeout=5):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import StaleElementReferenceException

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
    from selenium.webdriver.common.by import By

    browser.get(f"{base_url}/signup")

    browser.find_element(By.NAME, "username").send_keys(user["username"])
    browser.find_element(By.NAME, "email").send_keys(user["email"])
    browser.find_element(By.NAME, "password").send_keys(user["password"])

    confirm_fields = browser.find_elements(By.NAME, "confirm_password")
    if confirm_fields:
        confirm_fields[0].send_keys(user["password"])

    btn = browser.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    try:
        btn.click()
    except Exception:
        browser.execute_script("arguments[0].click();", btn)


def ensure_logged_in_after_signup(browser, base_url, user):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    WebDriverWait(browser, 5).until(
        lambda driver: driver.find_elements(By.TAG_NAME, "body")
    )

    if "/dashboard" in browser.current_url:
        return

    current_text = page_text(browser)

    if "/login" in browser.current_url or "login" in current_text:
        # fallback: do a login flow
        browser.get(f"{base_url}/login")
        email_fields = browser.find_elements(By.NAME, "email")
        username_fields = browser.find_elements(By.NAME, "username")

        if email_fields:
            email_fields[0].send_keys(user["email"])
        elif username_fields:
            username_fields[0].send_keys(user["username"])

        browser.find_element(By.NAME, "password").send_keys(user["password"])
        btn = browser.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        try:
            btn.click()
        except Exception:
            browser.execute_script("arguments[0].click();", btn)
        return

    browser.get(f"{base_url}/dashboard")

    if "/login" in browser.current_url:
        browser.get(f"{base_url}/login")


def test_capture_before_click(live_server, browser):
    """Reproduce add-task flow, save screenshot and element info before clicking."""
    out_dir = Path("selenium_screenshots")
    out_dir.mkdir(exist_ok=True)
    logs = Path("test_failure_logs")
    logs.mkdir(exist_ok=True)

    user = unique_user("debug")

    signup_through_ui(browser, live_server, user)
    ensure_logged_in_after_signup(browser, live_server, user)

    browser.get(f"{live_server}/dashboard")

    title_fields = browser.find_elements(By.NAME, "title")
    if not title_fields:
        pytest.skip("Dashboard task form not present")

    title_fields[0].send_keys("Selenium debug task")

    submit_buttons = browser.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    assert submit_buttons

    btn = submit_buttons[0]

    # small wait to allow any overlays/animations to settle
    time.sleep(0.5)

    # save screenshot
    screenshot_path = out_dir / "before_click.png"
    browser.save_screenshot(str(screenshot_path))

    # compute center coordinates of the button and capture the element at that point
    get_info = (
        "const el = arguments[0];"
        "const r = el.getBoundingClientRect();"
        "const cx = Math.round(r.left + r.width/2);"
        "const cy = Math.round(r.top + r.height/2);"
        "const hit = document.elementFromPoint(cx, cy);"
        "return {cx: cx, cy: cy, hit_tag: hit ? hit.tagName : null, hit_classes: hit ? hit.className : null, hit_outer: hit ? hit.outerHTML : null};"
    )

    info = browser.execute_script(get_info, btn)

    info_path = logs / "element_at_click.txt"
    info_path.write_text(str(info), encoding="utf-8")

    # also save page source for inspection
    (logs / "before_click_page.html").write_text(browser.page_source, encoding="utf-8")

    # fail intentionally to keep artifacts visible in pytest output (or assert True to pass)
    assert screenshot_path.exists()
