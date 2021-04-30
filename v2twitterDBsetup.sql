-- database structure for twitter-app v2 of twitter api

CREATE DATABASE IF NOT EXISTS TwitterV2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE TwitterV2;

-- DROP TABLE Tweets;
-- DROP TABLE Users;
-- DROP TABLE Said_by;
-- DROP TABLE Hashtags;
-- DROP TABLE Urls;
-- DROP TABLE User_mentions;
-- DROP TABLE Media;
-- DROP TABLE Poll;


CREATE TABLE Tweets (
	id_str			VARCHAR(50) NOT NULL,
	_text			VARCHAR(280) NOT NULL,
	created_at		VARCHAR(30) NOT NULL,
	source			VARCHAR(150) NOT NULL,
	quote_count		INT UNSIGNED DEFAULT 0,
	reply_count		INT UNSIGNED DEFAULT 0,
	retweet_count	INT UNSIGNED NOT NULL,
	favorite_count	INT UNSIGNED,	-- likes
	lang			VARCHAR(3),
	x_coor			REAL,			-- inside "coordinates"
	y_coor			REAL,
	last_updated	VARCHAR(30) NOT NULL,
	last_accessed	VARCHAR(30) NOT NULL,
	in_reply_to_user_id     VARCHAR(50) DEFAULT NULL,		-- added for V2, determines if tweet is a reply
	conversation_id		VARCHAR(50) DEFAULT NULL, 		-- added for V2, gets the ID of original Tweet of conversation. Direct replies, and replies of replies included
	PRIMARY KEY (id_str)
	);

CREATE TABLE Users (
	id_str					VARCHAR(50) NOT NULL,
	screen_name				VARCHAR(50) NOT NULL,
	_name					VARCHAR(50) NOT NULL,
	created_at				VARCHAR(30) NOT NULL,
	location				VARCHAR(30),
	followers_count			INT UNSIGNED NOT NULL,
	friends_count			INT UNSIGNED NOT NULL,
	listed_count			INT UNSIGNED NOT NULL,
	statuses_count			INT UNSIGNED NOT NULL,  -- including retweets
	default_profile			VARCHAR(5) NOT NULL,	-- bool
	default_profile_image	VARCHAR(5) NOT NULL,	-- converts to a 1 or 0
	last_updated	VARCHAR(30) NOT NULL,
	last_accessed	VARCHAR(30) NOT NULL,
	private_tweets	VARCHAR(5) DEFAULT NULL,			-- Determines if the user has made their tweets private V2 API
	verified_user	VARCHAR(5) DEFAULT NULL, 			-- Determines if the account has been verified by Twitter V2 API
	PRIMARY KEY (id_str)
	);

CREATE TABLE Timelines (
	user_id				VARCHAR(50) NOT NULL,
	retrieval_date		VARCHAR(30) NOT NULL,
	PRIMARY KEY (user_id)
	);

CREATE TABLE Said_by (
	tweet_id_str	VARCHAR(50) NOT NULL,
	user_id_str		VARCHAR(50) NOT NULL,
	PRIMARY KEY (tweet_id_str, user_id_str)
	);

CREATE TABLE Hashtags (
	_text		VARCHAR(140) NOT NULL,	-- excludes the #
	tweet_id	VARCHAR(50) NOT NULL,
	FOREIGN KEY (tweet_id)
		REFERENCES Tweets (id_str)
		ON DELETE CASCADE
	);

CREATE TABLE Urls (		-- found under the 'unwound' attribute
	url 		VARCHAR(1000) NOT NULL,
	tweet_id	VARCHAR(50) NOT NULL,
	FOREIGN KEY (tweet_id)
		REFERENCES Tweets (id_str)
		ON DELETE CASCADE
	);

CREATE TABLE User_mentions (
	_name		VARCHAR(50) NOT NULL,	-- the person mentioned
	screen_name	VARCHAR(50) NOT NULL,
	id_str		VARCHAR(50) NOT NULL UNIQUE,	-- the mentioned persons user_id
	tweet_id	VARCHAR(50) NOT NULL,	-- the tweet they were mentioned in
	FOREIGN KEY (tweet_id)
		REFERENCES Tweets (id_str)
		ON DELETE CASCADE
	);

CREATE TABLE Media (
	id_str					VARCHAR(50) NOT NULL UNIQUE,
	display_url				VARCHAR(100) NOT NULL,
	type					VARCHAR(20) NOT NULL,
	source_status_id_str	VARCHAR(50),	-- Tweets containing media that was originally associated with a different tweet
	tweet_id				VARCHAR(50) NOT NULL,
	FOREIGN KEY (tweet_id)
		REFERENCES Tweets (id_str)
		ON DELETE CASCADE
	);
