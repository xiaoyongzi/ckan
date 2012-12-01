(function ($) {
  $('.module-info-overlay').addClass('fade-in');
  $('section.hero-secondary a.close').click(function() {
    $('.module-info-overlay').removeClass('fade-in');
  });
}(jQuery));
