import Database from "better-sqlite3";
import * as path from "path";
import * as fs from "fs/promises";

export interface DocSection {
  id: number;
  title: string;
  url: string;
  content: string;
  section: string;
  doc_type: "api_reference" | "tutorial" | "example" | "guide";
  created_at: string;
  updated_at: string;
}

export class DocsStorage {
  private db: Database.Database;
  private dbPath: string;

  constructor(dbPath: string) {
    this.dbPath = dbPath;
    // Ensure data directory exists
    const dir = path.dirname(dbPath);
    fs.mkdir(dir, { recursive: true }).catch(() => {});
    
    this.db = new Database(dbPath);
    this.initializeSchema();
  }

  private initializeSchema() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS doc_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        content TEXT NOT NULL,
        section TEXT NOT NULL,
        doc_type TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
      );
      
      CREATE INDEX IF NOT EXISTS idx_url ON doc_sections(url);
      CREATE INDEX IF NOT EXISTS idx_doc_type ON doc_sections(doc_type);
      CREATE INDEX IF NOT EXISTS idx_section ON doc_sections(section);
      
      CREATE VIRTUAL TABLE IF NOT EXISTS doc_sections_fts USING fts5(
        title,
        content,
        section,
        content_rowid=id
      );
    `);
  }

  insertSection(
    title: string,
    url: string,
    content: string,
    section: string,
    docType: "api_reference" | "tutorial" | "example" | "guide"
  ) {
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO doc_sections (title, url, content, section, doc_type, updated_at)
      VALUES (?, ?, ?, ?, ?, datetime('now'))
    `);
    
    stmt.run(title, url, content, section, docType);
    
    // Update FTS index
    const ftsStmt = this.db.prepare(`
      INSERT OR REPLACE INTO doc_sections_fts (rowid, title, content, section)
      VALUES ((SELECT id FROM doc_sections WHERE url = ?), ?, ?, ?)
    `);
    ftsStmt.run(url, title, content, section);
  }

  clearAll() {
    this.db.exec(`
      DELETE FROM doc_sections;
      DELETE FROM doc_sections_fts;
    `);
  }

  searchDocs(query: string, limit: number = 5): DocSection[] {
    const stmt = this.db.prepare(`
      SELECT ds.* FROM doc_sections ds
      JOIN doc_sections_fts fts ON ds.id = fts.rowid
      WHERE doc_sections_fts MATCH ?
      ORDER BY rank
      LIMIT ?
    `);
    
    // Escape FTS5 query syntax
    const escapedQuery = query
      .replace(/"/g, '""')
      .split(/\s+/)
      .filter((w) => w.length > 0)
      .map((w) => `"${w}"*`)
      .join(" OR ");
    
    try {
      const results = stmt.all(escapedQuery, limit) as DocSection[];
      return results;
    } catch (error) {
      // If FTS query fails, fall back to simple LIKE search
      const fallbackStmt = this.db.prepare(`
        SELECT * FROM doc_sections
        WHERE title LIKE ? OR content LIKE ? OR section LIKE ?
        LIMIT ?
      `);
      const pattern = `%${query}%`;
      return fallbackStmt.all(pattern, pattern, pattern, limit) as DocSection[];
    }
  }

  getApiReference(topic: string): DocSection[] {
    const stmt = this.db.prepare(`
      SELECT * FROM doc_sections
      WHERE doc_type = 'api_reference'
        AND (title LIKE ? OR content LIKE ? OR section LIKE ?)
      ORDER BY 
        CASE 
          WHEN title LIKE ? THEN 1
          WHEN section LIKE ? THEN 2
          ELSE 3
        END
      LIMIT 10
    `);
    
    const pattern = `%${topic}%`;
    return stmt.all(
      pattern,
      pattern,
      pattern,
      pattern,
      pattern
    ) as DocSection[];
  }

  getExamples(exampleType: string): DocSection[] {
    const stmt = this.db.prepare(`
      SELECT * FROM doc_sections
      WHERE doc_type = 'example'
        AND (title LIKE ? OR section LIKE ? OR content LIKE ?)
      LIMIT 10
    `);
    
    const pattern = `%${exampleType}%`;
    return stmt.all(pattern, pattern, pattern) as DocSection[];
  }

  getLastUpdateTime(): Date | null {
    const stmt = this.db.prepare(`
      SELECT MAX(updated_at) as last_update FROM doc_sections
    `);
    const result = stmt.get() as { last_update: string | null } | undefined;
    if (result?.last_update) {
      return new Date(result.last_update);
    }
    return null;
  }

  close() {
    this.db.close();
  }
}

