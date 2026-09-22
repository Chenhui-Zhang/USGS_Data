const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');

const ZOTERO = 'http://127.0.0.1:23119/api';

async function zfetch(pathname) {
  const res = await fetch(`${ZOTERO}${pathname}`, {
    headers: { 'Zotero-API-Version': '3' }
  });
  if (!res.ok) throw new Error(`Zotero ${res.status}: ${await res.text()}`);
  const type = res.headers.get('content-type') || '';
  if (type.includes('application/json')) return res.json();
  return res.text();
}

ipcMain.handle('zotero:ping', async () => {
  try {
    await zfetch('/users/0/collections?limit=1');
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e.message };
  }
});

ipcMain.handle('zotero:collections', async () => {
  return zfetch('/users/0/collections?limit=100');
});

ipcMain.handle('zotero:items', async (_, collectionKey) => {
  const items = await zfetch(`/users/0/collections/${encodeURIComponent(collectionKey)}/items/top?limit=100`);
  return items.filter(x => {
    const t = x?.data?.itemType;
    return t && !['attachment','note','annotation'].includes(t);
  });
});

ipcMain.handle('zotero:paper', async (_, itemKey) => {
  const item = await zfetch(`/users/0/items/${encodeURIComponent(itemKey)}`);
  const children = await zfetch(`/users/0/items/${encodeURIComponent(itemKey)}/children?limit=100`);
  let fulltext = '';
  let attachmentKey = null;
  for (const ch of children) {
    if (ch?.data?.itemType === 'attachment' && ch?.data?.contentType === 'application/pdf') {
      attachmentKey = ch.key;
      try {
        const ft = await zfetch(`/users/0/items/${encodeURIComponent(ch.key)}/fulltext`);
        fulltext = typeof ft === 'string' ? ft : (ft?.content || '');
      } catch (_) {}
      if (fulltext) break;
    }
  }
  return { item, children, fulltext, attachmentKey };
});

ipcMain.handle('zotero:open', async (_, itemKey) => {
  const url = `zotero://select/library/items/${itemKey}`;
  await shell.openExternal(url);
  return true;
});

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1050,
    minHeight: 700,
    title: 'PaperSprout',
    backgroundColor: '#f7f7fb',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  win.loadFile(path.join(__dirname, 'index.html'));
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
