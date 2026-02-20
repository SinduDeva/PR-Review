-- PR Review Audit Database Schema
-- Initialize MySQL database for PR review tracking and audit trail

-- Create database
CREATE DATABASE IF NOT EXISTS pr_review_audit;
USE pr_review_audit;

-- Table 1: pr_review_run
-- Main execution record for each PR review run
CREATE TABLE IF NOT EXISTS pr_review_run (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(36) UNIQUE NOT NULL COMMENT 'UUID for this run',
    pr_number INT NOT NULL COMMENT 'Pull Request number',
    repo VARCHAR(255) COMMENT 'Repository name',
    workspace VARCHAR(255) COMMENT 'Workspace/organization name',
    source_branch VARCHAR(255) NOT NULL COMMENT 'Source branch name',
    target_branch VARCHAR(255) NOT NULL COMMENT 'Target branch name',
    reviewer VARCHAR(255) DEFAULT 'Automated Review System' COMMENT 'Who performed the review',
    workflow_file VARCHAR(255) COMMENT 'Path to workflow file',
    workflow_sha256 VARCHAR(64) COMMENT 'SHA256 checksum of workflow',
    started_at DATETIME COMMENT 'When execution started',
    finished_at DATETIME COMMENT 'When execution finished',
    status VARCHAR(50) COMMENT 'Overall status (success, completed_with_errors, etc)',
    execution_seconds INT COMMENT 'Total execution time in seconds',
    files_changed INT COMMENT 'Total files changed in PR',
    files_validated INT COMMENT 'Files reviewed by workflow',
    critical_issues INT DEFAULT 0 COMMENT 'Count of CRITICAL severity issues',
    high_issues INT DEFAULT 0 COMMENT 'Count of HIGH severity issues',
    medium_issues INT DEFAULT 0 COMMENT 'Count of MEDIUM severity issues',
    low_issues INT DEFAULT 0 COMMENT 'Count of LOW severity issues',
    test_coverage VARCHAR(10) COMMENT 'Overall test coverage percentage',
    risk_level VARCHAR(50) COMMENT 'Risk level assessment (LOW, MEDIUM, HIGH)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pr_number (pr_number),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 2: pr_review_step
-- Track execution status of each workflow step
CREATE TABLE IF NOT EXISTS pr_review_step (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL COMMENT 'Reference to pr_review_run.run_id',
    step_key VARCHAR(100) NOT NULL COMMENT 'Step identifier (e.g., step_0_pr_detection)',
    status VARCHAR(50) COMMENT 'Step status (success, failed, skipped, etc)',
    attempted BOOLEAN DEFAULT TRUE COMMENT 'Whether step was attempted',
    fallback_used BOOLEAN DEFAULT FALSE COMMENT 'Whether fallback method was used',
    error_message TEXT COMMENT 'Error message if step failed',
    note TEXT COMMENT 'Additional notes about step execution',
    started_at DATETIME COMMENT 'When step started',
    finished_at DATETIME COMMENT 'When step finished',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES pr_review_run(run_id) ON DELETE CASCADE,
    INDEX idx_run_id (run_id),
    INDEX idx_step_key (step_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 3: pr_review_file
-- Track analysis results for each file in the PR
CREATE TABLE IF NOT EXISTS pr_review_file (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL COMMENT 'Reference to pr_review_run.run_id',
    path VARCHAR(512) NOT NULL COMMENT 'File path in repository',
    layer VARCHAR(100) COMMENT 'Architectural layer (service, controller, etc)',
    status VARCHAR(50) COMMENT 'File status (ADDED, MODIFIED, DELETED)',
    lines_added INT DEFAULT 0 COMMENT 'Lines added in this file',
    lines_deleted INT DEFAULT 0 COMMENT 'Lines deleted in this file',
    summary TEXT COMMENT 'Summary of changes to this file',
    ai_summary TEXT COMMENT 'AI generated summary of changes',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES pr_review_run(run_id) ON DELETE CASCADE,
    INDEX idx_run_id (run_id),
    INDEX idx_path (path(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 4: pr_review_finding
-- Track each code review finding/issue
CREATE TABLE IF NOT EXISTS pr_review_finding (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL COMMENT 'Reference to pr_review_run.run_id',
    finding_id VARCHAR(50) NOT NULL COMMENT 'Finding identifier (FIND-001, etc)',
    severity VARCHAR(50) NOT NULL COMMENT 'Severity level (CRITICAL, HIGH, MEDIUM, LOW)',
    type VARCHAR(100) COMMENT 'Finding type (Bug, Security, Performance, etc)',
    title VARCHAR(255) NOT NULL COMMENT 'Finding title/summary',
    file_path VARCHAR(512) COMMENT 'File where finding was detected',
    line_no INT COMMENT 'Line number of finding',
    description TEXT COMMENT 'Detailed description of the issue',
    impact TEXT COMMENT 'Impact of this issue',
    suggestion TEXT COMMENT 'Suggested resolution',
    suggested_fix TEXT COMMENT 'Proposed code fix',
    code_snippet LONGTEXT COMMENT 'Code snippet showing the issue',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES pr_review_run(run_id) ON DELETE CASCADE,
    INDEX idx_run_id (run_id),
    INDEX idx_severity (severity),
    INDEX idx_finding_id (finding_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 5: pr_review_graph_node
-- Dependency graph nodes (files, classes, methods)
CREATE TABLE IF NOT EXISTS pr_review_graph_node (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL COMMENT 'Reference to pr_review_run.run_id',
    node_id VARCHAR(255) NOT NULL COMMENT 'Unique node identifier',
    label VARCHAR(255) COMMENT 'Display label for the node',
    layer VARCHAR(100) COMMENT 'Architectural layer',
    color VARCHAR(50) COMMENT 'Visual color for the node',
    status VARCHAR(50) COMMENT 'Node status (added, modified, unchanged)',
    file_path VARCHAR(512) COMMENT 'File path this node represents',
    props_json JSON COMMENT 'Additional properties as JSON',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES pr_review_run(run_id) ON DELETE CASCADE,
    INDEX idx_run_id (run_id),
    INDEX idx_node_id (node_id(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 6: pr_review_graph_edge
-- Dependency graph edges (relationships between nodes)
CREATE TABLE IF NOT EXISTS pr_review_graph_edge (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL COMMENT 'Reference to pr_review_run.run_id',
    source_id VARCHAR(255) NOT NULL COMMENT 'Source node identifier',
    target_id VARCHAR(255) NOT NULL COMMENT 'Target node identifier',
    edge_type VARCHAR(100) COMMENT 'Type of edge (DEPENDS_ON, CALLS, etc)',
    relationship VARCHAR(255) COMMENT 'Human-readable relationship',
    props_json JSON COMMENT 'Additional properties as JSON',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES pr_review_run(run_id) ON DELETE CASCADE,
    INDEX idx_run_id (run_id),
    INDEX idx_source (source_id(255)),
    INDEX idx_target (target_id(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Summary of all reviews by PR
CREATE OR REPLACE VIEW v_pr_review_summary AS
SELECT
    pr_number,
    COUNT(DISTINCT run_id) as total_runs,
    MAX(started_at) as last_review_date,
    SUM(critical_issues) as total_critical,
    SUM(high_issues) as total_high,
    AVG(execution_seconds) as avg_execution_time,
    GROUP_CONCAT(DISTINCT risk_level) as risk_levels
FROM pr_review_run
GROUP BY pr_number;

-- View: Finding statistics
CREATE OR REPLACE VIEW v_finding_statistics AS
SELECT
    severity,
    COUNT(*) as count,
    COUNT(DISTINCT run_id) as affecting_runs,
    COUNT(DISTINCT file_path) as affecting_files,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM pr_review_finding), 2) as percentage
FROM pr_review_finding
GROUP BY severity
ORDER BY FIELD(severity, 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW');

-- View: Top problematic files
CREATE OR REPLACE VIEW v_top_problematic_files AS
SELECT
    file_path,
    COUNT(DISTINCT run_id) as times_reviewed,
    COUNT(*) as total_findings,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
    SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high_count
FROM pr_review_finding
WHERE file_path IS NOT NULL
GROUP BY file_path
HAVING total_findings > 0
ORDER BY total_findings DESC
LIMIT 20;

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

-- Procedure: Get PR review history
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS sp_get_pr_review_history(IN p_pr_number INT)
BEGIN
    SELECT
        run_id,
        started_at,
        finished_at,
        status,
        critical_issues,
        high_issues,
        medium_issues,
        low_issues,
        risk_level
    FROM pr_review_run
    WHERE pr_number = p_pr_number
    ORDER BY started_at DESC;
END //
DELIMITER ;

-- Procedure: Get findings for a specific run
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS sp_get_run_findings(IN p_run_id VARCHAR(36))
BEGIN
    SELECT
        finding_id,
        severity,
        type,
        title,
        file_path,
        line_no,
        description,
        suggested_fix
    FROM pr_review_finding
    WHERE run_id = p_run_id
    ORDER BY
        FIELD(severity, 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'),
        file_path;
END //
DELIMITER ;

-- Procedure: Calculate metrics for a run
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS sp_calculate_run_metrics(IN p_run_id VARCHAR(36))
BEGIN
    SELECT
        p_run_id as run_id,
        COUNT(DISTINCT prf.path) as total_files,
        COUNT(DISTINCT f.id) as total_findings,
        SUM(CASE WHEN f.severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_issues,
        SUM(CASE WHEN f.severity = 'HIGH' THEN 1 ELSE 0 END) as high_issues,
        COUNT(DISTINCT f.type) as unique_issue_types,
        GROUP_CONCAT(DISTINCT f.type) as issue_types
    FROM pr_review_file prf
    LEFT JOIN pr_review_finding f ON prf.run_id = f.run_id AND prf.path = f.file_path
    WHERE prf.run_id = p_run_id;
END //
DELIMITER ;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_run_created ON pr_review_run(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_step_run_key ON pr_review_step(run_id, step_key);
CREATE INDEX IF NOT EXISTS idx_finding_severity ON pr_review_finding(severity);
CREATE INDEX IF NOT EXISTS idx_file_run ON pr_review_file(run_id);
CREATE INDEX IF NOT EXISTS idx_node_run ON pr_review_graph_node(run_id);
CREATE INDEX IF NOT EXISTS idx_edge_run ON pr_review_graph_edge(run_id);

-- ============================================================================
-- INITIALIZATION QUERIES
-- ============================================================================

-- Verify all tables were created
SELECT
    TABLE_NAME,
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'pr_review_audit' AND TABLE_NAME = t.TABLE_NAME) as column_count
FROM INFORMATION_SCHEMA.TABLES t
WHERE TABLE_SCHEMA = 'pr_review_audit'
ORDER BY TABLE_NAME;
