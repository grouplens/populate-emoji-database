USE emojistudy_db;

DROP TABLE IF EXISTS renderings;
DROP TABLE IF EXISTS platform_versions;
DROP TABLE IF EXISTS platforms;

CREATE TABLE IF NOT EXISTS platforms (
    platform_id TINYINT NOT NULL AUTO_INCREMENT,
    platform_name VARCHAR(20) NOT NULL UNIQUE,
    platform_display_name VARCHAR(20),
    PRIMARY KEY (platform_id)
);

CREATE TABLE IF NOT EXISTS platform_versions (
    platform_version_id SMALLINT NOT NULL AUTO_INCREMENT,
    platform_id TINYINT,
    version_name VARCHAR(50) NOT NULL UNIQUE,
    version_display_name VARCHAR(50),
    release_date DATE DEFAULT NULL,
    in_use BOOLEAN,
    emojipedia_url_ext VARCHAR(50),
    prev_version_id SMALLINT,
    post_version_id SMALLINT,
    num_emoji SMALLINT,
    num_changed_emoji SMALLINT,
    num_new_emoji SMALLINT,
    num_removed_emoji SMALLINT,
    PRIMARY KEY (platform_version_id),
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id),
    FOREIGN KEY (prev_version_id) REFERENCES platform_versions(platform_version_id),
    FOREIGN KEY (post_version_id) REFERENCES platform_versions(platform_version_id)
);

CREATE TABLE IF NOT EXISTS renderings (
    rendering_id MEDIUMINT NOT NULL AUTO_INCREMENT,
    emoji_id SMALLINT,
    platform_version_id SMALLINT,
    display_url VARCHAR(250),
    is_new BOOLEAN DEFAULT NULL,
    is_changed BOOLEAN DEFAULT NULL,
    PRIMARY KEY (rendering_id),
    FOREIGN KEY (emoji_id) REFERENCES emoji(emoji_id),
    FOREIGN KEY (platform_version_id) REFERENCES platform_versions(platform_version_id)
);

COMMIT;