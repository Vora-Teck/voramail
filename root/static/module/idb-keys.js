// idb-keys.js
//import * as API from "./api.js";

const DB_NAME = "eduka_ai_v1";
const DB_VERSION = 1;
const STORE_META = "meta";           // key -> value (school_info, email, api_token, device_id, etc)
const STORE_KEYS = "keys";
//const EXPIRY_HOURS = 24;


async function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      //console.log(db.objectStoreNames)
      if (!db.objectStoreNames.contains(STORE_META)) db.createObjectStore(STORE_META);
      if (!db.objectStoreNames.contains(STORE_KEYS)) db.createObjectStore(STORE_KEYS);
    };
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror = (e) => reject(e.target.error);
  });
}

export async function idbPut(storeName, key, value) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(storeName, "readwrite");
    tx.objectStore(storeName).put(value, key);
    tx.oncomplete = () => res(true);
    tx.onerror = (e) => rej(e.target.error);
  });
}

export async function idbGet(storeName, key) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(storeName, "readonly");
    const rq = tx.objectStore(storeName).get(key);
    rq.onsuccess = () => res(rq.result);
    rq.onerror = (e) => rej(e.target.error);
  });
}

export async function idbDelete(storeName, key) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(storeName, "readwrite");
    tx.objectStore(storeName).delete(key);
    tx.oncomplete = () => res(true);
    tx.onerror = (e) => rej(e.target.error);
  });
}

// --- Meta helpers (school_info, user_info)
export function setMeta(key, value) { return idbPut(STORE_META, key, value); }
export function getMeta(key) { return idbGet(STORE_META, key); }
export function delMeta(key) { return idbDelete(STORE_META, key); }


// --- Key helpers (public/private)
export function putKey(keyName, data){ return idbPut(STORE_KEYS, keyName, data) }
export function getKey(keyName){ return idbGet(STORE_KEYS, keyName) }
export function deleteKey(keyName) { return idbDelete(STORE_KEYS, keyName); }

