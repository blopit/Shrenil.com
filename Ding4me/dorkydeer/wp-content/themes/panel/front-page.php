<?php
/**
 * @package Panel
 */

get_header();

	//Get the latest comic
	$comic_args = array(
		'posts_per_page' => 1,
		'post_type'      => 'jetpack-comic',
	);
	$comic = new WP_Query( $comic_args );
?>

	<?php if ( $comic->have_posts() ) : ?>

		<div class="entry-comic">

			<?php /* Start the comic Loop */ ?>
			<?php while ( $comic->have_posts() ) : $comic->the_post(); ?>

				<?php get_template_part( 'content', 'comic' ); ?>

				<?php panel_content_nav( 'comic-nav-below' ); ?>

			<?php endwhile; ?>

		</div>

	<?php endif; ?>

	<?php wp_reset_postdata(); ?>

	<div id="primary" class="content-area">
		<?php
		//Display static front page content above Featured Posts area if set
		if ( is_page() ) :
			if ( have_posts() ) : ?>

				<div class="site-content">
				<?php
					while ( have_posts() ) : the_post();
						get_template_part( 'content', 'page' );
					endwhile;

					rewind_posts(); ?>
				</div>
			<?php endif;
		endif;

		$paged = ( get_query_var( 'paged' ) ) ? get_query_var( 'paged' ) : 1;

		$front_posts = new WP_Query( array(
			'posts_per_page' => get_option( 'posts_per_page' ),
			'paged'          => $paged,
			'no_found_rows'  => true,
		) );

		if ( panel_has_featured_posts() ) : ?>

			<div id="featured-content" class="site-content" role="main">

				<div class="featured-news-title"><?php esc_html_e( 'Featured News', 'panel' ); ?></div>

				<?php $featured_posts = panel_get_featured_posts(); ?>

				<?php foreach ( (array) $featured_posts as $order => $post ) : ?>

					<?php setup_postdata( $post ); ?>

					<?php get_template_part( 'content', 'featured' ); ?>

				<?php endforeach; ?>

			</div>

			<?php wp_reset_postdata(); ?>

		<?php elseif ( $front_posts->have_posts() ) : ?>

			<div id="content" class="site-content" role="main">

				<div class="featured-news-title"><?php esc_html_e( 'Latest News', 'panel' ); ?></div>

				<?php while ( $front_posts->have_posts() ) : $front_posts->the_post(); ?>

					<?php get_template_part( 'content', 'featured' ); ?>

				<?php endwhile; ?>

				<?php panel_content_nav( 'nav-below' ); ?>

			</div>

		<?php elseif ( 'page' !== get_option( 'show_on_front' ) ) : ?>

			<div id="content" class="site-content" role="main">

				<?php get_template_part( 'no-results', 'index' ); ?>

			</div>

		<?php endif; ?>

		<?php wp_reset_postdata(); ?>

	</div><!-- #primary -->
<?php if ( ! is_page_template( 'nosidebar-page.php' ) ) get_sidebar(); ?>
<?php get_footer(); ?>