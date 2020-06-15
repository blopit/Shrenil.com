<?php
/**
 * @package Panel
 */

$format = get_post_format();
$formats = get_theme_support( 'post-formats' );
?>
<article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
	<header class="entry-header">
		<?php if ( $format && in_array( $format, $formats[0] ) ): ?>
			<a class="entry-format" href="<?php echo esc_url( get_post_format_link( $format ) ); ?>" title="<?php echo esc_attr( sprintf( __( 'All %s posts', 'panel' ), get_post_format_string( $format ) ) ); ?>"><?php echo get_post_format_string( $format ); ?></a>
		<?php endif; ?>
		<?php the_title( '<h1 class="entry-title"><a href="' . esc_url( get_permalink() ) . '" rel="bookmark">', '</a></h1>' ); ?>
		<?php if ( 'post' == get_post_type() ) : ?>
			<div class="entry-meta">
				<?php panel_posted_on(); ?> <?php panel_posted_by(); ?> <?php edit_post_link( __( 'Edit', 'panel' ), '<span class="sep"> ~ </span><span class="edit-link">', '</span>' ); ?>
			</div>
		<?php endif; ?>
	</header><!-- .entry-header -->

	<?php if ( is_search() ) : // Only display Excerpts for Search ?>
	<div class="entry-summary">
		<?php the_excerpt(); ?>
	</div><!-- .entry-summary -->
	<?php else : ?>
	<div class="entry-content">
		<?php the_content( __( 'Continue reading <span class="meta-nav">&rarr;</span>', 'panel' ) ); ?>
		<?php
			wp_link_pages( array(
				'before' => '<div class="page-links">' . __( 'Pages:', 'panel' ),
				'after'  => '</div>',
			) );
		?>
	</div><!-- .entry-content -->
	<?php endif; ?>

	<footer class="entry-meta">
		<?php if ( 'post' == get_post_type() ) : // Hide category and tag text for pages on Search ?>
			<?php
				/* translators: used between list items, there is a space */
				$categories_list = get_the_category_list( ' ' );
				if ( $categories_list && panel_categorized_blog() ) :
			?>
			<span class="cat-links">
				<?php echo $categories_list; ?>
			</span>
			<?php endif; // End if categories ?>
		<?php endif; // End if 'post' == get_post_type() ?>

		<?php if ( ! post_password_required() && ( comments_open() || '0' != get_comments_number() ) ) : ?>
		<span class="comments-link"><?php comments_popup_link( __( '0', 'panel' ), __( '1', 'panel' ), __( '%', 'panel' ) ); ?></span>
		<?php endif; ?>

	</footer><!-- .entry-meta -->
</article><!-- #post-## -->
