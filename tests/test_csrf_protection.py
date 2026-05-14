from pathlib import Path

from app import create_app


def extract_post_forms(template_text):
    lower = template_text.lower()
    forms = []
    start = 0

    while True:
        form_start = lower.find("<form", start)
        if form_start == -1:
            break

        form_end = lower.find("</form>", form_start)
        if form_end == -1:
            break

        form_block = template_text[form_start:form_end]
        if 'method="post"' in form_block.lower() or "method='post'" in form_block.lower():
            forms.append(form_block)

        start = form_end + len("</form>")

    return forms


def test_csrf_extension_is_registered_in_development_app():
    app = create_app("development")

    assert "csrf" in app.extensions


def test_testing_config_disables_csrf_for_pytest_client_posts():
    app = create_app("testing")

    assert app.config["WTF_CSRF_ENABLED"] is False


def test_plain_post_forms_include_csrf_token_or_flask_wtf_hidden_tag():
    template_dir = Path("app/templates")
    checked_forms = 0

    for template_path in template_dir.glob("*.html"):
        text = template_path.read_text()
        post_forms = extract_post_forms(text)

        for form in post_forms:
            checked_forms += 1
            assert (
                "csrf_token" in form
                or "hidden_tag()" in form
                or ".hidden_tag()" in form
            ), f"Missing CSRF token in {template_path}"

    assert checked_forms >= 1


def test_csrf_javascript_helper_exists_for_frontend_ajax():
    csrf_js = Path("static/js/csrf.js")

    assert csrf_js.exists()

    text = csrf_js.read_text()

    assert "X-CSRFToken" in text
    assert "window.fetch" in text
    assert "getCsrfToken" in text


def test_dashboard_plain_post_forms_render_csrf_token(client):
    client.post(
        "/signup",
        data={
            "username": "csrfuser",
            "email": "csrfuser@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b'name="csrf_token"' in response.data
