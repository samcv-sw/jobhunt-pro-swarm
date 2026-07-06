/**
 * JobHunt Pro — SQLite Wasm + OPFS Client Engine v1.0
 * Bypasses centralized DB cost to zero-cost decentralized client-side storage.
 * Runs in browser background worker / main thread using OPFS (Origin Private File System).
 */

const SQLITE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.12.0/sql-wasm.js";
const WASM_CDN = "https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.12.0/sql-wasm.wasm";

let dbInstance: any = null;

export interface QueryResult {
  columns: string[];
  values: any[][];
}

/**
 * Initialize WebAssembly SQLite in browser
 */
export async function getClientDB(): Promise<any> {
  if (typeof window === "undefined") return null; // Bypasses Server-Side Rendering (SSR)
  if (dbInstance) return dbInstance;

  return new Promise((resolve, reject) => {
    // 1. Dynamic CDN inject to keep build bundles zero-dependency
    const script = document.createElement("script");
    script.src = SQLITE_CDN;
    script.onload = async () => {
      try {
        const initSqlJs = (window as any).initSqlJs;
        if (!initSqlJs) {
          throw new Error("initSqlJs is undefined on window");
        }

        const SQL = await initSqlJs({
          locateFile: () => WASM_CDN
        });

        // 2. Try loading from OPFS (Origin Private File System)
        let savedData: Uint8Array | null = null;
        try {
          if (navigator.storage && navigator.storage.getDirectory) {
            const root = await navigator.storage.getDirectory();
            const fileHandle = await root.getFileHandle("jobhunt_local.db", { create: true });
            const file = await fileHandle.getFile();
            const buffer = await file.arrayBuffer();
            if (buffer.byteLength > 0) {
              savedData = new Uint8Array(buffer);
            }
          }
        } catch (opfsErr) {
          console.warn("[WASM-DB] OPFS access failed, falling back to Memory/IndexedDB:", opfsErr);
        }

        // 3. Instantiate SQLite instance
        const db = savedData ? new SQL.Database(savedData) : new SQL.Database();
        
        // 4. Initialize Local Schemas
        db.run(`
          CREATE TABLE IF NOT EXISTS local_cv_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cv_text TEXT,
            skills TEXT,
            experience_years INTEGER,
            target_titles TEXT,
            target_locations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          );

          CREATE TABLE IF NOT EXISTS local_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id TEXT UNIQUE,
            status TEXT DEFAULT 'pending',
            total_companies INTEGER DEFAULT 0,
            sent_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          );

          CREATE TABLE IF NOT EXISTS local_sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT,
            table_name TEXT,
            payload TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          );
        `);

        // 5. Setup auto-persist on mutation
        const originalRun = db.run.bind(db);
        db.run = (sql: string, params?: any) => {
          const res = originalRun(sql, params);
          persistDB(db).catch(console.error);
          return res;
        };

        dbInstance = db;
        resolve(db);
      } catch (err) {
        reject(err);
      }
    };
    script.onerror = () => reject(new Error("Failed to load SQL.js Wasm script"));
    document.head.appendChild(script);
  });
}

/**
 * Persist database state back to OPFS
 */
async function persistDB(db: any): Promise<void> {
  try {
    if (navigator.storage && navigator.storage.getDirectory) {
      const binary = db.export();
      const root = await navigator.storage.getDirectory();
      const fileHandle = await root.getFileHandle("jobhunt_local.db", { create: true });
      const writable = await (fileHandle as any).createWritable();
      await writable.write(binary);
      await writable.close();
    }
  } catch (err) {
    console.error("[WASM-DB] Persistence failed:", err);
  }
}

/**
 * Execute a query and format results
 */
export async function runLocalQuery(sql: string, params?: any): Promise<QueryResult[]> {
  const db = await getClientDB();
  if (!db) return [];
  try {
    const stmt = db.prepare(sql);
    stmt.bind(params);
    const results: QueryResult[] = [];
    while (stmt.step()) {
      const row = stmt.getAsObject();
      const columns = Object.keys(row);
      const values = [Object.values(row)];
      results.push({ columns, values });
    }
    stmt.free();
    return results;
  } catch (err) {
    console.error("[WASM-DB] Query failed:", err);
    throw err;
  }
}

