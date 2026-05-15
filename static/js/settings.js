const privacyForm = document.getElementById("privacy-form");
const privacyToggle = document.getElementById("privacy-toggle");

if (privacyForm && privacyToggle) {
	privacyToggle.addEventListener("change", () => {
		privacyForm.submit();
	});
}