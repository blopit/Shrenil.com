<?php
/**
 * Custom template tags for this theme.
 *
 * Eventually, some of the functionality here could be replaced by core features
 *
 * @package Panel
 */

if ( ! function_exists( 'panel_content_nav' ) ) :
/**
 * Display navigation to next/previous pages when applicable
 */
function panel_content_nav( $nav_id ) {
	global $wp_query, $post;

	// Don't print empty markup on single pages if there's nowhere to navigate.
	if ( ! 'jetpack-comic' == get_post_type() || is_single() ) {
		$previous = ( is_attachment() ) ? get_post( $post->post_parent ) : get_adjacent_post( false, '', true );
		$next = get_adjacent_post( false, '', false );
	}

	// Don't print empty markup in archives if there's only one page.
	if ( $wp_query->max_num_pages < 2 && ! 'jetpack-comic' == get_post_type() && ( is_home() || is_archive() || is_search() ) )
		return;

	$nav_class = ( is_single() ) ? 'navigation-post' : 'navigation-paging';

	if ( 'jetpack-comic' == get_post_type() )
		$nav_class .= ' navigation-comic';

	?>
	<nav role="navigation" id="<?php echo esc_attr( $nav_id ); ?>" class="<?php echo $nav_class; ?> clear">
		<h1 class="screen-reader-text"><?php esc_html_e( 'Post navigation', 'panel' ); ?></h1>

	<?php if ( 'jetpack-comic' == get_post_type() && ( is_single() || is_front_page() ) ) : //navigation links for comics ?>

		<div class="nav-first"><a href="<?php echo esc_url( panel_get_first_post_link( array( 'post_type' => 'jetpack-comic' ) ) ); ?>"><span class="meta-nav"><?php echo esc_html_x( '&laquo;&nbsp;First', 'First comic link', 'panel' ); ?></span></a></div>
		<div class="nav-previous"><?php previous_post_link( '%link', '<span class="meta-nav">&larr;</span>&nbsp;' . esc_html_x( 'Prev', 'Previous comic link', 'panel' ) ); ?></div>
		<div class="nav-random"><a href="<?php echo esc_url( home_url( '/' ) ); ?>comic/?random"><span class="meta-nav"><?php echo esc_html_x( 'Random', 'Random comic link', 'panel' ) ?></span></a></div>
		<div class="nav-next"><?php next_post_link( '%link', esc_html_x( 'Next', 'Next comic link', 'panel' ) . '&nbsp;<span class="meta-nav">&rarr;</span>' ); ?></div>
		<div class="nav-last"><a href="<?php echo esc_url( panel_get_last_post_link( array( 'post_type' => 'jetpack-comic' ) ) ); ?>"><span class="meta-nav"><?php echo esc_html_x( 'Latest&nbsp;&raquo;', 'Latest comic link', 'panel' ); ?></span></a></div>

	<?php elseif ( is_single() ) : // navigation links for single posts ?>

		<?php previous_post_link( '<div class="nav-previous">%link</div>', '<span class="meta-nav">' . esc_html_x( '&larr;', 'Previous post link', 'panel' ) . '</span> %title' ); ?>
		<?php next_post_link( '<div class="nav-next">%link</div>', '%title <span class="meta-nav">' . esc_html_x( '&rarr;', 'Next post link', 'panel' ) . '</span>' ); ?>

	<?php elseif ( $wp_query->max_num_pages > 1 && ( is_home() || is_archive() || is_search() ) ) : // navigation links for home, archive, and search pages ?>

		<?php if ( get_next_posts_link() ) : ?>
		<div class="nav-previous"><?php next_posts_link( __( '<span class="meta-nav">&larr;</span> Older posts', 'panel' ) ); ?></div>
		<?php endif; ?>

		<?php if ( get_previous_posts_link() ) : ?>
		<div class="nav-next"><?php previous_posts_link( __( 'Newer posts <span class="meta-nav">&rarr;</span>', 'panel' ) ); ?></div>
		<?php endif; ?>

	<?php endif; ?>

	</nav><!-- #<?php echo esc_html( $nav_id ); ?> -->
	<?php
}
endif; // panel_content_nav

if ( ! function_exists( 'panel_comment' ) ) :
/**
 * Template for comments and pingbacks.
 *
 * Used as a callback by wp_list_comments() for displaying the comments.
 */
function panel_comment( $comment, $args, $depth ) {
	$GLOBALS['comment'] = $comment;

	if ( 'pingback' == $comment->comment_type || 'trackback' == $comment->comment_type ) : ?>

	<li id="comment-<?php comment_ID(); ?>" <?php comment_class(); ?>>
		<div class="comment-body">
			<?php esc_html_e( 'Pingback:', 'panel' ); ?> <?php comment_author_link(); ?> <?php edit_comment_link( __( 'Edit', 'panel' ), '<span class="sep"> ~ </span><span class="edit-link">', '</span>' ); ?>
		</div>

	<?php else : ?>

	<li id="comment-<?php comment_ID(); ?>" <?php comment_class( empty( $args['has_children'] ) ? '' : 'parent' ); ?>>
		<article id="div-comment-<?php comment_ID(); ?>" class="comment-body">
			<footer class="comment-meta">
				<div class="comment-author vcard">
					<?php if ( 0 != $args['avatar_size'] ) echo get_avatar( $comment, $args['avatar_size'] ); ?>
					<?php printf( '<cite class="fn">%s</cite>', get_comment_author_link() ); ?>
				</div><!-- .comment-author -->

				<div class="comment-metadata">
					<a href="<?php echo esc_url( get_comment_link( $comment->comment_ID ) ); ?>">
						<time datetime="<?php comment_time( 'c' ); ?>">
							<?php printf( esc_html_x( '%1$s at %2$s', '1: date, 2: time', 'panel' ), get_comment_date(), get_comment_time() ); ?>
						</time>
					</a>
					<?php edit_comment_link( __( 'Edit', 'panel' ), '<span class="sep"> ~ </span><span class="edit-link">', '</span>' ); ?>
				</div><!-- .comment-metadata -->

				<?php if ( '0' == $comment->comment_approved ) : ?>
				<p class="comment-awaiting-moderation"><?php esc_html_e( 'Your comment is awaiting moderation.', 'panel' ); ?></p>
				<?php endif; ?>
			</footer><!-- .comment-meta -->

			<div class="comment-content">
				<?php comment_text(); ?>
			</div><!-- .comment-content -->

			<div class="reply">
				<?php comment_reply_link( array_merge( $args, array( 'add_below' => 'div-comment', 'depth' => $depth, 'max_depth' => $args['max_depth'] ) ) ); ?>
			</div><!-- .reply -->
		</article><!-- .comment-body -->

	<?php
	endif;
}
endif; // ends check for panel_comment()

if ( ! function_exists( 'panel_the_attached_image' ) ) :
/**
 * Prints the attached image with a link to the next attached image.
 */
function panel_the_attached_image() {
	$post                = get_post();
	$attachment_size     = apply_filters( 'panel_attachment_size', array( 1200, 1200 ) );
	$next_attachment_url = wp_get_attachment_url();

	/**
	 * Grab the IDs of all the image attachments in a gallery so we can get the
	 * URL of the next adjacent image in a gallery, or the first image (if
	 * we're looking at the last image in a gallery), or, in a gallery of one,
	 * just the link to that image file.
	 */
	$attachment_ids = get_posts( array(
		'post_parent'    => $post->post_parent,
		'fields'         => 'ids',
		'numberposts'    => -1,
		'post_status'    => 'inherit',
		'post_type'      => 'attachment',
		'post_mime_type' => 'image',
		'order'          => 'ASC',
		'orderby'        => 'menu_order ID'
	) );

	// If there is more than 1 attachment in a gallery...
	if ( count( $attachment_ids ) > 1 ) {
		foreach ( $attachment_ids as $attachment_id ) {
			if ( $attachment_id == $post->ID ) {
				$next_id = current( $attachment_ids );
				break;
			}
		}

		// get the URL of the next image attachment...
		if ( $next_id )
			$next_attachment_url = get_attachment_link( $next_id );

		// or get the URL of the first image attachment.
		else
			$next_attachment_url = get_attachment_link( array_shift( $attachment_ids ) );
	}

	printf( '<a href="%1$s" title="%2$s" rel="attachment">%3$s</a>',
		esc_url( $next_attachment_url ),
		the_title_attribute( array( 'echo' => false ) ),
		wp_get_attachment_image( $post->ID, $attachment_size )
	);
}
endif;

if ( ! function_exists( 'panel_posted_on' ) ) :
/**
 * Prints HTML with meta information for the current post-date/time and author.
 */
function panel_posted_on() {
	if ( is_sticky() && ! is_single() ) {
		printf( __( '<a href="%1$s" title="%2$s" rel="bookmark" class="entry-date">Featured</a>', 'panel' ),
			esc_url( get_permalink() ),
			esc_attr( get_the_time() )
		);
	} else {
		printf( __( '<a href="%1$s" title="%2$s" rel="bookmark" class="entry-date"><time class="entry-date" datetime="%3$s">%4$s</time></a>', 'panel' ),
			esc_url( get_permalink() ),
			esc_attr( get_the_time() ),
			esc_attr( get_the_date( 'c' ) ),
			esc_html( get_the_date() )
		);
	}
}
endif;

if ( ! function_exists( 'panel_posted_by' ) ) :
/**
 * Prints HTML with meta information for the current post-date/time and author.
 */
function panel_posted_by() {

	printf( __( '<span class="byline"><span class="sep"> ~ </span><span class="author vcard"><a class="url fn n" href="%1$s" title="%2$s" rel="author">%3$s</a></span></span>', 'panel' ),
		esc_url( get_author_posts_url( get_the_author_meta( 'ID' ) ) ),
		esc_attr( sprintf( __( 'View all posts by %s', 'panel' ), get_the_author() ) ),
		get_the_author()
	);

}
endif;
/**
 * Returns true if a blog has more than 1 category
 */
function panel_categorized_blog() {
	if ( false === ( $all_the_cool_cats = get_transient( 'all_the_cool_cats' ) ) ) {
		// Create an array of all the categories that are attached to posts
		$all_the_cool_cats = get_categories( array(
			'hide_empty' => 1,
		) );

		// Count the number of categories that are attached to the posts
		$all_the_cool_cats = count( $all_the_cool_cats );

		set_transient( 'all_the_cool_cats', $all_the_cool_cats );
	}

	if ( '1' != $all_the_cool_cats ) {
		// This blog has more than 1 category so panel_categorized_blog should return true
		return true;
	} else {
		// This blog has only 1 category so panel_categorized_blog should return false
		return false;
	}
}

/**
 * Flush out the transients used in panel_categorized_blog
 */
function panel_category_transient_flusher() {
	// Like, beat it. Dig?
	delete_transient( 'all_the_cool_cats' );
}
add_action( 'edit_category', 'panel_category_transient_flusher' );
add_action( 'save_post', 'panel_category_transient_flusher' );

/**
 * Link to the first post in a series.
 *
 * @param string $format
 * @param array $args
 */
function panel_get_first_post_link( $args = array() ) {
	$args['order'] = 'ASC';

	return panel_get_bookend_post_link( $args );
}

/**
 * Link to the last post in a series.
 *
 * @param string $format
 * @param array $args
 */
function panel_get_last_post_link( $args = array() ) {
	$args['order'] = 'DESC';

	return panel_get_bookend_post_link( $args );
}

/**
 * Get the first or last link in a series.
 *
 * @param array $args
 */
function panel_get_bookend_post_link( $args = array() ) {
	$args['orderby'] = 'date';
	$args['posts_per_page'] = 1;

	$q = new WP_Query( $args );

	if ( $q->have_posts() )
		return get_permalink( $q->next_post()->ID );

	return '';
}
