<?php
/**
 * @package Panel
 */
?>
<article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
	<?php if ( '' != get_the_post_thumbnail() && panel_has_featured_posts() ) : ?>
	<figure class="home-thumbnail">
		<a href="<?php the_permalink(); ?>" rel="bookmark"><?php the_post_thumbnail( 'panel-home' ); ?></a>
	</figure>
	<?php endif; ?>
	<div class="home-content-wrapper clear">
		<header class="entry-header">
			<?php if ( ! post_password_required() && ( comments_open() || '0' != get_comments_number() ) ) : ?>
			<span class="comments-link"><?php comments_popup_link( __( '0', 'panel' ), __( '1', 'panel' ), __( '%', 'panel' ) ); ?></span>
			<?php endif; ?>
			<?php the_title( '<h1 class="entry-title"><a href="' . esc_url( get_permalink() ) . '" rel="bookmark">', '</a></h1>' ); ?>
			<div class="entry-meta">
				<?php panel_posted_on(); ?> <?php panel_posted_by(); ?> <?php edit_post_link( __( 'Edit', 'panel' ), '<span class="sep"> ~ </span><span class="edit-link">', '</span>' ); ?>
			</div>
		</header><!-- .entry-header -->

		<?php if ( panel_has_featured_posts() ) : ?>
		<div class="entry-summary">
			<?php the_excerpt(); ?>
		</div><!-- .entry-summary -->
		<?php else: ?>
		<div class="entry-content">
			<?php
				// Set $more to 0 in order to only get the first part of the post
				global $more;
				$more = 0;
			?>
			<?php the_content( __( 'Continue reading <span class="meta-nav">&rarr;</span>', 'panel' ) ); ?>
			<?php
				wp_link_pages( array(
					'before' => '<div class="page-links">' . __( 'Pages:', 'panel' ),
					'after'  => '</div>',
				) );
			?>
		</div><!-- .entry-content -->
		<?php endif; ?>
	</div>
</article><!-- #post-## -->
