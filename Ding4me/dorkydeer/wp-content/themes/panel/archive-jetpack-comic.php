<?php
/**
 * The template for displaying Comics Archive pages.
 *
 * Learn more: http://codex.wordpress.org/Template_Hierarchy
 *
 * @package Panel
 */

get_header(); ?>

	<section id="primary" class="content-area">
		<div id="content" class="site-content" role="main">

		<?php if ( have_posts() ) : ?>

			<header class="page-header">
				<h1 class="page-title">
					<?php esc_html_e( 'Comic Archives', 'panel' ); ?>
				</h1>
			</header><!-- .page-header -->

			<?php /* Start the Loop */ ?>

			<ul class="comics-archive-list">

			<?php while ( have_posts() ) : the_post(); ?>

				<li class="comic-archives-entry"><span class="comic-archives-date"><?php echo get_the_date(); ?></span><span class="sep"> ~ </span><span class="comic-archives-title"><a href="<?php the_permalink(); ?>" rel="bookmark"><?php the_title(); ?></a></span></li>

			<?php endwhile; ?>

			</ul>

			<?php panel_content_nav( 'comics-nav-below' ); ?>

		<?php else : ?>

			<?php get_template_part( 'no-results', 'archive' ); ?>

		<?php endif; ?>

		</div><!-- #content -->
	</section><!-- #primary -->

<?php get_sidebar(); ?>
<?php get_footer(); ?>