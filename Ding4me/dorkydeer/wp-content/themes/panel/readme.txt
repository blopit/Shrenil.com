=== Panel ===
Contributors: automattic
Donate link:
Tags: black, beige, orange, white, one-column, two-columns, right-sidebar, fixed-layout, responsive-layout, custom-background, custom-colors, custom-header, custom-menu, editor-style, featured-images, featured-image-header, full-width-template, infinite-scroll, post-formats, rtl-language-support, translation-ready, art, artwork, cartoon, clean, light, minimal, modern, professional, traditional
Requires at least: 3.4
Tested up to: 4.2
Stable tag:
License: GPLv2 or later
License URI: http://www.gnu.org/licenses/gpl-2.0.html

A modern theme that makes it quick and easy to publish a webcomic when used with Jetpack (http://jetpack.me).

== Description ==

A modern theme that makes it quick and easy to publish a webcomic when used with [Jetpack](http://jetpack.me).

* Designed to beautifully display your webcomic series
* First, Previous, Next, Last, and Random comic navigation
* Date-based comics archive, which can be viewed at example.com/comic/ (replacing example.com with your site's URL)
* Convert existing Posts to Comics, and vice versa
* Showcase your latest news on the home page with Jetpack.me compatibility for Featured Content
* Full-width page template
* Responsive layout
* Custom Background
* Custom Header
* Jetpack.me compatibility for Infinite scroll & Social Links
* Keyboard navigation for image attachment templates.
* CSS3 transition effects
* The GPL v2.0 or later license. :) Use it to make something cool.

== Installation ==

1. In your admin panel, go to Appearance -> Themes and click the Add New button.
2. Click Upload and Choose File, then select the theme's .zip file. Click Install Now.
3. Click Activate to use your new theme right away.

== Frequently Asked Questions ==

= I don't see the Comics menu in my dashboard, where can I find it? =

To make the Comics menu appear in your dashboard, you need to install the [Jetpack plugin](http://jetpack.me) because it has the required code needed to make [custom post types](http://codex.wordpress.org/Post_Types#Custom_Post_Types) work for the Panel theme.

Once Jetpack is active, the Comics menu will appear in the dashboard, in addition to standard blog posts. No special Jetpack module is needed and a WordPress.com connection is not required for the Comics feature to function. Comics will work on a localhost installation of WordPress if you add this line to `wp-config.php`:

`define( 'JETPACK_DEV_DEBUG', TRUE );`

The Comics dashboard: https://cloudup.com/cQn7PDFLwzQ

= Is there a quicker way to add new comics than by uploading them through my dashboard? =

Panel features an easy drag-and-drop method for uploading comics through the front end of your site. Just drag a comic image file onto any page on the public side of your site, and it'll create a new Comic post for you. Add a title, category, and tags as you like, and you're all set. Here's a little video to see how it works:

Drag-and-drop comics on the front end: https://cloudup.com/csNWEYDlDdD (screencast)

= Can I get a page that lists all my comics in chronological order? =

Yes! Panel automatically generates an archive of all your comics, which you can see by adding this to the end of your site's URL:

`/comic/`

Users can also access your Comics via an RSS feed by appending this to your site's URL:

`/comic/feed/`

You'll need pretty permalinks (any structure) for this URL to work. If you're stuck with default permalinks – your links have a query string at the end, like ?p=123 – then your comics archive can be accessed by adding this immediately after your URL:

`/?post_type=jetpack-comic`

The Comics archive page: https://cloudup.com/cRIY1lZAWmA

= Can I have multiple comics archives on one site, say if I have more than one comic series? =

At this time only one comic archive per site is available.

= Can I add a link to the next comic on the image itself, in addition to the arrows below the comic? =

You can edit each comic to add a link to the next comic in the series.

Click the image in the visual editor, and then click the small blue "Edit image" icon.

Edit image: https://cloudup.com/c44sbpanEbx

In the overlay window, paste a link to the next comic page in the Link URL field. Click Update, and then publish or update your post.

Edit Link URL: https://cloudup.com/ch7FSVBGohL

= Is there a way to import comics in bulk? =

If you have a few regular blog posts with comic content, you can convert them to Comics in bulk, using the Convert to Comic bulk-edit option.

Open the All Posts dashboard: Posts → All Posts.
Check the checkbox next to any posts that are comics and then choose “Convert to Comic” from the Bulk Actions dropdown.
 

Your comic posts will now be listed under Comics → All Comics

Convert to Comic: https://cloudup.com/c8YZ4DtLyzg

= Are there any keyboard shortcuts to let my readers navigate between comics more easily? =

Your visitors can read through your comics by using the navigation buttons underneath each comic. They’ll have easy access to the beginning of your strip or to the latest entry, and they can instantly load the next or previous installment by using the left (←) and right (→) arrow keyboard keys.

Navigation: https://cloudup.com/cQfa7LJEoPe

= Does Panel come with multiple page templates? =

Panel comes with a full-width page template. If you would like to remove the sidebar from a Page, assign it the Full Width, No Sidebar template under Page Attributes.

Full-width template: https://cloudup.com/cArXliethok

= Can I highlight specific posts on the homepage? =

Panel has an optional featured-content area on the homepage, which you can set up by following these steps:

1. Tag any posts you want to feature with a specific Tag of your choosing, such as the word "featured".
2. Navigate to Appearance → Customize.
3. In the section labeled "Featured Content," enter the name of a tag.
4. Click the "Save" button.
Featured Content: https://cloudup.com/cZ7UfQ9iJ5E

If no Featured Content is selected, your latest posts will be displayed in this area.

= Does Panel use featured images? =

If a Featured Image at least 1500px by 400px is set for a post or page, it will display as a Featured Header Image, appearing as a full-width banner across the top.

= Quick Panel Specs (all measurements in pixels) =

1. The main column width is 750 except in the full-width layout where it’s 1019.
2. The Comic content column width is 940.
3. The Primary sidebar width is 200.
4. The Footer Sidebar widths are 300.
5. Featured Header Images are 1500 wide and 400 tall, cropped.
6. Comic Featured Images are 940 wide with unlimited height.
7. Featured Images on the front page are 300 pixels square, cropped.

== Changelog ==

= 2 November 2015 =
* Correct poorly-formed translated links.
* Update datestring for comic-navigation.js so it uses the updated version;
* Update navigation to scroll to top of page when switching between comics.

= 27 October 2015 =
* Updated Genericons font to the latest version; Related to #3465;

= 23 October 2015 =
* Fix issue with "First" comic nav button not displaying. Closes #2875

= 28 September 2015 =
* Prevent navigation from disappearing when first comic is displayed. Closes r2875.

= 24 September 2015 =
* Use global handle when enqueueing Genericons.

= 15 September 2015 =
* Display social media icons inline rather then as block elements; Fixes #3411;

= 20 August 2015 =
* Add text domain and/or remove domain path. (O-S)

= 17 August 2015 =
* Ensure that prev/next strings for comic navigation are

= 31 July 2015 =
* Remove `.screen-reader-text:hover` and `.screen-reader-text:active` style rules.

= 15 July 2015 =
* Always use https when loading Google Fonts.

= 15 June 2015 =
* Updating version number for regenerated download

= 2 June 2015 =
* fix `sprintf` placeholder.

= 6 May 2015 =
* Fully remove example.html from Genericons folders.
* Remove index.html file from Genericions.

= 6 March 2015 =
* If a user has selected a static front page for their site, don't display a "No results" message if no posts are found.

= 17 December 2014 =
* Allow tablets to access submenu items in the site navigation.

= 23 September 2014 =
* Remove a gap between custom header and the content on small screen.

= 24 July 2014 =
* change theme/author URIs and footer links to `wordpress.com/themes`.

= 3 July 2014 =
* remove unused `outdoorsy` tag, add `outdoors` tag

= 1 June 2014 =
* add/update pot files.

= 8 April 2014 =
* Update readme with new featured content instructions.

= 11 March 2014 =
* Remove infinite-scroll tag since this theme does not currently support IS.

= 13 January 2014 =
* Update readme to WordPress.org plugin standards.

= 19 December 2013 =
* Fixed issue with sidebar showing on front page when full width template is applied.

= 6 December 2013 =
* update Width terms to Layout.

= 3 December 2013 =
* add box-sizing for captions so they aren't cut off in the responsive design.

= 8 November 2013 =
* testing out a commit, please ignore.

= 6 November 2013 =
* Remove escaping for HTML blocks.

= 31 October 2013 =
* Ensure random comic navigation button points to the site's home_url rather than using a relative link. This

= 30 October 2013 =
* Disable PJAX loading of comics if WordAds is active, and include a constant/filter for self-hosted users to disable it. Props @georgestephanis.
* Minor tweak to syntax to ensure theme does not fatal error for certain self-hosted configurations. Worked on .com but not on a local install of 3.6 with PHP 5.2 or 5.3.6
* Ensure images do not get duplicated when uploaded using easy upload; strip out image from the_content if the same featured image is set. Fixes #1982. Props @georgestephanis

= 25 October 2013 =
* Remove stray punctuation mark in stylesheet.

= 21 October 2013 =
* Remove flush_rewrite_rules from after_setup_theme, leaving on after_switch_theme only; leaving it on both
* Flush rewrite rules for the Comics CPT on theme setup and switch; this *should* fix issues with broken URLs/404s upon activation

= 5 September 2013 =
* Add description in readme. Move all wp.com related code/functionality in a inc/wpcom.php file.
* Add more detailed licensing information, based on latest theme review. Bump to version 1.0.1.

= 7 August 2013 =
* Update POT file for submission to Extend
* Remove gettext wrapper around empty string in content.php

= 5 August 2013 =
* update author in footer and stylesheet.

= 29 July 2013 =
* code style consistency.

= 24 July 2013 =
* remove hardcoded inclusion of wpcom.php.
* Ensure custom query on home page respects pagination and/or the More tag.

= 22 July 2013 =
* Fix bug where a static front page + latest posts combination would not display on the home page; had to create a custom query to do this.
* Ensure infinite scroll post display is consistent between front page and static front page views.
* Ensure we don't add the custom-header body class to home page when a static front page is defined; this will prevent the blog posts list from being displayed over the header.

= 18 July 2013 =
* Add POT file to prep for submission to Extend

= 11 July 2013 =
* Display comic meta on the home page, but hide with CSS, so users can customize if they want to.

= 10 July 2013 =
* If no Featured Content is active, display the full content for latest posts
* Fix custom header display for search pages
* Set a fixed height on the header.
* Tweaks to featured image styles so they don't get stretched; fix featured header image display on archive pages.
* Ensure that, when displaying "latest posts" on the front page, and the latest one has a featured image, the .custom-header class does not get set on the body tag.
* Load comments for new comics that are loaded via AJAX.
* Make the comics navigation links a bit more prominent, with better contrast

= 9 July 2013 =
* Update the page title when a new comic is loaded via AJAX.
* Add a more prominent link to comments to promote discussion on Comics posts when on the front page.
* Add screenshot

= 8 July 2013 =
* WP_Query defaults to DESC and post_type -- we don't need to do it twice.
* Hide tags and categories on the front page
* Add support for pagination within Comics posts.
* Refine tags/categories integration on comics archive.
* Add support for front-end comics loading via JS, props @georgestephanis; begin adding taxonomies to comics in singular view.

= 7 July 2013 =
* Adjust margins for mobile views depending on prescence of a custom header image

= 6 July 2013 =
* Ensure navigation links display without overlapping on all screen sizes.
* Ensure theme validates properly -- can't include DIV inside H1, change menu-toggle-icon to SPAN to conform
* Style fixes for mobile devices; ensure navigation for comics does not get squished together on small screens, and that content areas have appropriate padding/margins
* Ensure stats smiley does not show above header
* Tweaks to logic around comic navigation so it will display properly when no Posts exist.

= 4 July 2013 =
* Replace instances of _e, __() and _x with esc_html_ versions for greater security.
* Tweak to widget list border color for footer widgets; replace _e with esc_html_e in footer.php
* Let ordered lists retain their numbers in widgets
* Tweaks to widget list styles;
* Multiple changes:

= 3 July 2013 =
* Ensure content does not overflow when using a static front page
* Ensure single image attachments are centered
* Ensure a div is always displayed for comic navigation links, even if a link does not exist, so that they stay in the same place when navigating
* Comments to explain jetpack support functions
* Update image.php with simplifications from _s; extract image logic into template-tags.php
* Enqueue Genericons in functions.php; simplify panel_mce_css() function; organize jetpack.php
* Wrap print-style theme support in a callback function
* Add support for Tumblr social link
* Remove back-compat for custom headers and backgrounds; move file inclues to bottom of functions.php; replace global $post->ID with get_the_ID(); add screen-reader-text with title to Read More link for a11y
* Prefix featured images
* Echo categories_list in index view; remove content-comic-archive.php and move it into archive-jetpack-comic.php; re-order IF/THEN checks for featured header images; cleanup style.css, updated license and add -wpcom suffix to version #; minor code cleanup in template-tags.php; exchange the_time() for get_the_date() in content-comic.php

= 2 July 2013 =
* Link to permalink instead of full size image
* Move entry meta to float to the right of the title for comics, so there's less vertical space required to get to the comics navigation.
* Don't use $query->the_post() as it steps on the global $post loop.
* First/Last links in the comic navigation.
* Fix date_format option for comic permalink
* Clean up list styles in widgets
* Add entry-meta class around date permalink for Comics posts

= 29 June 2013 =
* Add permalink date/time to comic entries, in absence of a post title; ensure custom headers display properly on comic archives.

= 28 June 2013 =
* Multiple changes:

= 26 June 2013 =
* Add support for social links in the footer
* Add RTL styles; remove unused page title from comics archives template; move navigation outside the loop when no featured posts are set; remove duplicated call to Social Links theme support
* Deactivate infinite scroll when sidebar is active in mobile; tweaks to styles; update $themecolors array with proper colors
* Tweak to width of navigation links for comics posts

= 25 June 2013 =
* Fix navigation alignment with a more specific CSS rule
* Adjust comic navigation such that it remains centered regardless of the existence of a previous/next comic (like on the home page, where the comic will never have a "next").
* Move Jetpack functions into jetpack.php; add Edit link for Comic posts.
* Add the random comic link.
* Update Jetpack infinite scroll support
* Update for Jetpack infinite scroll support; use the_content instead of the_excerpt for comics posts.
* Add tags to style.css; fall back to "No posts found" message if no featured content or latest posts exist
* Multiple changes:

= 24 June 2013 =
* Initial commit from local
