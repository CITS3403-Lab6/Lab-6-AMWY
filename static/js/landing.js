document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center'});
    }

    setTimeout(() => {
      target.classList.add('section-highlight');

      setTimeout(() => {
        target.classList.remove('section-highlight');
      }, 1500);

    }, 400);
  });
});