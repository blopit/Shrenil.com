/**
 * boxlayout.js v1.0.0
 * http://www.codrops.com
 */
var Boxlayout = (function() {
    var $el = $('#bl-main'),
        $sections = $el.children('section'),
        $sectionWork = $('#bl-work-section'),
        transEndEventNames = {
            'WebkitTransition': 'webkitTransitionEnd',
            'MozTransition': 'transitionend',
            'OTransition': 'oTransitionEnd',
            'msTransition': 'MSTransitionEnd',
            'transition': 'transitionend'
        },
        transEndEventName = transEndEventNames[Modernizr.prefixed('transition')],
        supportTransitions = Modernizr.csstransitions;

    function init() {
        initEvents();
    }

    function initEvents() {
        $sections.each(function() {
            var $section = $(this);

            // expand the clicked section and scale down the others
            $section.on('click', function() {
                if (!$section.data('open')) {
                    $section.data('open', true).addClass('bl-expand bl-expand-top');
                    $el.addClass('bl-expand-item');
                }
            }).find('span.fa-times').on('click', function() {
                // close the expanded section and scale up the others
                $section.data('open', false).removeClass('bl-expand').on(transEndEventName, function(event) {
                    if (!$(event.target).is('section')) return false;
                    $(this).off(transEndEventName).removeClass('bl-expand-top');
                });

                if (!supportTransitions) {
                    $section.removeClass('bl-expand-top');
                }

                $el.removeClass('bl-expand-item');
                return false;
            });
        });
    }

    return { init: init };
})(); 