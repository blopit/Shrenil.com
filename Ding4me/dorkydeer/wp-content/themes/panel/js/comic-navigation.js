jQuery( document ).ready( function( $ ) {

	if ( comicNavigationOptions.pjax && history.pushState ) {

		// Include a slug function here for future development or people to duck-punch.
		var doComicAnalytics = function( url ) {}

		// Just load the comic at the URL in question.
		// Used by `handleComicNavigation` and the `popstate` handler.
		var loadComic = function( url ) {
			$( '.entry-comic' ).addClass( 'loading' ).spin( 'large', '#000' ).load( url + ' .entry-comic > *', function( response ) {
				var $response = $( response ),
					$response_comments = $response.find( '#comments' ),
					$comments = $( '#comments' );
				$( this ).removeClass( 'loading' ).spin( false );

				// Update the page title:
				document.title = $response.filter( 'title' ).text();

				// Scroll up to top of page
				$(window).scrollTop(0);

				// Update the comments area:
				if ( $comments.length ) {
					$comments.replaceWith( $response_comments.clone() );
					$( '#comments .comment-textarea' ).prepend( $response_comments.find( '.comment-textarea label' ) );
					highlander_expando_javascript();
					HighlanderComments.init();
				}
			} );
		}

		// Handle the manual activation of the comic navigation buttons.
		var handleComicNavigation = function( event ) {
			// If we're already loading something, don't double-load.
			if ( $( event.target ).closest( '.entry-comic' ).hasClass( 'loading' ) ) {
				return;
			}

			var link = $( event.target ).closest( 'a' ),
				href = link.length ? link[0].href : false;

			// If we don't have a URL to work off of, treat the click normally.
			if( ! href ) {
				return;
			}

			// Update the URL, load the new block, and do any relevant analytics.
			history.pushState( { path : href }, '', href );
			loadComic( href );
			doComicAnalytics( href );

			event.preventDefault();
		}

		// Catch clicks on the navigation buttons.
		$( '.entry-comic' ).on( 'click', '.navigation-comic a', handleComicNavigation );

		// Catch back and forward history buttons.
		// @todo: Find a good way to cache the contents so it doesn't keep firing off a new GET request each time?
		$( window ).bind( 'popstate', function( event ) {
			if ( event.originalEvent.state ) {
				loadComic( event.originalEvent.state.path );
			}
		} );

		// Shove in the path of the initial page, so we have something to come back to.
		history.replaceState( { path: window.location.href }, '' );

	}

	// Regardless of whether the visitor has history.pushState, let's
	// let them navigate with their back and forward buttons.
	$( document ).keydown( function( event ) {
		// Don't do anything if the user is focused in an input field or textarea.
		var tagName = event.target.tagName.toLowerCase();
		if ( 'input' == tagName || 'textarea' == tagName ) {
			return;
		}

		switch ( event.which ) {
			case 37: // left
				$( '.navigation-comic .nav-previous a' ).click();
				break;
			case 39: // right
				$( '.navigation-comic .nav-next a' ).click();
				break;
			default:
				return;
		}

		// If the switch caught something and didn't return, prevent the keypress from running its course.
		event.preventDefault();
	} );

} );
