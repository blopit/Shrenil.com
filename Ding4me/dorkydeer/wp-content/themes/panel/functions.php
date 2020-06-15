<?php
/**
 * Readable functions and definitions
 *
 * @package Panel
 */

/**
 * Set the content width based on the theme's design and stylesheet.
 */
if ( ! isset( $content_width ) )
	$content_width = 750; /* pixels */

/**
 * Adjust the content width for comics & Full Width page template.
 */
function panel_set_content_width() {
	global $content_width;

	if ( is_front_page() || 'jetpack-comic' == get_post_type() ) {
		$content_width = 940;
	}
	else if ( is_page_template( 'nosidebar-page.php' ) ) {
		$content_width = 1019;
	}
}
add_action( 'template_redirect', 'panel_set_content_width' );

if ( ! function_exists( 'panel_setup' ) ) :
/**
 * Sets up theme defaults and registers support for various WordPress features.
 *
 * Note that this function is hooked into the after_setup_theme hook, which runs
 * before the init hook. The init hook is too late for some features, such as indicating
 * support post thumbnails.
 */
function panel_setup() {
	/**
	 * Make theme available for translation
	 * Translations can be filed in the /languages/ directory
	 * If you're building a theme based on Readable, use a find and replace
	 * to change 'panel' to the name of your theme in all the template files
	 */
	load_theme_textdomain( 'panel', get_template_directory() . '/languages' );

	/**
	 * Add default posts and comments RSS feed links to head
	 */
	add_theme_support( 'automatic-feed-links' );

	/**
	 * Enable support for editor styles
	 */
	add_editor_style();

	/**
	 * Enable support for Post Thumbnails on posts and pages
	 */
	add_theme_support( 'post-thumbnails' );
	set_post_thumbnail_size( '1500', '400', true ); //Featured header images
	add_image_size( 'panel-comic-strip', '940', '9999' ); //Large comic strips
	add_image_size( 'panel-home', '300', '300', true ); //Home page template featured thumbnails

	/**
	 * This theme uses wp_nav_menu() in one location.
	 */
	register_nav_menus( array(
		'primary' => __( 'Primary Menu', 'panel' ),
	) );

	/**
	 * Enable support for Post Formats
	 */
	add_theme_support( 'post-formats', array( 'aside', 'image', 'video', 'quote', 'link' ) );

}
endif; // panel_setup
add_action( 'after_setup_theme', 'panel_setup' );

/* Flush rewrite rules for Comics CPT on setup and switch */
function panel_flush_rewrite_rules() {
     flush_rewrite_rules();
}

add_action( 'after_switch_theme', 'panel_flush_rewrite_rules' );

/**
 * Setup the WordPress core custom background feature.
 *
 * Use add_theme_support to register support for WordPress 3.4+
 * as well as provide backward compatibility for WordPress 3.3
 * using feature detection of wp_get_theme() which was introduced
 * in WordPress 3.4.
 *
 * @todo Remove the 3.3 support when WordPress 3.6 is released.
 *
 * Hooks into the after_setup_theme action.
 */
function panel_register_custom_background() {
	$args = array(
		'default-color' => 'fdfdfa',
		'default-image' => '',
	);

	$args = apply_filters( 'panel_custom_background_args', $args );

	add_theme_support( 'custom-background', $args );
}
add_action( 'after_setup_theme', 'panel_register_custom_background' );

/**
 * Register widgetized area and update sidebar with default widgets
 */
function panel_widgets_init() {
	register_sidebar( array(
		'name'          => __( 'Primary Sidebar', 'panel' ),
		'id'            => 'sidebar-1',
		'before_widget' => '<aside id="%1$s" class="widget %2$s">',
		'after_widget'  => '</aside>',
		'before_title'  => '<h1 class="widget-title">',
		'after_title'   => '</h1>',
	) );
	register_sidebar( array(
		'name'          => __( 'Footer Sidebar 1', 'panel' ),
		'id'            => 'footer-sidebar-1',
		'before_widget' => '<aside id="%1$s" class="widget %2$s">',
		'after_widget'  => '</aside>',
		'before_title'  => '<h1 class="widget-title">',
		'after_title'   => '</h1>',
	) );
	register_sidebar( array(
		'name'          => __( 'Footer Sidebar 2', 'panel' ),
		'id'            => 'footer-sidebar-2',
		'before_widget' => '<aside id="%1$s" class="widget %2$s">',
		'after_widget'  => '</aside>',
		'before_title'  => '<h1 class="widget-title">',
		'after_title'   => '</h1>',
	) );
	register_sidebar( array(
		'name'          => __( 'Footer Sidebar 3', 'panel' ),
		'id'            => 'footer-sidebar-3',
		'before_widget' => '<aside id="%1$s" class="widget %2$s">',
		'after_widget'  => '</aside>',
		'before_title'  => '<h1 class="widget-title">',
		'after_title'   => '</h1>',
	) );
}
add_action( 'widgets_init', 'panel_widgets_init' );

/**
 * Enqueue scripts and styles
 */
function panel_scripts() {
	wp_enqueue_style( 'panel-style', get_stylesheet_uri() );

	wp_enqueue_style( 'panel-sourcesanspro' );
	wp_enqueue_style( 'panel-alegreya' );

	wp_enqueue_script( 'panel-navigation', get_template_directory_uri() . '/js/navigation.js', array(), '20120206', true );

	wp_enqueue_script( 'panel-skip-link-focus-fix', get_template_directory_uri() . '/js/skip-link-focus-fix.js', array(), '20130115', true );

	if ( is_singular() && comments_open() && get_option( 'thread_comments' ) )
		wp_enqueue_script( 'comment-reply' );

	if ( is_front_page() || is_singular( 'jetpack-comic' ) ) {
		wp_enqueue_script( 'panel-comic-navigation', get_template_directory_uri() . '/js/comic-navigation.js', array( 'jquery', 'jquery.spin' ), '20151102', true );
		wp_localize_script( 'panel-comic-navigation', 'comicNavigationOptions', array(
			'pjax' => panel_enable_pjax(),
		) );
	}

	if ( is_singular() && wp_attachment_is_image() )
		wp_enqueue_script( 'panel-keyboard-image-navigation', get_template_directory_uri() . '/js/keyboard-image-navigation.js', array( 'jquery' ), '20120202', true );
}
add_action( 'wp_enqueue_scripts', 'panel_scripts' );

/**
 * Whether or not to enable pjax loading of and navigation for comics.
 * This can result in fewer ad views, so users can disable it here.
 */
function panel_enable_pjax() {
	$enabled = true;

	// Let self-hosted .org installs disable it if they like.
	if ( defined( 'PANEL_DISABLE_PJAX' ) && PANEL_DISABLE_PJAX )
		$enabled = false;

	// If we're on WordPress.com, and the user gets ad revenue, turn this off.
	if ( function_exists( 'has_blog_sticker' ) && has_blog_sticker( 'wordads' ) )
		$enabled = false;

	return apply_filters( 'panel_enable_pjax', $enabled );
}

/**
 * Register Google Fonts
 */
function panel_google_fonts() {
	/*	translators: If there are characters in your language that are not supported
		by Source Sans Pro, translate this to 'off'. Do not translate into your own language. */
	if ( 'off' !== esc_html_x( 'on', 'Source Sans Pro font: on or off', 'panel' ) )
		wp_register_style( 'panel-sourcesanspro', "https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,700,400italic,700italic" );

	/*	translators: If there are characters in your language that are not supported
		by Alegreya, translate this to 'off'. Do not translate into your own language. */
	if ( 'off' !== esc_html_x( 'on', 'Alegreya font: on or off', 'panel' ) )
		wp_register_style( 'panel-alegreya', "https://fonts.googleapis.com/css?family=Alegreya:400italic,700italic,400,700&subset=latin,latin-ext" );
}
add_action( 'init', 'panel_google_fonts' );

/**
 * Loads the Genericons font file
 */
function panel_genericons() {
	wp_enqueue_style( 'genericons', get_template_directory_uri() . '/font/genericons.css', array(), '3.4.1' );
}
add_action( 'wp_enqueue_scripts', 'panel_genericons' );

/**
 * Enqueue Google Fonts for custom headers
 */
function panel_admin_scripts( $hook_suffix ) {
	if ( 'appearance_page_custom-header' != $hook_suffix )
		return;

	wp_enqueue_style( 'panel-sourcesanspro' );
	wp_enqueue_style( 'panel-alegreya' );

}
add_action( 'admin_enqueue_scripts', 'panel_admin_scripts' );


/**
 * Returns the Google font stylesheet URL if available.
 *
 * The use of Alegreya & Source Sans Pro by default is localized. For languages that use
 * characters not supported by the font, the font can be disabled.
 *
 * @return string Font stylesheet or empty string if disabled.
 */
function panel_get_font_urls() {
	$font_url = '';
	$subsets = 'latin,latin-ext';

	/* translators: If there are characters in your language that are not supported
	 by Alegreya, translate this to 'off'. Do not translate into your own language. */
	if ( 'off' !== esc_html_x( 'on', 'Alegreya font: on or off', 'panel' ) ) {

		$query_args = array(
			'family' => 'Alegreya:400italic,700italic,400,700',
			'subset' => $subsets,
		);
		$alegreya_font_url = add_query_arg( $query_args, "https://fonts.googleapis.com/css" );
	}

	/* translators: If there are characters in your language that are not supported
	 by Source Sans Pro, translate this to 'off'. Do not translate into your own language. */
	if ( 'off' !== esc_html_x( 'on', 'Source Sans Pro font: on or off', 'panel' ) ) {

		$query_args = array(
			'family' => 'Source+Sans+Pro:400,700,400italic,700italic',
			'subset' => $subsets,
		);
		$source_font_url = add_query_arg( $query_args, "https://fonts.googleapis.com/css" );
	}

	$fonts = array( $alegreya_font_url, $source_font_url );

	return $fonts;
}

/**
 * Adds additional stylesheets to the TinyMCE editor if needed.
 *
 * @uses panel_get_font_url() To get the Google Font stylesheet URL.
 *
 * @param string $mce_css CSS path to load in TinyMCE.
 * @return string
 */
function panel_mce_css( $mce_css ) {
	$fonts = panel_get_font_urls();

	if ( empty( $fonts ) )
		return $mce_css;

	if ( ! empty( $mce_css ) )
		$mce_css .= ',';

	for ( $i = 0; count( $fonts ) > $i; $i++ )
		$fonts[ $i ] = esc_url_raw( str_replace( ',', '%2C', $fonts[ $i ] ) );

	return $mce_css . implode( ',', $fonts );
}
add_filter( 'mce_css', 'panel_mce_css' );

/**
 * Implement the Custom Header feature.
 */
require get_template_directory() . '/inc/custom-header.php';

/**
 * Custom template tags for this theme.
 */
require get_template_directory() . '/inc/template-tags.php';

/**
 * Custom functions that act independently of the theme templates.
 */
require get_template_directory() . '/inc/extras.php';

/**
 * Customizer additions.
 */
require get_template_directory() . '/inc/customizer.php';

/**
 * Load Jetpack compatibility file.
 */
require get_template_directory() . '/inc/jetpack.php';



