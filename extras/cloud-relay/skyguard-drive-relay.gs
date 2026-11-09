/**
 * SKYGUARD Drive relay (v1) – Google Apps Script web app.
 * The phone app POSTs events/location lines and audio/video chunks here; this script writes them into
 * YOUR Google Drive under SKYGUARD/phone/<YYYY-MM-DD>. No Google Cloud project / OAuth client needed.
 *
 * Deploy once (from a browser where you are already signed in to Google):
 *   script.google.com -> New project -> paste this file -> Deploy -> New deployment -> type "Web app"
 *   Execute as: Me   |   Who has access: Anyone   -> Deploy -> Authorize (Advanced -> Go to project) -> copy the /exec URL.
 * The /exec URL is the secret: whoever has it can ADD files under SKYGUARD/ in your Drive (never read or delete).
 *
 * Protocol: see app/src/main/java/com/skyguard/radar/cloud/RelayPolicy.kt
 */
var ROOT = 'SKYGUARD';

function doGet() { return out({ ok: true, service: 'skyguard-drive-relay', v: 1 }); }

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(60000);
  try {
    var r = JSON.parse(e.postData.contents);
    return out(handle(r));
  } catch (err) {
    return out({ ok: false, error: String(err && err.message || err) });
  } finally {
    lock.releaseLock();
  }
}

function handle(r) {
  if (!r || r.v !== 1) throw new Error('version');
  var path = String(r.path || '');
  if (path.indexOf(ROOT + '/') !== 0 || /(^|\/)\.\.?(\/|$)/.test(path) || /\/\//.test(path)) throw new Error('bad path');
  var name = String(r.name || '');
  if (!name || /[\/\\]/.test(name) || name.length > 200) throw new Error('bad name');
  var bytes = Utilities.base64Decode(r.data || '');
  var folder = folderFor(path);
  if (r.op === 'append') return append(folder, name, String(r.mime || 'application/json'), Number(r.offset), bytes);
  if (r.op === 'part') return part(folder, path, name, String(r.mime || 'application/octet-stream'), Number(r.offset), Number(r.size), bytes);
  throw new Error('bad op');
}

/** Text log append, idempotent by byte offset. */
function append(folder, name, mime, offset, bytes) {
  var it = folder.getFilesByName(name);
  var f = it.hasNext() ? it.next() : null;
  var size = f ? f.getSize() : 0;
  var end = offset + bytes.length;
  if (f && size >= end && offset < size) return { ok: true, id: f.getId(), next: end, dup: true };
  if (size !== offset) return { ok: false, error: 'offset', size: size };
  if (!f) {
    f = folder.createFile(Utilities.newBlob(bytes, mime, name));
  } else {
    var old = f.getBlob().getBytes();
    f.setContent(Utilities.newBlob(old.concat(bytes)).getDataAsString('UTF-8'));
  }
  return { ok: true, id: f.getId(), next: end };
}

/** Binary chunk -> Drive resumable session (one normal file at the end). */
function part(folder, path, name, mime, offset, size, bytes) {
  if (!(size >= 0) || !(offset >= 0) || offset + bytes.length > size) throw new Error('bad range');
  var props = PropertiesService.getScriptProperties();
  var key = 'ses|' + path + '/' + name + '|' + size;
  var doneId = props.getProperty('done' + key);
  if (doneId) return { ok: true, id: doneId, done: true, next: size };
  var it = folder.getFilesByName(name);
  while (it.hasNext()) { var ex = it.next(); if (ex.getSize() === size) { props.setProperty('done' + key, ex.getId()); return { ok: true, id: ex.getId(), done: true, next: size }; } }

  var ses = props.getProperty(key);
  if (!ses) {
    if (offset !== 0) return { ok: false, error: 'restart' };
    ses = startSession(folder.getId(), name, mime, size);
    props.setProperty(key, ses);
  }
  var have = queryOffset(ses, size);
  if (have === null) { props.deleteProperty(key); return { ok: false, error: 'restart' }; }
  if (have.done) { props.setProperty('done' + key, have.id); props.deleteProperty(key); return { ok: true, id: have.id, done: true, next: size }; }
  if (have.next > offset) return { ok: true, next: have.next };          // duplicate chunk (lost reply)
  if (have.next < offset) return { ok: false, error: 'offset', size: have.next };

  var res = UrlFetchApp.fetch(ses, {
    method: 'put', contentType: mime, payload: bytes, muteHttpExceptions: true,
    headers: { 'Content-Range': size === 0 ? 'bytes */0' : 'bytes ' + offset + '-' + (offset + bytes.length - 1) + '/' + size }
  });
  var code = res.getResponseCode();
  if (code === 200 || code === 201) {
    var id = JSON.parse(res.getContentText()).id;
    props.setProperty('done' + key, id); props.deleteProperty(key);
    return { ok: true, id: id, done: true, next: size };
  }
  if (code === 308) return { ok: true, next: nextFromRange(res.getHeaders()) };
  if (code === 404 || code === 410) { props.deleteProperty(key); return { ok: false, error: 'restart' }; }
  throw new Error('drive ' + code + ' ' + res.getContentText().slice(0, 200));
}

function startSession(parentId, name, mime, size) {
  var res = UrlFetchApp.fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id', {
    method: 'post', contentType: 'application/json; charset=UTF-8', muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken(), 'X-Upload-Content-Type': mime, 'X-Upload-Content-Length': String(size) },
    payload: JSON.stringify({ name: name, parents: [parentId] })
  });
  if (res.getResponseCode() !== 200) throw new Error('session ' + res.getResponseCode() + ' ' + res.getContentText().slice(0, 200));
  var h = res.getHeaders();
  return h['Location'] || h['location'];
}

/** {next} | {done,id} | null (session expired). */
function queryOffset(ses, size) {
  var res = UrlFetchApp.fetch(ses, { method: 'put', muteHttpExceptions: true, headers: { 'Content-Range': 'bytes */' + size }, payload: '' });
  var code = res.getResponseCode();
  if (code === 200 || code === 201) return { done: true, id: JSON.parse(res.getContentText()).id };
  if (code === 308) return { next: nextFromRange(res.getHeaders()) };
  return null;
}

function nextFromRange(h) {
  var r = h['Range'] || h['range'];
  var m = r && /bytes=0-(\d+)/.exec(r);
  return m ? Number(m[1]) + 1 : 0;
}

function folderFor(path) {
  var cache = CacheService.getScriptCache();
  var hit = cache.get('f|' + path);
  if (hit) { try { return DriveApp.getFolderById(hit); } catch (e) { cache.remove('f|' + path); } }
  var parts = path.split('/');
  var f = DriveApp.getRootFolder();
  for (var i = 0; i < parts.length; i++) {
    var it = f.getFoldersByName(parts[i]);
    f = it.hasNext() ? it.next() : f.createFolder(parts[i]);
  }
  cache.put('f|' + path, f.getId(), 21600);
  return f;
}

function out(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

/** Run once from the editor (▶ selftest) to grant permissions and check that writing works. */
function selftest() {
  var day = Utilities.formatDate(new Date(), 'Etc/UTC', 'yyyy-MM-dd');
  var line = Utilities.newBlob('{"selftest":"' + new Date().toISOString() + '"}\n').getBytes();
  var f = folderFor(ROOT + '/phone/' + day);
  var it = f.getFilesByName('relay_selftest.jsonl');
  var size = it.hasNext() ? it.next().getSize() : 0;
  Logger.log(JSON.stringify(append(f, 'relay_selftest.jsonl', 'application/json', size, line)));
}
