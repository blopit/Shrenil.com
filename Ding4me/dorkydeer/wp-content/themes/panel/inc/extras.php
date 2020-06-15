<?php
/**
 * Custom functions that act independently of the theme templates
 *
 * Eventually, some of the functionality here could be replaced by core features
 *
 * @package Panel
 */

/**
 * Get our wp_nav_menu() fallback, wp_page_menu(), to show a home link.
 */
function panel_page_menu_args( $args ) {
	$args['show_home'] = true;
	return $args;
}
add_filter( 'wp_page_menu_args', 'panel_page_menu_args' );

/**
 * Adds custom classes to the array of body classes.
 */
function panel_body_classes( $classes ) {

	// Adds a class of group-blog to blogs with more than 1 published author
	if ( is_multi_author() )
		$classes[] = 'group-blog';

	$header_image = get_header_image();
	if ( ! empty( $header_image ) || ( '' != get_the_post_thumbnail() && 'jetpack-comic' != get_post_type() && ! is_front_page() && ! is_archive() && ! is_search() && ! is_home() ) )
		$classes[] = 'custom-header';

	return $classes;
}
add_filter( 'body_class', 'panel_body_classes' );

/**
 * Filter in a link to a content ID attribute for the next/previous image links on image attachment pages
 */
function panel_enhanced_image_navigation( $url, $id ) {
	if ( ! is_attachment() && ! wp_attachment_is_image( $id ) )
		return $url;

	$image = get_post( $id );
	if ( ! empty( $image->post_parent ) && $image->post_parent != $id )
		$url .= '#main';

	return $url;
}
add_filter( 'attachment_link', 'panel_enhanced_image_navigation', 10, 2 );

/**
 * Filters wp_title to print a neat <title> tag based on what is being viewed.
 */
function panel_wp_title( $title, $sep ) {
	global $page, $paged;

	if ( is_feed() )
		return $title;

	// Add the blog name
	$title .= get_bloginfo( 'name' );

	// Add the blog description for the home/front page.
	$site_description = get_bloginfo( 'description', 'display' );
	if ( $site_description && ( is_home() || is_front_page() ) )
		$title .= " $sep $site_description";

	// Add a page number if necessary:
	if ( $paged >= 2 || $page >= 2 )
		$title .= " $sep " . sprintf( __( 'Page %s', 'panel' ), max( $paged, $page ) );

	return $title;
}
add_filter( 'wp_title', 'panel_wp_title', 10, 2 );

/**
 *	Customize excerpts more tag
 */
function panel_excerpt_more( $more ) {
	return '... <a class="more-link" href="'. esc_url( get_permalink() ) . '">' . sprintf( __( 'Read More <span class="screen-reader-text"> in %1$s</span>', 'panel' ), esc_attr( strip_tags( get_the_title() ) ) ) . '</a>';
}
add_filter( 'excerpt_more', 'panel_excerpt_more' );