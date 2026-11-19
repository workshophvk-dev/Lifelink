-- LifeLink: Blood and Body Stock Monitor (MySQL 8+)
-- IMPORTANT: All rows below are SAMPLE / SYNTHETIC data for testing.
-- They are NOT real-time or real-world figures. Replace by loading from
-- real sources (hospital/blood bank feeds, e-RaktKosh, national registries).

CREATE DATABASE IF NOT EXISTS lifelink CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE lifelink;

DROP VIEW  IF EXISTS v_low_blood_stock;
DROP VIEW  IF EXISTS v_body_program_status;
DROP TABLE IF EXISTS blood_stock_log;
DROP TABLE IF EXISTS blood_stock;
DROP TABLE IF EXISTS body_donation_program;
DROP TABLE IF EXISTS facilities;

CREATE TABLE facilities (
  facility_id   INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(150) NOT NULL,
  type          ENUM('blood_bank','hospital','medical_college') NOT NULL,
  city          VARCHAR(80)  NOT NULL,
  state_region  VARCHAR(80),
  country       VARCHAR(80)  NOT NULL,
  latitude      DECIMAL(9,6),
  longitude     DECIMAL(9,6),
  UNIQUE KEY uq_fac (name, city, country)
) ENGINE=InnoDB;

CREATE TABLE blood_stock (
  facility_id  INT NOT NULL,
  blood_group  ENUM('O-','O+','A-','A+','B-','B+','AB-','AB+') NOT NULL,
  units        INT NOT NULL DEFAULT 0 CHECK (units >= 0),
  safe_level   INT NOT NULL DEFAULT 20,
  updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (facility_id, blood_group),
  FOREIGN KEY (facility_id) REFERENCES facilities(facility_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE blood_stock_log (
  log_id       BIGINT AUTO_INCREMENT PRIMARY KEY,
  facility_id  INT NOT NULL,
  blood_group  ENUM('O-','O+','A-','A+','B-','B+','AB-','AB+') NOT NULL,
  change_units INT NOT NULL,            -- +donation, -issued
  reason       ENUM('donation','issue','expiry','transfer','adjustment') NOT NULL,
  logged_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_fac_time (facility_id, logged_at),
  FOREIGN KEY (facility_id) REFERENCES facilities(facility_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Body donation is not a "stock" in the public sense: this tracks pledges and
-- medical-college capacity for education/research, not inventory for sale.
CREATE TABLE body_donation_program (
  facility_id       INT PRIMARY KEY,    -- must be a medical_college
  pledges_registered INT NOT NULL DEFAULT 0,
  bodies_received_ytd INT NOT NULL DEFAULT 0,
  teaching_capacity  INT NOT NULL DEFAULT 0,
  updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (facility_id) REFERENCES facilities(facility_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE VIEW v_low_blood_stock AS
SELECT f.name, f.city, f.country, s.blood_group, s.units, s.safe_level,
       (s.safe_level - s.units) AS shortfall, s.updated_at
FROM blood_stock s JOIN facilities f USING (facility_id)
WHERE s.units < s.safe_level
ORDER BY shortfall DESC;

CREATE VIEW v_body_program_status AS
SELECT f.name, f.city, f.country, b.pledges_registered, b.bodies_received_ytd,
       b.teaching_capacity,
       (b.teaching_capacity - b.bodies_received_ytd) AS capacity_gap
FROM body_donation_program b JOIN facilities f USING (facility_id);

-- ---------- SAMPLE DATA (synthetic) ----------
INSERT INTO facilities (name, type, city, state_region, country, latitude, longitude) VALUES
('Sample Blood Bank Pune',   'blood_bank',      'Pune',   'Maharashtra', 'India', 18.5204, 73.8567),
('Sample Hospital Mumbai',   'hospital',        'Mumbai', 'Maharashtra', 'India', 19.0760, 72.8777),
('Sample Medical College Nagpur','medical_college','Nagpur','Maharashtra','India', 21.1458, 79.0882),
('Sample Blood Bank London', 'blood_bank',      'London', 'England',     'UK',    51.5072, -0.1276),
('Sample Blood Bank Nairobi','blood_bank',      'Nairobi','Nairobi',     'Kenya', -1.2921, 36.8219);

INSERT INTO blood_stock (facility_id, blood_group, units, safe_level) VALUES
(1,'O-',12,20),(1,'O+',48,40),(1,'A-',9,15),(1,'A+',35,30),
(1,'B-',7,15),(1,'B+',41,35),(1,'AB-',4,10),(1,'AB+',18,15),
(2,'O-',22,20),(2,'O+',60,40),(2,'A-',14,15),(2,'A+',38,30),
(2,'B-',11,15),(2,'B+',44,35),(2,'AB-',8,10),(2,'AB+',20,15),
(4,'O-',30,25),(4,'O+',70,50),(4,'A+',52,40),(4,'B+',33,30),
(5,'O+',25,30),(5,'A+',19,25),(5,'B+',21,25),(5,'O-',6,12);

INSERT INTO blood_stock_log (facility_id, blood_group, change_units, reason) VALUES
(1,'O-', 5,'donation'),(1,'B-',-2,'issue'),(2,'A+',10,'donation'),(5,'O-',-3,'issue');

INSERT INTO body_donation_program (facility_id, pledges_registered, bodies_received_ytd, teaching_capacity) VALUES
(3, 120, 14, 30);

-- Example queries
-- SELECT * FROM v_low_blood_stock;
-- SELECT blood_group, SUM(units) AS total_units FROM blood_stock GROUP BY blood_group;
-- SELECT * FROM v_body_program_status;
