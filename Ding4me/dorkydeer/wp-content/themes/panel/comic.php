<?php
/**
 * The comics template file.
 *
 * @package Panel
 */

get_header(); ?>

	<div id="primary" class="content-area">
		<div id="content" class="site-content" role="main">

		<?php if ( have_posts() ) : ?>

			<?php /* Start the Loop */ ?>
			<?php while ( have_posts() ) : the_post(); ?>

				<?php get_template_part( 'content', 'comic' ); ?>

			<?php endwhile; ?>

			<?php panel_content_nav( 'comic-nav-below' ); ?>

		<?php else : ?>

			<?php get_template_part( 'no-results', 'index' ); ?>

		<?php endif; ?>

		</div><!-- #content -->
	</div><!-- #primary -->

<?php get_footer(); ?>