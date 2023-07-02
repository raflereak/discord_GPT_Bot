CREATE TABLE user_data (
  UID INT PRIMARY KEY,
  user_data TEXT,
  resetCount INT
);


CREATE TABLE chat_history (
  cid INT AUTO_INCREMENT PRIMARY KEY,
  role VARCHAR(255),
  message TEXT,
  uid INT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  resetCount INT,
  FOREIGN KEY (uid) REFERENCES user_data (UID)
);
