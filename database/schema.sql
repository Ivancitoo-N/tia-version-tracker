-- TIA Version Tracker Database Schema
-- SQLite database for storing TIA Portal project snapshots and metadata

-- Projects table: stores basic TIA Portal project information
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Snapshots table: stores version snapshots of projects
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operator TEXT NOT NULL,
    file_name TEXT,
    file_hash TEXT UNIQUE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Tags table: stores individual tag metadata from each snapshot
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    tag_name TEXT NOT NULL,
    tag_type TEXT,
    tag_address TEXT,
    tag_description TEXT,
    hardware_reference TEXT,
    block_reference TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
);

-- Blocks table: stores PLC block information
CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    block_name TEXT NOT NULL,
    block_type TEXT,
    block_number INTEGER,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
);

-- Hardware table: stores hardware configuration
CREATE TABLE IF NOT EXISTS hardware (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    device_name TEXT NOT NULL,
    device_type TEXT,
    ip_address TEXT,
    rack_slot TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_snapshots_project_id ON snapshots(project_id);
CREATE INDEX IF NOT EXISTS idx_tags_snapshot_id ON tags(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(tag_name);
CREATE INDEX IF NOT EXISTS idx_blocks_snapshot_id ON blocks(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_hardware_snapshot_id ON hardware(snapshot_id);
