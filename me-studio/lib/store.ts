"use client";

// Everything lives on this device: the persona in localStorage, photos in
// IndexedDB. Nothing about you is kept on the server.

export type Persona = {
  state: "training" | "ready" | "failed";
  jobId: string;
  selfieCount: number;
  startedAt: number;
  loraUrl?: string;
  readyAt?: number;
  error?: string;
};

export type Photo = {
  id: string;
  prompt: string;
  createdAt: number;
  dataUrl: string;
};

const PERSONA_KEY = "me-studio.persona";
const DB_NAME = "me-studio";
const STORE = "photos";

export function loadPersona(): Persona | null {
  try {
    const raw = localStorage.getItem(PERSONA_KEY);
    return raw ? (JSON.parse(raw) as Persona) : null;
  } catch {
    return null;
  }
}

export function savePersona(p: Persona | null) {
  try {
    if (p) localStorage.setItem(PERSONA_KEY, JSON.stringify(p));
    else localStorage.removeItem(PERSONA_KEY);
  } catch {
    // Private browsing can block storage; the app still works for this visit.
  }
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      const store = req.result.createObjectStore(STORE, { keyPath: "id" });
      store.createIndex("createdAt", "createdAt");
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function tx<T>(mode: IDBTransactionMode, run: (s: IDBObjectStore) => IDBRequest<T> | void): Promise<T | undefined> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const t = db.transaction(STORE, mode);
    const req = run(t.objectStore(STORE));
    t.oncomplete = () => {
      db.close();
      resolve(req ? req.result : undefined);
    };
    t.onerror = () => {
      db.close();
      reject(t.error);
    };
  });
}

export async function addPhotos(photos: Photo[]) {
  await tx("readwrite", (s) => {
    for (const p of photos) s.put(p);
  });
}

export async function listPhotos(): Promise<Photo[]> {
  const all = (await tx<Photo[]>("readonly", (s) => s.getAll())) ?? [];
  return all.sort((a, b) => b.createdAt - a.createdAt);
}

export async function deletePhoto(id: string) {
  await tx("readwrite", (s) => s.delete(id));
}

export async function deleteAllPhotos() {
  await tx("readwrite", (s) => s.clear());
}

export function newId(): string {
  return crypto.randomUUID();
}
