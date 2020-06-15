<?php
/**
 * @package Panel
 */
?>
<article id="jetpack-comic-<?php the_id(); ?>" <?php post_class(); ?>>
	<a href="<?php the_permalink(); ?>"><?php the_post_thumbnail( 'panel-comic-strip' ); ?></a>
	<?php the_title( '<h1 class="comic-title"><a href="' . esc_url( get_permalink() ) . '" rel="bookmark">', '</a></h1>' ); ?>
	<header class="comic-meta entry-meta">
		<a href="<?php the_permalink(); ?>"><?php echo get_the_date(); ?></a>
		<?php if ( ! is_singular( 'jetpack-comic' ) && ! post_password_required() && ( comments_open() || '0' != get_comments_number() ) ) : ?>
		<span class="sep"> ~ </span>
		<span class="comic-comments-link"><?php comments_popup_link( __( 'Leave a comment', 'panel' ), __( '1 Comment', 'panel' ), __( '% Comments', 'panel' ) ); ?></span>
		<?php endif; ?>
		<?php edit_post_link( __( 'Edit', 'panel' ), '<span class="sep"> ~ </span><span class="comic-edit-link">', '</span>' ); ?>
	</header>
	<div class="comic-content">
		<?php the_content(); ?>
		<?php
			wp_link_pages( array(
				'before' => '<div class="page-links">' . __( 'Pages:', 'panel' ),
				'after'  => '</div>',
			) );
		?>
	</div>
	<footer class="comic-meta entry-meta">
		<?php
		/* translators: used between list items, there is a space after the comma */
		$category_list = get_the_category_list( __( ', ', 'panel' ) );

		/* translators: used between list items, there is a space after the comma */
		$tag_list = get_the_tag_list( '', __( ', ', 'panel' ) );

		if ( ! panel_categorized_blog() ) {
			// This blog only has 1 category so we just need to worry about tags in the meta text
			if ( '' != $tag_list ) {
				$meta_text = __( 'This comic was tagged %2$s.', 'panel' );
			}

		} else {
			// But this blog has loads of categories so we should probably display them here
			if ( '' != $tag_list ) {
				$meta_text = __( 'This comic was posted in %1$s and tagged %2$s.', 'panel' );
			} else {
				$meta_text = __( 'This comic was posted in %1$s.', 'panel' );
			}

		} // end check for categories on this blog

		printf(
			$meta_text,
			$category_list,
			$tag_list
		);
		?>
	</footer>
</article>