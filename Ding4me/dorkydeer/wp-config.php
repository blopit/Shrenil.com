<?php
/**
 * The base configuration for WordPress
 *
 * The wp-config.php creation script uses this file during the
 * installation. You don't have to use the web site, you can
 * copy this file to "wp-config.php" and fill in the values.
 *
 * This file contains the following configurations:
 *
 * * MySQL settings
 * * Secret keys
 * * Database table prefix
 * * ABSPATH
 *
 * @link https://codex.wordpress.org/Editing_wp-config.php
 *
 * @package WordPress
 */

// ** MySQL settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define('DB_NAME', 'blopit_wp1');

/** MySQL database username */
define('DB_USER', 'blopit_wp1');

/** MySQL database password */
define('DB_PASSWORD', 'P[R[m9@3r(ImzC0VBV.50^^2');

/** MySQL hostname */
define('DB_HOST', 'localhost');

/** Database Charset to use in creating database tables. */
define('DB_CHARSET', 'utf8');

/** The Database Collate type. Don't change this if in doubt. */
define('DB_COLLATE', '');

/**#@+
 * Authentication Unique Keys and Salts.
 *
 * Change these to different unique phrases!
 * You can generate these using the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}
 * You can change these at any point in time to invalidate all existing cookies. This will force all users to have to log in again.
 *
 * @since 2.6.0
 */
define('AUTH_KEY',         'qmDZ4MC2Wg1ROKJ5BjCYtSisVNREemdvMlcbLbohb7oWoIlPrd0gODQhUNxzDvmN');
define('SECURE_AUTH_KEY',  '90ftB8Tuz8kpc29303K2IKAZexRy1C4AlcygfVaJUycmdXl2I3IEPdUO3u1WQcJr');
define('LOGGED_IN_KEY',    'UJMumNv6l0UojFXgOgBBaZmLIwZsUur0WyMOhX6QXwuK8SvEdYWZ6NEd5oGJwOo4');
define('NONCE_KEY',        'vfxaVk3X331dHC4o8LKSW4sOWipMErYUNmfJNTgREhvRSzn35thf3RNJYHNvBHlI');
define('AUTH_SALT',        'BoPwP25fDhYu1jMpOhGNVhKUwHwfMRodcKrNf19NulY1IV6WBLbyTAnAF79bUofS');
define('SECURE_AUTH_SALT', '16SdzNkO4hfUN7WUwoTo6z0974TyhwJFz2933AHRrveWnTv2HBKBdT2soSEOuXtE');
define('LOGGED_IN_SALT',   'N18INqYcEtCkLwDDDS0b7uDtDYJekNJ5LQvwd6SNWNH6SwWY4vrU5NdgkHxWzhiF');
define('NONCE_SALT',       'FzbcEIESoBp4V5ve9e6AjcJh1qNTQYKfnNxWBTFebd0PKGquFj81lj0LpJLPz6JH');

/**
 * Other customizations.
 */
define('FS_METHOD','direct');define('FS_CHMOD_DIR',0755);define('FS_CHMOD_FILE',0644);
define('WP_TEMP_DIR',dirname(__FILE__).'/wp-content/uploads');

/**
 * Turn off automatic updates since these are managed upstream.
 */
define('AUTOMATIC_UPDATER_DISABLED', true);


/**#@-*/

/**
 * WordPress Database Table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 */
$table_prefix  = 'wp_';

/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the Codex.
 *
 * @link https://codex.wordpress.org/Debugging_in_WordPress
 */
define('WP_DEBUG', false);

/* That's all, stop editing! Happy blogging. */

/** Absolute path to the WordPress directory. */
if ( !defined('ABSPATH') )
	define('ABSPATH', dirname(__FILE__) . '/');

/** Sets up WordPress vars and included files. */
require_once(ABSPATH . 'wp-settings.php');
