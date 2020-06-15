<?php
/**
 * Jetpack Compatibility File
 * See: http://jetpack.me/
 *
 * @package Panel
 */

function panel_jetpack_setup() {

	/**
	 * Add theme support for Infinite Scroll if no featured posts are set.
	 * See: http://jetpack.me/support/infinite-scroll/
	 */

	add_theme_support( 'infinite-scroll', array(
		'type'           => 'click',
		'container'      => 'content',
		'footer'         => 'main',
		'render'         => 'panel_infinite_scroll_render'
	) );

	/* Enable Social Links */
	add_theme_support( 'social-links', array(
		'facebook', 'twitter', 'tumblr',
	) );

	/* Enable Comics CPT */
	add_theme_support( 'jetpack-comic' );

	/**
	 * Jetpack: Enable Featured Content support for front page
	 */
	add_theme_support( 'featured-content', array(
		'featured_content_filter' => 'panel_get_featured_posts',
		'max_posts'               => 20,
	) );

}
add_action( 'after_setup_theme', 'panel_jetpack_setup' );

/*
 * We use a custom content-part.php for the home page
 */
function panel_infinite_scroll_render() {
	while( have_posts() ) {
		the_post();

		if ( is_front_page() ) :
			get_template_part( 'content', 'featured' );
		else :
			get_template_part( 'content', get_post_format() );
		endif;
	}
}

/*
 * This function stops infinite scroll if footer widgets are active, or if the sidebar
 * drops below the content in mobile view
 */
if ( function_exists( 'jetpack_is_mobile' ) ) :
	function panel_has_footer_widgets() {
		if ( is_active_sidebar( 'footer-sidebar-1' ) ||
			 is_active_sidebar( 'footer-sidebar-2' ) ||
			 is_active_sidebar( 'footer-sidebar-3' ) ||
			 ( is_active_sidebar( 'sidebar-1' ) && jetpack_is_mobile( '', true ) ) )
			return true;

		return false;
	}
	add_filter( 'infinite_scroll_has_footer_widgets', 'panel_has_footer_widgets' );
endif;

/*
 * Helper functions for Featured Content
 */
function panel_get_featured_posts() {
	return apply_filters( 'panel_get_featured_posts', array() );
}

function panel_has_featured_posts( $minimum = 1 ) {

	if ( is_paged() )
		return false;

	$minimum = absint( $minimum );
	$featured_posts = apply_filters( 'panel_get_featured_posts', array() );

	if ( ! is_array( $featured_posts ) )
		return false;

	if ( $minimum > count( $featured_posts ) )
		return false;

	return true;
}

/**
 * For comic CPTs, as we display the featured image properly,
 * regex it out of the content.  Don't do this for all themes,
 * as some themes may not display the featured image.
 */
function panel_strip_comic_image( $content ) {
	if ( class_exists( 'Jetpack_Comic' ) && ( Jetpack_Comic::POST_TYPE === get_post_type() ) && '' != get_the_post_thumbnail() ) {
		$image_url = wp_get_attachment_image_src( get_post_thumbnail_id(), 'full' );
		$image_url = $image_url[0];
		$image_url = str_replace( array( 'http://', 'https://' ), 'https?://', $image_url );
		$regex     = sprintf( '#<a href="%1$s"><img[^>]*? src="%1$s[^"]*" [^>]*?/></a>#', $image_url );
		$content   = preg_replace( $regex, '', $content );
	}

	return $content;
}
add_filter( 'the_content', 'panel_strip_comic_image' );