SET time_zone = "+00:00";
CREATE DATABASE IF NOT EXISTS youtube;
use youtube;
CREATE TABLE IF NOT EXISTS `youtube_resources` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `owner_id` varchar(55) CHARACTER SET utf8 NOT NULL,
  `res_id` int(11) NOT NULL,
  `link` varchar(255) NOT NULL,
  UNIQUE KEY `owner_id` (`owner_id`),
  KEY `link` (`link`),
  KEY `red_id` (`res_id`)
) DEFAULT CHARSET=latin1;

CREATE TABLE `youtube_videos` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `owner_id` varchar(30) NOT NULL,
  `item_id` varchar(30) NOT NULL,
  `res_id` int(11) NOT NULL,
  `link` varchar(4000) NOT NULL,
  `text` longtext CHARACTER SET utf8mb4 NOT NULL,
  `subtitles` longtext NOT NULL,
  `date` int(11) NOT NULL,
  `lang` varchar(11) NOT NULL DEFAULT '0',
  `count_views` int(11) NOT NULL,
  `count_comments` int(11) NOT NULL,
  `add_date` datetime NOT NULL,
  `end_date` datetime NOT NULL,
  UNIQUE KEY `owner_id` (`owner_id`, `item_id`) USING BTREE,
  KEY `res_id` (`res_id`)
)DEFAULT CHARSET=utf8;
