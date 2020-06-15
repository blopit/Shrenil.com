<?php
/**
 * The template for displaying the footer.
 *
 * Contains the closing of the id=main div and all content after
 *
 * @package Panel
 */

$facebook = get_theme_mod( 'jetpack-facebook' );
$twitter = get_theme_mod( 'jetpack-twitter' );
$tumblr = get_theme_mod( 'jetpack-tumblr' );
?>

	</div><!-- #main -->
	<footer id="colophon" class="site-footer" role="contentinfo">
		<?php get_sidebar( 'tertiary' ); ?>
		<div class="colophon-wrapper clear">
			<div class="site-info">
				<?php do_action( 'panel_credits' ); ?>
				<a href="http://wordpress.org/" title="<?php esc_attr_e( 'A Semantic Personal Publishing Platform', 'panel' ); ?>" rel="generator"><?php printf( __( 'Proudly powered by %s', 'panel' ), 'WordPress' ); ?></a>
				<span class="sep"> ~ </span>
				<?php printf( __( 'Theme: %1$s by %2$s.', 'panel' ), 'Panel', '<a href="https://wordpress.com/themes" rel="designer">WordPress.com</a>' ); ?>
			</div><!-- .site-info -->
			<?php if ( $facebook || $twitter || $tumblr ) : ?>
				<div class="social-links">
				<?php if ( $facebook ) : ?>
					<a href="<?php echo esc_url( $facebook ); ?>" class="facebook-link" data-icon="&#xF204;">
						<span class="screen-reader-text"><?php esc_html_e( 'Facebook', 'panel' ); ?></span>
					</a>
				<?php endif; ?>
				<?php if ( $twitter ) : ?>
					<a href="<?php echo esc_url( $twitter ); ?>" class="twitter-link" data-icon="&#xF202;">
						<span class="screen-reader-text"><?php esc_html_e( 'Twitter', 'panel' ); ?></span>
					</a>
				<?php endif; ?>
				<?php if ( $tumblr ) : ?>
					<a href="<?php echo esc_url( $tumblr ); ?>" class="tumblr-link" data-icon="&#xF214;">
						<span class="screen-reader-text"><?php esc_html_e( 'Tumblr', 'panel' ); ?></span>
					</a>
				<?php endif; ?>
				</div>
			<?php endif; ?>
		</div><!-- .colophon-wrapper -->
	</footer><!-- #colophon -->
</div><!-- #page -->

<?php wp_footer(); ?>

</body>
</html>