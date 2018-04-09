CREATE TABLE users(
  	user_id VARCHAR(40),
  	playlist_setting VARCHAR(10) NOT NULL DEFAULT 'weekly',
  	hybrid_num_weeks INTEGER,
  	num_hybrid_playlists INTEGER,
  	global_playlist_id VARCHAR(40) DEFAULT NULL,
  	refresh_token VARCHAR(40) NOT NULL,
  	PRIMARY KEY(user_id)
);

CREATE TABLE user_playlists(
	playlist_id VARCHAR(40),
	owner_id VARCHAR(40) NOT NULL,
	age_in_weeks INTEGER DEFAULT 0,
	FOREIGN KEY (owner_id) REFERENCES users(user_id),
	PRIMARY KEY(playlist_id)
);