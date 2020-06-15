<?php
/**
 * @package Panel
 */

/**
 * Setup the WordPress core custom header feature.
 *
 * Use add_theme_support to register support for WordPress 3.4+
 * as well as provide backward compatibility for previous versions.
 * Use feature detection of wp_get_theme() which was introduced
 * in WordPress 3.4.
 *
 * @todo Rework this function to remove WordPress 3.4 support when WordPress 3.6 is released.
 *
 * @uses panel_header_style()
 * @uses panel_admin_header_style()
 * @uses panel_admin_header_image()
 *
 * @package Panel
 */
function panel_custom_header_setup() {
	$args = array(
		'default-text-color'     => 'ffffff',
		'width'                  => 1500,
		'height'                 => 400,
		'flex-height'            => true,
		'wp-head-callback'       => 'panel_header_style',
		'admin-head-callback'    => 'panel_admin_header_style',
		'admin-preview-callback' => 'panel_admin_header_image',
	);

	$args = apply_filters( 'panel_custom_header_args', $args );

	add_theme_support( 'custom-header', $args );

}
add_action( 'after_setup_theme', 'panel_custom_header_setup' );

/**
 * Shiv for get_custom_header().
 *
 * get_custom_header() was introduced to WordPress
 * in version 3.4. To provide backward compatibility
 * with previous versions, we will define our own version
 * of this function.
 *
 * @todo Remove this function when WordPress 3.6 is released.
 * @return stdClass All properties represent attributes of the curent header image.
 *
 * @package Panel
 */

if ( ! function_exists( 'get_custom_header' ) ) {
	function get_custom_header() {
		return (object) array(
			'url'           => get_header_image(),
			'thumbnail_url' => get_header_image(),
			'width'         => HEADER_IMAGE_WIDTH,
			'height'        => HEADER_IMAGE_HEIGHT,
		);
	}
}

if ( ! function_exists( 'panel_header_style' ) ) :
/**
 * Styles the header image and text displayed on the blog
 *
 * @see panel_custom_header_setup().
 */
function panel_header_style() {
	$header_text_color = get_header_textcolor();

	// If no custom options for text are set, let's bail
	// get_header_textcolor() options: HEADER_TEXTCOLOR is default, hide text (returns 'blank') or any hex value
	if ( HEADER_TEXTCOLOR == $header_text_color )
		return;

	// If we get this far, we have custom styles. Let's do this.
	?>
	<style type="text/css">
	<?php
		// Has the text been hidden?
		if ( 'blank' == $header_text_color ) :
	?>
		.site-title,
		.site-description {
			position: absolute;
			clip: rect(1px 1px 1px 1px); /* IE6, IE7 */
			clip: rect(1px, 1px, 1px, 1px);
		}
	<?php
		// If the user has set a custom color for the text use that
		else :
	?>
		.site-title a {
			color: #<?php echo $header_text_color; ?>;
		}
	<?php endif; ?>
	</style>
	<?php
}
endif; // panel_header_style

if ( ! function_exists( 'panel_admin_header_style' ) ) :
/**
 * Styles the header image displayed on the Appearance > Header admin panel.
 *
 * @see panel_custom_header_setup().
 */
function panel_admin_header_style() {
?>
	<style type="text/css">
	.appearance_page_custom-header #headimg {
		background: #333;
		border: none;
		border-bottom: 5px solid #fe7050;
	}
	.branding {
		margin: .8em 0 .8em 1.6em;
		max-width: 33%;
	}
	#headimg h1,
	#desc {
	}
	#headimg h1 {
		font-family: Alegreya, "Times New Roman", serif;
		font-size: 23px;
		font-weight: normal;
		line-height: 1.25;
		margin: 0;
	}
	#headimg h1 a {
		text-decoration: none;
	}
	#desc {
		color: rgba(255,255,255,.4) !important;
		font-family: "Source Sans Pro", Arial, Helvetica, sans-serif;
		font-size: 14px;
		font-style: italic;
		line-height: 1.25;
		margin: 0;
	}
	.header-image {
		max-width: 100%;
		height: auto;
	}
	</style>
<?php
}
endif; // panel_admin_header_style

if ( ! function_exists( 'panel_admin_header_image' ) ) :
/**
 * Custom header image markup displayed on the Appearance > Header admin panel.
 *
 * @see panel_custom_header_setup().
 */
function panel_admin_header_image() {
	$style        = sprintf( ' style="color:#%s;"', get_header_textcolor() );
	$header_image = get_header_image();
?>
	<div id="headimg">
		<div class="branding">
			<h1 class="displaying-header-text"><a id="name"<?php echo $style; ?> onclick="return false;" href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php bloginfo( 'name' ); ?></a></h1>
			<div class="displaying-header-text" id="desc"<?php echo $style; ?>><?php bloginfo( 'description' ); ?></div>
		</div>
	</div>
	<?php if ( ! empty( $header_image ) ) : ?>
		<img src="<?php echo esc_url( $header_image ); ?>" alt="" class="header-image" />
	<?php endif; ?>
<?php
}
endif; // panel_admin_header_image
