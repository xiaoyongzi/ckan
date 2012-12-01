(function ($) {
  $('.module-info-overlay').addClass('fade-in')
  .find('a.close').click(function() {
    $('.module-info-overlay').removeClass('fade-in');
  });
}(jQuery));
