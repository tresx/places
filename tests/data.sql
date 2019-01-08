-- Insert two users, password for both is 'p'
INSERT INTO users (email, password)
VALUES
    ('user1@example.com', 'pbkdf2:sha256:50000$X3Ei072U$4eb641d28a2d100aed52681478855a61ff82214de7f20e3ab1417c3c98a99ae8'),
    ('user2@example.com', 'pbkdf2:sha256:50000$X3Ei072U$4eb641d28a2d100aed52681478855a61ff82214de7f20e3ab1417c3c98a99ae8');


INSERT INTO locations (user_id, name, description, postcode, lat, lng)
VALUES
    (
        1,
        'The Eagle',
        'Watson and Crick''s legendary watering hole.',
        'CB2 3QN',
        52.2042,
        0.118223
    ),
    (
        1,
        'King''s College Chapel',
        'Late Gothic edifice with a vast fan ceiling, ornate stained glass windows and CofE services.',
        'CB2 1ST',
        52.2043,
        0.116434
    ),
    (
        1,
        'The Mill',
        'Renovated traditional riverside pub serving cask ales, craft beer and hearty food.',
        'CB2 1RX',
        52.2015,
        0.117082
    ),
    (
        1,
        'Mathematical Bridge',
        'This historical footbridge was built with all straight timbers & thoughtful engineering.',
        'CB3 9ET',
        52.2021,
        0.113977
    );


INSERT INTO reviews (user_id, location_id, rating, review)
VALUES
    (1, 1, 4, 'Pretty good.'),
    (2, 1, 5, 'Great.');
