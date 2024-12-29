(function($) {
    'use strict';

    // Simple accordion plugin
    $.fn.simpleAccordion = function() {
        this.on("click", ".accordion__control", function() {
            $(this).toggleClass("accordion__control--active").next().slideToggle();
        });
        return this;
    };

    // Document ready handler
    $(document).ready(function() {
        // Initialize accordion
        $(".accordion").simpleAccordion();
        $(".accordion__control").next().slideUp();
        
        // Initialize emoji conversion
        if (typeof joypixels !== 'undefined') {
            $('.convert-emoji').each(function() {
                var $this = $(this);
                var text = $this.html();
                $this.html(joypixels.shortnameToImage(text));
            });
        }

        // Initialize boxlayout if available
        if (typeof Boxlayout !== 'undefined') {
            Boxlayout.init();
        }
    });
})(jQuery);