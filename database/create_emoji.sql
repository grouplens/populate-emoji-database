USE emojistudy_db;

DROP TABLE IF EXISTS emoji_codepoints;
DROP TABLE IF EXISTS codepoints;
DROP TABLE IF EXISTS emoji;

CREATE TABLE IF NOT EXISTS emoji (
    emoji_id SMALLINT NOT NULL AUTO_INCREMENT,
    emoji_name VARCHAR(150),
    emojipedia_url_ext VARCHAR(150) UNIQUE,
    emojipedia_category VARCHAR(50),
    codepoint_string VARCHAR(150) UNIQUE,
    num_codepoints TINYINT,
    num_platforms_support TINYINT,
    num_renderings TINYINT,
    num_changed_renderings TINYINT,
    hasComponent BOOLEAN DEFAULT NULL,
    hasModifier BOOLEAN DEFAULT NULL,
    hasModifierBase BOOLEAN DEFAULT NULL,
    appearance_differs_flag BOOLEAN,
    unicode_not_recommended BOOLEAN,
    num_tweets INT DEFAULT 0,
    num_filtered_tweets INT DEFAULT 0,
    num_invited_tweets INT DEFAULT 0,
    num_study_tweets INT DEFAULT 0,
    PRIMARY KEY (emoji_id)
);

CREATE TABLE IF NOT EXISTS codepoints (
    codepoint_id SMALLINT NOT NULL AUTO_INCREMENT,
    codepoint VARCHAR(7) NOT NULL UNIQUE,
    isComponent BOOLEAN DEFAULT NULL,
    isModifier BOOLEAN DEFAULT NULL,
    isModifierBase BOOLEAN DEFAULT NULL,
    PRIMARY KEY (codepoint_id)
);

CREATE TABLE IF NOT EXISTS emoji_codepoints (
    emoji_codepoint_id MEDIUMINT NOT NULL AUTO_INCREMENT,
    emoji_id SMALLINT,
    codepoint_id SMALLINT,
    sequence_index TINYINT,
    PRIMARY KEY (emoji_codepoint_id),
    FOREIGN KEY (emoji_id) REFERENCES emoji(emoji_id),
    FOREIGN KEY (codepoint_id) REFERENCES codepoints(codepoint_id)
);

COMMIT;